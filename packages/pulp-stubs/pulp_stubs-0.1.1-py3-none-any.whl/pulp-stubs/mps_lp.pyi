from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any, Final, Literal, NotRequired, TypedDict, type_check_only

from pulp.pulp import LpAffineExpression, LpProblem, LpVariable

CORE_FILE_ROW_MODE: Final = "ROWS"
CORE_FILE_COL_MODE: Final = "COLUMNS"
CORE_FILE_RHS_MODE: Final = "RHS"
CORE_FILE_BOUNDS_MODE: Final = "BOUNDS"

CORE_FILE_BOUNDS_MODE_NAME_GIVEN: Final = "BOUNDS_NAME"
CORE_FILE_BOUNDS_MODE_NO_NAME: Final = "BOUNDS_NO_NAME"
CORE_FILE_RHS_MODE_NAME_GIVEN: Final = "RHS_NAME"
CORE_FILE_RHS_MODE_NO_NAME: Final = "RHS_NO_NAME"

ROW_MODE_OBJ: Final = "N"

ROW_EQUIV: dict[Literal["L", "E", "G"], Literal[-1, 0, 1]]
COL_EQUIV: dict[Literal[0, 1], Literal["Continuous", "Integer"]]

@type_check_only
class _MPSParamatersData(TypedDict, extra_items=Any):  # pyright: ignore[reportExplicitAny]
    name: str
    sense: str
    status: str
    sol_status: str

@dataclass
class MPSParameters:
    name: str
    sense: int
    status: int
    sol_status: int
    @classmethod
    def fromDict(cls, data: _MPSParamatersData) -> MPSParameters: ...

@type_check_only
class _MPSCoefficientData(TypedDict, extra_items=Any):  # pyright: ignore[reportExplicitAny]
    name: str
    value: str

@dataclass
class MPSCoefficient:
    name: str
    value: float
    @classmethod
    def fromDict(cls, data: _MPSCoefficientData) -> MPSCoefficient: ...

@type_check_only
class _MPSObjectiveData(TypedDict, extra_items=Any):  # pyright: ignore[reportExplicitAny]
    name: str
    coefficients: Iterable[_MPSCoefficientData]

@dataclass
class MPSObjective:
    name: str | None
    coefficients: list[MPSCoefficient]
    @classmethod
    def fromDict(cls, data: _MPSObjectiveData) -> MPSObjective: ...

@type_check_only
class _MPSVariableData(TypedDict, extra_items=Any):  # pyright: ignore[reportExplicitAny]
    name: str
    cat: str
    lowBound: NotRequired[float | None]
    upBound: NotRequired[float | None]
    varValue: NotRequired[float | None]
    dj: NotRequired[float | None]

@dataclass
class MPSVariable:
    name: str
    cat: str
    lowBound: float | None = 0
    upBound: float | None = None
    varValue: float | None = None
    dj: float | None = None
    @classmethod
    def fromDict(cls, data: _MPSVariableData) -> MPSVariable: ...

@type_check_only
class _MPSConstraintData(TypedDict, extra_items=Any):  # pyright: ignore[reportExplicitAny]
    name: NotRequired[str | None]
    sense: int
    coefficients: Iterable[_MPSCoefficientData]
    pi: NotRequired[float | None]
    constant: NotRequired[float]

@dataclass
class MPSConstraint:
    name: str | None
    sense: int
    coefficients: list[MPSCoefficient]
    pi: float | None = None
    constant: float = 0
    @classmethod
    def fromDict(cls, data: _MPSConstraintData) -> MPSConstraint: ...

@type_check_only
class _MPSData(TypedDict, extra_items=Any):  # pyright: ignore[reportExplicitAny]
    parameters: _MPSParamatersData
    objective: _MPSObjectiveData
    variables: Iterable[_MPSVariableData]
    constraints: Iterable[_MPSConstraintData]
    sos1: Iterable[Any]  # pyright: ignore[reportExplicitAny]
    sos2: Iterable[Any]  # pyright: ignore[reportExplicitAny]

@dataclass
class MPS:
    parameters: MPSParameters
    objective: MPSObjective
    variables: list[MPSVariable]
    constraints: list[MPSConstraint]
    sos1: list[Any]  # pyright: ignore[reportExplicitAny]
    sos2: list[Any]  # pyright: ignore[reportExplicitAny]
    @classmethod
    def fromDict(cls, data: _MPSData) -> MPS: ...

def readMPS(path: str, sense: int, dropConsNames: bool = ...) -> MPS:
    """
    adapted from Julian Märte (https://github.com/pchtsp/pysmps)
    returns a dictionary with the contents of the model.
    This dictionary can be used to generate an LpProblem

    :param path: path of mps file
    :param sense: 1 for minimize, -1 for maximize
    :param dropConsNames: if True, do not store the names of constraints
    :return: a dictionary with all the problem data
    """
    ...

def readMPSSetBounds(
    line: list[str], variable_dict: dict[str, MPSVariable]
) -> None: ...
def readMPSSetRhs(
    line: list[str], constraintsDict: dict[str, MPSConstraint]
) -> None: ...
def writeMPS(
    lp: LpProblem,
    filename: str,
    mpsSense: int = ...,
    rename: bool = ...,
    mip: bool = ...,
    with_objsense: bool = ...,
) -> (
    list[LpVariable]
    | tuple[list[LpVariable], dict[str, str], dict[str, str], str | None]
): ...
def writeMPSColumnLines(
    cv: dict[str, int | float],
    variable: LpVariable,
    mip: bool,
    name: str,
    cobj: LpAffineExpression,
    objName: str,
) -> list[str]: ...
def writeMPSBoundLines(name: str, variable: LpVariable, mip: bool) -> list[str]: ...
def writeLP(
    lp: LpProblem,
    filename: str,
    writeSOS: bool = ...,
    mip: bool = ...,
    max_length: int = ...,
) -> list[LpVariable]: ...
