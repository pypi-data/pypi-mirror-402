import os
from threading import Lock

import numpy as np
import requests
from bokeh.io import curdoc
from bokeh.layouts import column, row
from bokeh.models import ColorBar, ColumnDataSource, Div, HoverTool, LinearColorMapper, Select, Slider
from bokeh.plotting import figure, show
from bokeh.transform import transform
from patme.service.systemutils import log

from delismm import name
from delismm.model.apimodels import SurrogateInfo
from delismm.model.surrogate import Kriging
from delismm.service.exception import DelisMMError

# import logging
# log.logLevel = logging.DEBUG

# check environment variable
if os.environ.get("DELISMMSERVER") is not None:
    server = os.environ["DELISMMSERVER"]
else:
    server = f"https://delismm.nimbus.dlr.de"
actualSurrogate = None
callEndpoint = "/call/"
callReturn = requests.get(f"{server}/list_surrogates")
surrogateNames = list(callReturn.json().values()) if callReturn else []
replotLock = False  # lock if anything should happen, when changing the active parameter
bokehTools = "pan,wheel_zoom,box_zoom,reset,save,undo"
plotPoints = ["6", "11", "21", "51", "101", "201", "501", "1001"]


def resetSurrogate():
    """Get the information of a surrogate model from the server."""
    surrogateName = getSurrogateSelector().value
    response = requests.get(f"{server}/surrogate_info/{surrogateName}")
    surrogateInfo = SurrogateInfo(**response.json())
    global actualSurrogate
    actualSurrogate = Kriging(
        np.zeros((surrogateInfo.number_of_parameters, 1)),
        [0],
        np.array(surrogateInfo.lowerBounds),
        np.array(surrogateInfo.upperBounds),
        parameterNames=surrogateInfo.parameterNames,
        resultNames=surrogateInfo.model_name,
    )


def getActiveSliderValues():
    sliders = getSliders()
    numberOfParameters = actualSurrogate.p
    return [slider.value for slider in sliders[:numberOfParameters]]


def updateSurrogateValues1D(variableParameterName1):
    global actualSurrogate
    log.debug("get 1Dplot data")
    surrogateName = getSurrogateSelector().value
    numberOfPlotPoints = getNumberOfPlotPoints()
    allParameters = np.array([getActiveSliderValues()] * numberOfPlotPoints)
    paramIndex1 = actualSurrogate.parameterNames.index(variableParameterName1)
    x = np.linspace(
        actualSurrogate.lowerBounds[paramIndex1], actualSurrogate.upperBounds[paramIndex1], numberOfPlotPoints
    )
    allParameters[:, paramIndex1] = x
    results = []
    for parameters in allParameters:
        request = (
            f"{server}{callEndpoint}?surrogate_name={surrogateName}&"
            f"parameters={'&parameters='.join([str(p) for p in parameters])}"
        )
        r = requests.get(request)
        results.append(float(r.text))
    source1D.data = dict(x=x, data=np.array(results))
    log.debug("done getting 1Dplot data")


def updateSurrogateValues2D(variableParameterName1, variableParameterName2):
    global actualSurrogate
    log.debug("get 2Dplot data")
    surrogateName = getSurrogateSelector().value
    numberOfPlotPoints = getNumberOfPlotPoints()
    allParameters = np.array([getActiveSliderValues()] * numberOfPlotPoints**2)
    paramIndex1 = actualSurrogate.parameterNames.index(variableParameterName1)
    paramIndex2 = actualSurrogate.parameterNames.index(variableParameterName2)
    x = np.linspace(
        actualSurrogate.lowerBounds[paramIndex1], actualSurrogate.upperBounds[paramIndex1], numberOfPlotPoints
    )
    y = np.linspace(
        actualSurrogate.lowerBounds[paramIndex2], actualSurrogate.upperBounds[paramIndex2], numberOfPlotPoints
    )
    gridx, gridy = np.meshgrid(x, y)
    gridx, gridy = gridx.flatten(), gridy.flatten()
    allParameters[:, paramIndex1] = gridx
    allParameters[:, paramIndex2] = gridy
    results = []
    for parameters in allParameters:
        request = (
            f"{server}{callEndpoint}?surrogate_name={surrogateName}&"
            f"parameters={'&parameters='.join([str(p) for p in parameters])}"
        )
        r = requests.get(request)
        results.append(float(r.text))
    source2D.data = dict(x=gridx, y=gridy, data=np.array(results))
    log.debug("done getting 2Dplot data")
    return x, y


def replot(createNewPlot=False):
    surrogateName = getSurrogateSelector().value
    parameterName1, parameterName2 = [paramWidget.value for paramWidget in getActiveParameters()]
    if createNewPlot:
        plot = figure(width=600, height=500, margin=30, toolbar_location="below", tools=bokehTools)
        curdoc().roots[0].children[1] = plot
    else:
        plot = getPlot()
    if parameterName2 == "none":
        updateSurrogateValues1D(parameterName1)
        if createNewPlot:
            plot.line("x", "data", source=source1D, line_width=3, line_alpha=0.6)
        plot.add_tools(HoverTool(tooltips=[(parameterName1, "@x"), (surrogateName, "@data")]))
        plot.yaxis.axis_label = surrogateName
    else:
        x, y = updateSurrogateValues2D(parameterName1, parameterName2)
        if createNewPlot:
            mapper = LinearColorMapper(
                palette="Viridis256", low=source1D.data["data"].min(), high=source1D.data["data"].max()
            )
            plot.rect(
                "x",
                "y",
                width=x[1] - x[0],
                height=y[1] - y[0],
                source=source2D,
                line_color=None,
                fill_color=transform("data", mapper),
            )
            plot.add_layout(ColorBar(color_mapper=mapper), "right")
        plot.add_tools(HoverTool(tooltips=[(parameterName1, "@x"), (parameterName2, "@y"), (surrogateName, "@data")]))
        plot.yaxis.axis_label = parameterName2

    plot.title.text = surrogateName
    plot.xaxis.axis_label = parameterName1
    log.debug(f"replot done")


def eventSurrogateChanged(attr, old, new):
    log.info(f"eventSurrogateChanged: Selected surrogate: {new}")
    if new not in surrogateNames:
        raise Exception(f"{new} is not in valid surrogate names: {surrogateNames}")
    resetSurrogate()
    numberOfParameters = actualSurrogate.p
    global replotLock
    for slider, paramName, lb, ub in zip(
        getSliders()[:numberOfParameters],
        actualSurrogate.parameterNames,
        actualSurrogate.lowerBounds,
        actualSurrogate.upperBounds,
    ):
        slider.visible = True
        slider.title = paramName
        slider.start = lb
        slider.end = ub
        slider.step = (slider.end - slider.start) / 1000
        slider.value = lb + (slider.end - slider.start) / 2
    for slider in getSliders()[numberOfParameters:]:
        slider.visible = False
    selectActiveParameter1, selectActiveParameter2 = getActiveParameters()
    selectActiveParameter1.options = actualSurrogate.parameterNames
    selectActiveParameter2.options = ["none"] + actualSurrogate.parameterNames
    replotLock = True
    setActiveParameter1(actualSurrogate.parameterNames[0])
    setActiveParameter2("none")
    replotLock = False
    replot(True)


def onchangeNumberOfSamples(attr, old, new):
    log.info(f"onchangeNumberOfSamples: {attr} changed from {old} to {new}")
    replot()


def onchangeActiveParameter1(attr, old, new):
    log.debug(f"onchangeActiveParameter1: {attr} changed from {old} to {new}. Lock is active: {replotLock}")
    if replotLock:
        return  # if lock is active, do nothing
    replot()


def onchangeActiveParameter2(attr, old, new):
    log.debug(f"onchangeActiveParameter2: {attr} changed from {old} to {new}. Lock is active: {replotLock}")
    if replotLock:
        return  # if lock is active, do nothing
    createNewPlot = False
    if old == "none":
        log.debug(f"switch plot from 1D to 2D")
        createNewPlot = True
    if new == "none":
        log.debug(f"switch plot from 2D to 1D")
        createNewPlot = True
    replot(createNewPlot=createNewPlot)


def onchangeSlider(attr, old, new):
    log.info(f"onchangeSlider: {attr} changed from {old} to {new}")
    replot()


def createWidgets():
    selectSurrogateName = Select(title="Select surrogate", options=surrogateNames, width=300)
    selectSurrogateName.on_change("value", eventSurrogateChanged)

    selectNumberOfSamples = Select(title="Number of Samples", options=plotPoints, value="6", width=300)
    selectNumberOfSamples.on_change("value", onchangeNumberOfSamples)

    selectActiveParameter = Select(options=[], width=300)
    selectActiveParameter.on_change("value", onchangeActiveParameter1)
    selectActiveParameter2 = Select(value="none", options=[], width=300)
    selectActiveParameter2.on_change("value", onchangeActiveParameter2)

    p = figure(width=600, height=500, margin=30, toolbar_location="below", tools=bokehTools)

    sliders = []
    for i in range(10):
        slider = Slider(start=0.1, end=10, value=1, step=0.1, title=f"Parameter {i}")
        slider.on_change("value_throttled", onchangeSlider)
        sliders.append(slider)

    layout = row(
        column(selectSurrogateName, selectNumberOfSamples),
        p,
        column(
            [
                Div(text="<b>Plot Parameters</b>"),
                selectActiveParameter,
                selectActiveParameter2,
                Div(text="\n<b>Nominal parameter values:</b>"),
            ]
            + sliders
        ),
    )
    return layout


def getSurrogateSelector():
    return curdoc().roots[0].children[0].children[0]


def getPlot():
    return curdoc().roots[0].children[1]


def getSliders():
    return curdoc().roots[0].children[2].children[4:]


def setNumberOfPlotPoints(value):
    if str(value) not in plotPoints:
        raise DelisMMError("Invalid number of plot points")
    curdoc().roots[0].children[0].children[1].value = value


def getNumberOfPlotPoints():
    return int(curdoc().roots[0].children[0].children[1].value)


def getActiveParameters():
    return curdoc().roots[0].children[2].children[1], curdoc().roots[0].children[2].children[2]


def setActiveParameter1(param):
    curdoc().roots[0].children[2].children[1].value = param


def setActiveParameter2(param):
    curdoc().roots[0].children[2].children[2].value = param


def setActiveParameters(param1, param2):
    global replotLock
    replotLock = True
    curdoc().roots[0].children[2].children[1].value = param1
    replotLock = False
    curdoc().roots[0].children[2].children[2].value = param2


source1D = ColumnDataSource(data=dict(x=[0, 1], y=[0, 2]))
source2D = ColumnDataSource()
layout = createWidgets()
curdoc().add_root(layout)
curdoc().title = name + " plotter"
dummyPlot = getPlot()
dummyPlot.line("x", "data", source=source1D, line_width=3, line_alpha=0.6)

if 1 and surrogateNames:
    getSurrogateSelector().value = "lh2_tank_totalMass[kg]_v_1.1"
    getSliders()[0].value = 1716 * 2
    getSliders()[1].value = 0.66
    getSliders()[2].value = 0.2
    # setActiveParameters("dcyl[mm]", "lcylByR-")

if __name__ == "__main__":
    show(curdoc().roots[0])
