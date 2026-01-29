from typing import Literal, TypedDict, type_check_only

@type_check_only
class _LpCategories(TypedDict):
    LpContinuous: Literal["Continuous"]
    LpInteger: Literal["Integer"]
    LpBinary: Literal["Binary"]

VERSION: Literal["3.3.0"]
EPS: float

# variable categories
LpContinuous: Literal["Continuous"]
LpInteger: Literal["Integer"]
LpBinary: Literal["Binary"]
LpCategories: _LpCategories

# objective sense
LpMinimize: Literal[1]
LpMaximize: Literal[-1]
LpSenses: dict[Literal[-1, 1], Literal["Maximize", "Minimize"]]
LpSensesMPS: dict[Literal[-1, 1], Literal["MAX", "MIN"]]

# problem status
LpStatusNotSolved: Literal[0]
LpStatusOptimal: Literal[1]
LpStatusInfeasible: Literal[-1]
LpStatusUnbounded: Literal[-2]
LpStatusUndefined: Literal[-3]
LpStatus: dict[
    Literal[-3, -2, -1, 0, 1],
    Literal["Not Solved", "Optimal", "Infeasible", "Unbounded", "Undefined"],
]

# solution status
LpSolutionNoSolutionFound: Literal[0]
LpSolutionOptimal: Literal[1]
LpSolutionIntegerFeasible: Literal[2]
LpSolutionInfeasible: Literal[-1]
LpSolutionUnbounded: Literal[-2]
LpSolution: dict[
    Literal[-2, -1, 0, 1, 2],
    Literal[
        "No Solution Found",
        "Optimal Solution Found",
        "Solution Found",
        "No Solution Exists",
        "Solution is Unbounded",
    ],
]
LpStatusToSolution: dict[
    Literal[-3, -2, -1, 0, 1],
    Literal[-2, -1, 1],
]

# constraint sense
LpConstraintLE: Literal[-1]
LpConstraintEQ: Literal[0]
LpConstraintGE: Literal[1]
LpConstraintTypeToMps: dict[Literal[-1, 0, 1], Literal["L", "E", "G"]]
LpConstraintSenses: dict[Literal[-1, 0, 1], Literal["<=", "=", ">="]]
LpCplexLPLineSize: Literal[78]

class PulpError(Exception):
    """
    Pulp Exception Class
    """

    ...
