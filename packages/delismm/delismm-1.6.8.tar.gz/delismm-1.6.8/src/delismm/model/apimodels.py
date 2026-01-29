from pydantic import BaseModel, PositiveInt


class SurrogateInfo(BaseModel):
    kriging_type: str
    model_name: str
    number_of_samples: int
    number_of_parameters: int
    condition: float
    correlation_function: str
    regression_function: str
    regularizationParameter: float
    optThetaGlobalLocalType: str
    optThetaGlobalAttempts: int
    optThetaMaxIter: int
    optThetaPrintout: bool
    correlationMatrixAlgo: str
    log10SampleX: list[bool]
    log10SampleY: bool
    parameterNames: list[str]
    lowerBounds: list[float]
    upperBounds: list[float]
    theta: list[float]
