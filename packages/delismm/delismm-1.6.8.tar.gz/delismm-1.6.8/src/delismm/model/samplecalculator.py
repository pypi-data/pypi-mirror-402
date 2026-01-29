"""
Created on 24.01.2017

@author: freu_se
"""

import copy
import getpass
import logging
import os
import pickle
import time
import traceback
from configparser import ConfigParser
from multiprocessing import Pool, Process, Queue, Value, cpu_count, current_process

import numpy as np
import pandas as pd
from patme.service.decorators import memoize
from patme.service.logger import log, resetLoggerToNewRunDir
from patme.service.systemutils import getTimeString
from patme.sshtools.cara import numberOfClusterJobsAvailable

from delismm.service.exception import DelisMMError
from delismm.service.utilities import extractTrailingNumber


@memoize
def getY(sampleX, targetFunctionInstance, verbose=True, runDir=None, resumeSamples=False, staggerStart=0):
    """Method that returns function values at the sample points.

    It is the main entry point to calculate samples. There are several variants for calculation.

    1. calculate serial
    #. calculate parallel. For this, targetFunctionInstance must have the attribute doParallelization=[clusterqueue, local] or one of them.
    #. calculate remote. Performed if, targetFunctionInstance.doRemoteCall==True must have the attribute doRemoteCall=True

    :param sampleX: p,n array with samples not normalized
    :param targetFunctionInstance: instance of a delismm.model.customsystemfunction class
        or a sub class of it.
    :param verbose: Flag if the calculation should be output to the commandline
    :param runDir: directory of the run. If present, for serial runs, the results are written after each sample
    :param resumeSamples: Flag if sampleY in runDir should be resumed. In this case, sampleY.pickle is read and the rest of the calculation resumed.
        Only works for serial or local parallel runs with given runDir.
        If None, a new run is started
    :param staggerStart: seconds to wait between each start of a parallel process, if running parallel
    :return: function values at the sample points
    """
    if sampleX is None:
        log.warning("SampleX not given in getYStatic. Returning")
        return None
    sampleX = np.array(sampleX)

    # parallelization state
    doRemoteCall = hasattr(targetFunctionInstance, "doRemoteCall") and targetFunctionInstance.doRemoteCall
    clusterQueueParallelization, localParalellization, asyncParallelization = False, False, False
    if hasattr(targetFunctionInstance, "doParallelization"):
        clusterQueueParallelization = "clusterqueue" in targetFunctionInstance.doParallelization
        localParalellization = "local" in targetFunctionInstance.doParallelization
        asyncParallelization = "async" in targetFunctionInstance.doParallelization

    # remote runs
    try:
        if clusterQueueParallelization and doRemoteCall:
            return getYParallel(sampleX, targetFunctionInstance, verbose)
        if doRemoteCall:
            return remoteCaller(sampleX, targetFunctionInstance, verbose)

    # local runs
    except Exception as e:
        log.error(
            "Received an error while performing the function call remotely. Trying local run instead. Original error:\n"
            + str(e)
        )

        return _getYLocalTemporary(sampleX, targetFunctionInstance, verbose)
    if localParalellization:
        return getYParallel(
            sampleX, targetFunctionInstance, verbose, resumeSamples=resumeSamples, staggerStart=staggerStart
        )
    elif asyncParallelization:
        return getYParallelAsync(sampleX, targetFunctionInstance, verbose)
    return getYSerial(sampleX, targetFunctionInstance, verbose, runDir, resumeSamples=resumeSamples)


def getYSerial(sampleX, targetFunctionInstance, verbose=True, runDir=None, resumeSamples=False):
    """Runs the target function in serial

    For a parameter documentation, refer to getY()"""
    from delismm.model.doe import AbstractDOE, DOEfromFile

    if resumeSamples:
        sampleYFile = os.path.join(runDir, "sampleY.pickle")
        sampleY = AbstractDOE.ysFromFile(sampleYFile, targetFunctionInstance)
        sampleX = sampleX[:, len(sampleY) :]
        log.info("Resuming samples. Already calculated: " + str(len(sampleY)))
    else:
        sampleY = []
    numberOfSamples = sampleX.shape[1]
    if verbose:
        log.info("Calculating samples.")
    if runDir:
        sampleXFilename = os.path.join(runDir, "sampleX_bounds.txt")
        if not os.path.exists(sampleXFilename):
            AbstractDOE.xToFileStatic(sampleXFilename, sampleX)
    for sampleNumber in range(numberOfSamples):
        sampleY.append(targetFunctionInstance(sampleX[:, sampleNumber]))
        if verbose and divmod(sampleNumber + 1, 10)[1] == 0:
            log.info("Calculated " + str(sampleNumber + 1) + " samples.")
        if runDir:
            AbstractDOE.yToFile(os.path.join(runDir, "sampleY.txt"), targetFunctionInstance, sampleY)
    return sampleY


def _getYLocalTemporary(sampleX, targetFunctionInstance, verbose):
    """calculates the samples locally if a remote call failed. The parameters are adpated only temporary"""
    targetFunctionInstance.doRemoteCall = False
    clusterqueue = (
        True
        if hasattr(targetFunctionInstance, "doParallelization")
        and "clusterqueue" in targetFunctionInstance.doParallelization
        else False
    )
    if clusterqueue:
        targetFunctionInstance.doParallelization.remove("clusterqueue")

    sampleY = getY(sampleX, targetFunctionInstance, verbose)

    if clusterqueue:
        targetFunctionInstance.doParallelization.append("clusterqueue")
    targetFunctionInstance.doRemoteCall = True

    return sampleY


def getYParallel(sampleX, targetFunctionInstance, verbose=True, resumeSamples=False, staggerStart=0):
    """Runs the target function in parallel.

    It determines the number of processes either by the number of cores or by the
    number of cluster jobs. Then for each parallel process, a copy of the targetfunction
    running in a subdirectory is created. Lastly, the samples are split for each process.
    After the parallel run, the results are put together and returned.
    """
    numberOfProcesses = _getNumberOfProcesses(sampleX.shape[1], targetFunctionInstance)
    targetFunctionCopies = _getTargetFunctionCopies(targetFunctionInstance, numberOfProcesses, resumeSamples)
    processInputs = _getParallelRunInputSamples(
        sampleX, targetFunctionCopies, numberOfProcesses, verbose, resumeSamples, staggerStart
    )

    # run parallel
    log.info("Start parallel run with " + str(numberOfProcesses) + " processes")
    with Pool(processes=numberOfProcesses) as pool:
        sampleYmultiprocesses = pool.map(calledParallelExecution, processInputs)

    # put results together
    sampleY = []
    for sampleYmultiprocess in sampleYmultiprocesses:
        sampleY.extend(sampleYmultiprocess)
    log.info("parallel run done")

    return sampleY


manualMinParallelProcesses = None


def _getNumberOfProcesses(sampleLength, targetFunctionInstance):
    """Calculates the number of processes that might be run. Processes for the cluster
    are dependent on the number of available cluster jobs. Local parallelization depends
    on the number of cores"""
    if "clusterqueue" in targetFunctionInstance.doParallelization:
        numberOfProcesses = numberOfClusterJobsAvailable() - 1
        numberOfProcesses = np.max([numberOfProcesses, 2])
        numberOfProcesses = np.min(
            [numberOfProcesses, 8]
        )  # use a maximum of 8 cluster processes. Otherwise protocol banner error might occur
    else:
        numberOfProcesses = int(np.ceil(cpu_count() * 2 / 3))
    return int(
        np.min([sampleLength, numberOfProcesses, manualMinParallelProcesses if manualMinParallelProcesses else np.inf])
    )


def _getTargetFunctionCopies(targetFunctionInstance, numberOfProcesses, resumeSamples=False):
    """creates copies of the given target function. It removes the parallelization mode, that is
    used (clusterqueue or local). For each new function a subdirectory is created for a run
    independently to the other target functions."""
    targetFunctionCopies = []
    parallelDirName = "parallel_"
    runDir = targetFunctionInstance.runDir if hasattr(targetFunctionInstance, "runDir") else None
    foldersFound = []
    if runDir is not None and resumeSamples:
        # look for folders like with parallelDirName
        for dirName in os.listdir(runDir):
            dirPath = os.path.join(runDir, dirName)
            if os.path.isdir(dirPath) and parallelDirName in dirName:
                foldersFound.append(dirPath)
        if not len(foldersFound) == numberOfProcesses:
            raise DelisMMError(
                "Number of parallel folders found in runDir does not match number of processes. Found: "
                + f"{len(foldersFound)}, Expected: {numberOfProcesses}"
            )
    # sort folders by process number
    foldersFound.sort(key=extractTrailingNumber)

    for processNumber in range(numberOfProcesses):
        targetFunctionCopy = copy.deepcopy(targetFunctionInstance)
        if "clusterqueue" in targetFunctionCopy.doParallelization:
            targetFunctionCopy.doParallelization.remove("clusterqueue")
        elif "local" in targetFunctionCopy.doParallelization:
            targetFunctionCopy.doParallelization.remove("local")
        else:
            targetFunctionCopy.doParallelization.remove("async")
        # reset rundir
        if resumeSamples:
            targetFunctionCopy.runDir = foldersFound[processNumber]
        elif targetFunctionCopy.runDir is not None:
            zerosToAdd = "0" * (len(str(numberOfProcesses)) - len(str(processNumber)))
            targetFunctionCopy.runDir = (
                os.path.abspath(os.path.join(runDir, parallelDirName + getTimeString()))
                + "_"
                + zerosToAdd
                + str(processNumber)
            )
            if not os.path.exists(targetFunctionCopy.runDir):
                os.makedirs(targetFunctionCopy.runDir)
        targetFunctionCopies.append(targetFunctionCopy)
    return targetFunctionCopies


def _getParallelRunInputSamples(
    sampleX, targetFunctionCopies, numberOfProcesses, verbose, resumeSamples=False, staggerStart=0
):
    """Create a list of 3-tuples. Each list entry has the input for each parallel process to be run.
    A tuple consists of (sub-sampleX, targetFunctionCopy, verbose)

    Each tuple will be used for the method "calledParallelExecution"
    """
    # split samples
    splitSampleLength = int(np.ceil(sampleX.shape[1] / numberOfProcesses))
    splitSamples = [
        sampleX[:, splitSampleLength * count : splitSampleLength * (count + 1)]
        for count in range(numberOfProcesses)
        if splitSampleLength * count < sampleX.shape[1]
    ]

    # setup input list
    return list(
        zip(
            splitSamples,
            targetFunctionCopies,
            range(numberOfProcesses),
            [verbose] * numberOfProcesses,
            [resumeSamples] * numberOfProcesses,
            [staggerStart * i for i in range(numberOfProcesses)],
        )
    )


def getYParallelAsync(sampleX, targetFunctionInstance, verbose=True):
    """This function performs a parallel execution of the target function.
    The targetfunction must have these attributes set:

    - asyncWaitTime
    - asyncMaxProcesses
    - getNumberOfNewJobs()

    Please refer to customsystemfunction for a description of those.

    The run is performed asynchronously, so that it respects if a new job can
    be run (by a call to getNumberOfNewJobs()) e.g. due to license restrictions.
    A task creation process is generated which submits a job if getNumberOfNewJobs() > 0.
    These jobs of single samples are taken by the worker processes, that perform the
    calculation and return the result and sample index(since it must be put in the correct
    order afterwards).
    """
    if targetFunctionInstance.asyncMaxProcesses is None:
        raise DelisMMError("Maximum number of processes must be set.")
    numberOfSamples = sampleX.shape[1]
    numberOfWorkerProcesses = np.min([targetFunctionInstance.asyncMaxProcesses, numberOfSamples])

    # Create queues
    taskQueue = Queue()
    resultQueue = Queue()
    numberOfRunningJobs = Value("I", lock=True)

    # Submit tasks in a task process that only puts new jobs in the taskQueue, if it is possible

    runDir = targetFunctionInstance.runDir if hasattr(targetFunctionInstance, "runDir") else None
    processInputs = _getParallelRunInputSamples(
        sampleX, [targetFunctionInstance] * numberOfSamples, numberOfSamples, verbose
    )
    process = Process(
        target=taskCreatorAsync,
        args=(taskQueue, resultQueue, processInputs, runDir, numberOfWorkerProcesses, numberOfRunningJobs),
    )
    process.start()
    process.join()

    # Start worker processes
    targetFunctionCopies = _getTargetFunctionCopies(targetFunctionInstance, numberOfWorkerProcesses)
    for targetFunctionCopy in targetFunctionCopies:
        process = Process(target=workerAsync, args=(taskQueue, resultQueue, targetFunctionCopy, numberOfRunningJobs))
        process.start()
        process.join()

    resultArray = []
    # wait for results and get results
    for _ in range(numberOfSamples):
        resultArray.append(resultQueue.get())
    # sort results
    resultDf = pd.DataFrame(resultArray, columns=["results", "indexes"])
    resultDf.sort_values(by="indexes", inplace=True)

    log.info("parallel run done")

    return resultDf["results"].tolist()


def taskCreatorAsync(taskQueue, resultQueue, processInputs, runDirBase, numberOfWorkerProcesses, numberOfRunningJobs):
    """Function run by the asynchronous task generator processes

    :param runDir: directory where the base process is working - a new folder for own logging files is created
    """

    def stopWorkerProcesses(onError=False):
        log.debug("stop worker processes")
        for _ in range(numberOfWorkerProcesses):
            taskQueue.put("STOP")
        if onError:
            for sampleIndex in range(len(processInputs)):
                # puts None in the result Queue, indicating an error
                resultQueue.put([None, sampleIndex])

    def getMaxNewJobs(runDir, verboseOutput=False):
        logLevel = log.INFO if verboseOutput else log.DEBUG
        maxjobs, minjobs, unusedLicense = readAsyncTaskGenConfig(runDir)
        newJobsByLicense = targetFunctionInstance.getNumberOfNewJobs()
        maxNewJobs = _evaluateMaxNewJobArgs(
            maxjobs, minjobs, unusedLicense, numberOfRunningJobs.value, newJobsByLicense
        )
        log.log(
            logLevel,
            "MaxNewJobs: {}. All job determining parameters are: {}".format(
                maxNewJobs,
                list(
                    zip(
                        ["newJobsByLicense", "maxjobs", "minjobs", "unusedLicense", "numberOfRunningJobs", "waitTime"],
                        [
                            newJobsByLicense,
                            maxjobs,
                            minjobs,
                            unusedLicense,
                            numberOfRunningJobs.value,
                            targetFunctionInstance.asyncWaitTime,
                        ],
                    )
                ),
            ),
        )
        return maxNewJobs

    try:
        runDir = None
        if runDirBase is not None:
            runDir = os.path.abspath(os.path.join(runDirBase, "parallel_{}_taskGen".format(getTimeString())))
            _resetLogger(runDir)
            writeAsyncTaskGenConfig(runDir)

        for sampleX, targetFunctionInstance, sampleIndex, verbose, _, _ in processInputs:
            newJobCount = getMaxNewJobs(runDir, verboseOutput=False)
            log.info(
                "Try send and start sample #{}. Actual max number of new jobs: {}".format(sampleIndex, newJobCount)
            )
            iterationIndex = 0
            while newJobCount == 0:
                verbose = iterationIndex % 12 == 0
                if verbose:
                    log.info(
                        "Waiting for next possible calculation. Actual max number of new jobs: {}".format(newJobCount)
                    )
                time.sleep(5)
                newJobCount = getMaxNewJobs(runDir, verboseOutput=verbose)
                iterationIndex += 1
            log.debug("put sample in queue. sample: \n" + str(sampleX))

            #             if sampleIndex != 257:continue

            taskQueue.put([sampleX, sampleIndex, verbose])
            # wait for a certain time specified by the target function (e.g. to start the previous process)
            time.sleep(targetFunctionInstance.asyncWaitTime)
        log.info("All tasks submitted")
    except Exception as e:
        stopWorkerProcesses(True)
        log.error("Got an exception: " + str(e))
        raise

    stopWorkerProcesses()


def workerAsync(taskQueue, resultQueue, targetFunctionCopy, numberOfRunningJobs):
    """Function run by the asynchronous worker processes"""
    firstIteration = True
    for sampleX, sampleIndex, verbose in iter(taskQueue.get, "STOP"):
        with numberOfRunningJobs.get_lock():
            numberOfRunningJobs.value += 1
        if firstIteration:
            _resetLogger(targetFunctionCopy.runDir)
            firstIteration = False
        log.info(f"calculate sample #{sampleIndex} in {current_process().name} and these samples: {sampleX}")
        try:
            result = _callGetYInNewProcess(sampleX, targetFunctionCopy, sampleIndex, verbose)
            resultQueue.put([result[0], sampleIndex])
        except:
            resultQueue.put([None, sampleIndex])
        with numberOfRunningJobs.get_lock():
            numberOfRunningJobs.value -= 1
    log.info('Subprocess done with "{}" and processId {}'.format(str(current_process().name), str(os.getpid())))


def calledParallelExecution(args):
    """method that is called from the synchronous parallel process. Resets the logger and calls getY"""
    log.info("in calledParallelExecution")
    sampleX, targetFunctionInstance, sampleSetIndex, verbose, resumeSamples, waitBeforeStart = args
    # sleep for process_number * staggerStart s to stagger API call (needed for muwind)
    time.sleep(waitBeforeStart)
    _resetLogger(targetFunctionInstance.runDir)
    sampleY = _callGetYInNewProcess(sampleX, targetFunctionInstance, sampleSetIndex, verbose, resumeSamples)
    log.info('Subprocess done with "{}" and processId {}'.format(str(current_process().name), str(os.getpid())))
    return sampleY


def _callGetYInNewProcess(sampleX, targetFunctionInstance, sampleSetIndex, verbose, resumeSamples=False):
    """doc"""
    log.info('Call getY in "%s" with processId %s' % (str(current_process().name), str(os.getpid())))
    log.debug("calculate sample set #{} and these samples: {}".format(sampleSetIndex, str(sampleX)))
    try:
        sampleY = getY(
            sampleX, targetFunctionInstance, verbose, runDir=targetFunctionInstance.runDir, resumeSamples=resumeSamples
        )
    except Exception as e:
        log.error(
            "\n".join(
                [
                    "Exception raised in " + str(current_process().name) + " with this message:",
                    str(e),
                    traceback.format_exc(),
                ]
            )
        )
        logging.shutdown()
        raise
    return sampleY


def _resetLogger(runDir):
    """resets the logger when a new process is started to prevent the processes to log in to the same file"""
    try:
        os.makedirs(runDir, exist_ok=True)
        resetLoggerToNewRunDir(runDir)
    except:
        # if delis is not on the search path, the logger will not be reset, since there is no file handler in the logger
        pass


taskGeneratorConfigName = "taskGenerator.config"
configSection = "AsyncTaskGeneratorOptions"


def writeAsyncTaskGenConfig(runDir, maxjobs=1000000, minjobs=1, unusedLicenses=1):
    """writes a config file defining configuration options for the asynchronous task generator"""
    configString = _getAsyncTaskGenConfig(maxjobs, minjobs, unusedLicenses)

    with open(os.path.join(runDir, taskGeneratorConfigName), "w") as f:
        f.write(configString)


def _getAsyncTaskGenConfig(maxjobs=1000000, minjobs=1, unusedLicenses=1):
    """writes a config file defining configuration options for the asynchronous task generator"""

    separator = "###################################################"
    configString = """{}
# configuration options for the asynchronous task generator
# hierarchy in case of conflicting values: 1. minJobs, 2.unusedLicenses, 3. maxJobs
{}
[{}]

# maximum number of jobs that may run in parallel
maxJobs = {}

# minimum number of jobs that may run in parallel. The jobs will be sent, without regard of actual license availability
minJobs = {}

# number of licenses that will be kept available to others and will be by this task
unusedLicenses = {}
""".format(
        separator, separator, configSection, maxjobs, minjobs, unusedLicenses
    )
    return configString


def readAsyncTaskGenConfig(runDir):
    """reads the config file from runDir

    :return: tuple: (maxjobs, minjobs, unusedLicense)
    """
    if runDir is None or not os.path.exists(os.path.join(runDir, taskGeneratorConfigName)):
        return 1000000, 0, 0
    with open(os.path.join(runDir, taskGeneratorConfigName)) as f:
        configString = f.read()
    return _readAsyncTaskGenConfig(configString)


def _readAsyncTaskGenConfig(configString):
    """reads the given config string.

    :param configString: string e.g. as generated by _getAsyncTaskGenConfig()

    :return: tuple: (maxjobs, minjobs, unusedLicense)
    """
    parser = ConfigParser(allow_no_value=False)
    parser.read_string(configString)
    configItems = ["maxJobs", "minJobs", "unusedLicenses"]
    configResults = [int(parser[configSection][configItem]) for configItem in configItems]
    return configResults


def _evaluateMaxNewJobArgs(maxjobs, minjobs, unusedLicense, numberOfRunningJobs, newJobsByLicense):
    """doc"""
    maxNewJobs = min(maxjobs - numberOfRunningJobs, newJobsByLicense - unusedLicense)
    maxNewJobs = max(minjobs - numberOfRunningJobs, maxNewJobs, 0)
    return maxNewJobs


def readMaxJobsFile(runDir, verbose=False):
    """reads the file 'maxjobs.txt' if it exists. The file should contain an integer
    defining the maximum number of actual licenses to be used.
    The runDir is usually the task generator process dir: '*_taskGen'"""
    if runDir is None or not os.path.exists(os.path.join(runDir, "maxjobs.txt")):
        return 100000000
    with open(os.path.join(runDir, "maxjobs.txt")) as f:
        line = f.readline()
        try:
            maxJobs = int(line)
            if verbose:
                log.info("Found a max jobs file. Read maxjobs: {}".format(maxJobs))
            return maxJobs
        except:
            log.warning("Found a max jobs file, but could not read the content")
            return 100000000


_getYRemoteInputFileName = "getYInput.pickle"
_getYRemoteResultFileName = "getYResult.pickle"


def remoteCaller(sampleX, targetFunctionInstance, verbose=True):
    """This method handles calling the targetfunction remotely on the institute cluster"""

    # serializing sampleX and targetFunction and put them to a file in targetFucntionInstance.runDir
    tfAndSamplesFile = os.path.join(targetFunctionInstance.runDir, _getYRemoteInputFileName)
    sampleYFile = os.path.join(targetFunctionInstance.runDir, _getYRemoteResultFileName)
    if os.path.exists(tfAndSamplesFile):
        os.remove(tfAndSamplesFile)
    if os.path.exists(sampleYFile):
        os.remove(sampleYFile)

    runDirBak = targetFunctionInstance.runDir  # remotely, the current dir will be targetFunctionInstance.runDir
    targetFunctionInstance.runDir = "."
    with open(tfAndSamplesFile, "wb") as f:
        pickle.dump([sampleX, targetFunctionInstance, verbose], f)
    targetFunctionInstance.runDir = runDirBak

    # call remote
    _callRemote(targetFunctionInstance)

    # read sampleY
    if not os.path.exists(sampleYFile):
        raise FileNotFoundError(
            "The expected sample result does not exist. Possibly, the cluster call failed. Please have a look at the cluster log in this directory: "
            + targetFunctionInstance.runDir
        )
    with open(sampleYFile, "rb") as f:
        sampleY = pickle.load(f)

    if len(sampleY) != sampleX.shape[1]:
        raise DelisMMError("lengths of sampleX and sampleY do not match!")
    return sampleY


def _callRemote(targetFunctionInstance):
    """sends the remote call to the cluster"""
    from patme.sshtools.clustercaller import PythonModuleCaller

    jobName = targetFunctionInstance.name.replace(" ", "_")
    jobCommands = []
    jobCommands += ["/home/%s/delismm/src/delismm/model/samplecalculator.py" % getpass.getuser()]
    caller = PythonModuleCaller(targetFunctionInstance.runDir, jobCommands)
    caller.runRemote(jobName=jobName)


def remoteReader():
    """method called remote (on the cluster) to read the samples and target function, calculate sampleY and write sampleY."""
    try:
        log.info("On remote machine: calculate samples remote")

        log.debug("Read target function and samples")
        runDir = "."  # on the cluster, the process is started in the directory with the input samples
        tfAndSamplesFile = os.path.join(runDir, _getYRemoteInputFileName)
        sampleYFile = os.path.join(runDir, _getYRemoteResultFileName)

        with open(tfAndSamplesFile, "rb") as f:
            sampleX, targetFunctionInstance, verbose = pickle.load(f)

        log.debug("Call getY")
        targetFunctionInstance.doRemoteCall = False
        sampleY = getY(sampleX, targetFunctionInstance, verbose)

        log.debug("Write sampleY")
        with open(sampleYFile, "wb") as f:
            pickle.dump(sampleY, f)

    except Exception as e:
        log.error("\n".join(["Got this error on the remote machine:", str(e), traceback.format_exc()]))
        raise
