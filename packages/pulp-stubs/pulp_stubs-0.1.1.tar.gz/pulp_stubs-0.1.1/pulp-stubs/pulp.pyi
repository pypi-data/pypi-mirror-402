from _collections_abc import dict_items, dict_keys, dict_values
from collections.abc import Collection, Iterable, Iterator
from logging import Logger
from re import Pattern
from typing import Any, Final, Literal, LiteralString, Self, override

from pulp.apis import LpSolver

from . import mps_lp as mpslp

log: Logger

type _Addable = (
    int
    | float
    | None
    | LpElement
    | LpAffineExpression
    | LpConstraint
    | dict[Any, _Addable]  # pyright: ignore[reportExplicitAny]
    | Iterable[_Addable]
)

type _Multiplicable = int | float | LpAffineExpression | LpConstraint | LpVariable

type _AddableToProblem = (
    int | float | LpConstraint | LpConstraintVar | LpAffineExpression | LpVariable
)

class LpElement:
    """Base class for LpVariable and LpConstraintVar"""

    illegal_chars: Final = "-+[] ->/"
    expression: Pattern[str]
    trans: dict[int, int]
    def setName(self, name: str | None) -> None: ...
    def getName(self) -> str | None: ...

    name: property
    def __init__(self, name: str | None) -> None: ...
    @override
    def __hash__(self) -> int: ...
    @override
    def __str__(self) -> str: ...
    @override
    def __repr__(self) -> str | None: ...
    def __neg__(self) -> LpAffineExpression: ...
    def __pos__(self) -> Self: ...
    def __bool__(self) -> bool: ...
    def __add__(self, other: _Addable) -> LpAffineExpression: ...
    def __radd__(self, other: _Addable) -> LpAffineExpression: ...
    def __sub__(self, other: _Addable) -> LpAffineExpression: ...
    def __rsub__(self, other: _Addable) -> LpAffineExpression: ...
    def __mul__(self, other: _Multiplicable) -> LpAffineExpression: ...
    def __rmul__(self, other: _Multiplicable) -> LpAffineExpression: ...
    def __truediv__(self, other: _Multiplicable) -> LpAffineExpression: ...
    def __le__(self, other: _Addable) -> LpConstraint: ...
    def __ge__(self, other: _Addable) -> LpConstraint: ...
    @override
    def __eq__(self, other: _Addable) -> LpConstraint: ...
    @override
    def __ne__(self, other: object) -> bool: ...

class LpVariable(LpElement):
    """
    This class models an LP Variable with the specified associated parameters

    :param name: The name of the variable used in the output .lp file
    :param lowBound: The lower bound on this variable's range.
        Default is negative infinity
    :param upBound: The upper bound on this variable's range.
        Default is positive infinity
    :param cat: The category this variable is in, Integer, Binary or
        Continuous(default)
    :param e: Used for column based modelling: relates to the variable's
        existence in the objective function and constraints
    """

    varValue: float | None
    dj: float | None
    lowBound: float | None
    upBound: float | None
    cat: str
    _lowbound_original: float | None
    _upbound_original: float | None
    def __init__(
        self,
        name: str,
        lowBound: float | None = ...,
        upBound: float | None = ...,
        cat: str = ...,
        e: dict[LpConstraintVar, float | int] | None = ...,
    ) -> None: ...
    def toDataclass(self) -> mpslp.MPSVariable:
        """
        Exports a variable into a dataclass with its relevant information

        :return: a :py:class:`mpslp.MPSVariable` with the variable information
        :rtype: :mpslp.MPSVariable
        """
        ...

    @classmethod
    def fromDataclass(cls, mps: mpslp.MPSVariable) -> LpVariable:
        """
        Initializes a variable object from information that comes from a dataclass

        :param mps: a :py:class:`mpslp.MPSVariable` with the variable information
        :return: a :py:class:`LpVariable`
        :rtype: :LpVariable
        """
        ...

    def toDict(self) -> dict[str, Any]:
        """
        Exports a variable into a dict with its relevant information.

        :return: a :py:class:`dict` with the variable information
        :rtype: :dict
        """
        ...

    def to_dict(self) -> dict[str, Any]:
        """
        Exports a variable into a dict with its relevant information.

        This method is deprecated and :py:class:`LpVariable.toDict` should be used instead.

        :return: a :py:class:`dict` with the variable information
        :rtype: :dict
        """
        ...

    @classmethod
    def fromDict(cls, data: dict[str, Any]) -> LpVariable:
        """
        Initializes a variable object from information that comes from a dict.

        :param data: a dict with the variable information
        :return: a :py:class:`LpVariable`
        :rtype: :LpVariable
        """
        ...

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> LpVariable:
        """
        Initializes a variable object from information that comes from a dict.

        This method is deprecated and :py:class:`LpVariable.fromDict` should be used instead.

        :param data: a dict with the variable information
        :return: a :py:class:`LpVariable`
        :rtype: :LpVariable
        """
        ...

    def add_expression(self, e: dict[LpConstraintVar, float | int]): ...
    @classmethod
    def matrix(
        cls, name, indices=..., lowBound=..., upBound=..., cat=..., indexStart=...
    ): ...
    @classmethod
    def dicts(
        cls, name, indices=..., lowBound=..., upBound=..., cat=..., indexStart=...
    ):
        """
        This function creates a dictionary of :py:class:`LpVariable` with the specified associated parameters.

        :param name: The prefix to the name of each LP variable created
        :param indices: A list of strings of the keys to the dictionary of LP
            variables, and the main part of the variable name itself
        :param lowBound: The lower bound on these variables' range. Default is
            negative infinity
        :param upBound: The upper bound on these variables' range. Default is
            positive infinity
        :param cat: The category these variables are in, Integer or
            Continuous(default)

        :return: A dictionary of :py:class:`LpVariable`
        """
        ...

    @classmethod
    def dict(cls, name, indices, lowBound=..., upBound=..., cat=...): ...
    def getLb(self) -> float | None: ...
    def getUb(self) -> float | None: ...
    def bounds(self, low: float | None, up: float | None) -> None: ...
    def positive(self) -> None: ...
    def value(self) -> float | None: ...
    def round(self, epsInt: float = ..., eps: float = ...) -> None: ...
    def roundedValue(self, eps: float = ...) -> int | float | None: ...
    def valueOrDefault(self) -> float | Literal[0]: ...
    def valid(self, eps: float) -> bool: ...
    def infeasibilityGap(self, mip: int = ...) -> float | Literal[0]: ...
    def isBinary(self) -> bool: ...
    def isInteger(self) -> bool: ...
    def isFree(self) -> bool: ...
    def isConstant(self) -> bool: ...
    def isPositive(self) -> bool: ...
    def asCplexLpVariable(self) -> LiteralString: ...
    def asCplexLpAffineExpression(
        self, name: str, include_constant: bool = ...
    ) -> LiteralString: ...
    @override
    def __ne__(self, other: object) -> bool: ...
    @override
    def __bool__(self) -> bool: ...
    def addVariableToConstraints(self, e: dict[LpConstraintVar, float | int]) -> None:
        """adds a variable to the constraints indicated by
        the LpConstraintVars in e
        """
        ...

    def setInitialValue(self, val: float, check: bool = ...) -> bool:
        """
        sets the initial value of the variable to `val`
        May be used for warmStart a solver, if supported by the solver

        :param float val: value to set to variable
        :param bool check: if True, we check if the value fits inside the variable bounds
        :return: True if the value was set
        :raises ValueError: if check=True and the value does not fit inside the bounds
        """
        ...

    def fixValue(self) -> None:
        """
        changes lower bound and upper bound to the initial value if exists.
        :return: None
        """
        ...

    def isFixed(self) -> bool:
        """

        :return: True if upBound and lowBound are the same
        :rtype: bool
        """
        ...

    def unfixValue(self) -> None: ...

class LpAffineExpression(dict[LpVariable, int | float]):
    """
    A linear combination of :class:`LpVariables<LpVariable>`.
    Can be initialised with the following:

    #.   e = None: an empty Expression
    #.   e = dict: gives an expression with the values being the coefficients of the keys (order of terms is undetermined)
    #.   e = list or generator of 2-tuples: equivalent to dict.items()
    #.   e = LpElement: an expression of length 1 with the coefficient 1
    #.   e = other: the constant is initialised as e

    Examples:

       >>> f=LpAffineExpression(LpElement('x'))
       >>> f
       1*x + 0
       >>> x_name = ['x_0', 'x_1', 'x_2']
       >>> x = [LpVariable(x_name[i], lowBound = 0, upBound = 10) for i in range(3) ]
       >>> c = LpAffineExpression([ (x[0],1), (x[1],-3), (x[2],4)])
       >>> c
       1*x_0 + -3*x_1 + 4*x_2 + 0
    """

    trans: dict[int, int]
    @property
    def name(self) -> str | None: ...
    @name.setter
    def name(self, name: str | None) -> None: ...
    def __init__(
        self,
        e: float
        | LpAffineExpression
        | LpConstraint
        | LpElement
        | dict[LpVariable, int | float]
        | Iterable[tuple[LpVariable, int | float]] = ...,
        constant: float = ...,
        name: str | None = ...,
    ) -> None: ...
    def isAtomic(self) -> bool: ...
    def isNumericalConstant(self) -> bool: ...
    def atom(self) -> LpVariable: ...
    def __bool__(self) -> bool: ...
    def value(self) -> float | None: ...
    def valueOrDefault(self) -> float: ...
    def addterm(self, key: LpElement, value: float | int) -> None: ...
    def emptyCopy(self) -> LpAffineExpression: ...
    @override
    def copy(self) -> LpAffineExpression:
        """Make a copy of self except the name which is reset"""
        ...

    @override
    def __str__(
        self, include_constant: bool = ..., override_constant: float | None = ...
    ) -> str: ...
    def sorted_keys(self) -> list[LpElement]:
        """
        returns the list of keys sorted by name
        """
        ...

    @override
    def __repr__(self, override_constant: float | None = ...) -> str: ...
    def asCplexVariablesOnly(self, name: str) -> tuple[str, list[str]]:
        """
        helper for asCplexLpAffineExpression
        """
        ...

    def asCplexLpAffineExpression(
        self,
        name: str,
        include_constant: bool = ...,
        override_constant: float | None = ...,
    ) -> LiteralString:
        """
        returns a string that represents the Affine Expression in lp format
        """
        ...

    def addInPlace(self, other: _Addable, sign: Literal[+1, -1] = ...) -> Self:
        """
        :param int sign: the sign of the operation to do other.
            if we add other => 1
            if we subtract other => -1
        """
        ...

    def subInPlace(self, other: _Addable) -> Self: ...
    def __neg__(self) -> LpAffineExpression: ...
    def __pos__(self) -> Self: ...
    def __add__(self, other: _Addable) -> LpAffineExpression: ...
    def __radd__(self, other: _Addable) -> LpAffineExpression: ...
    def __iadd__(self, other: _Addable) -> Self: ...
    def __sub__(self, other: _Addable) -> LpAffineExpression: ...
    def __rsub__(self, other: _Addable) -> LpAffineExpression: ...
    def __isub__(self, other: _Addable) -> Self: ...
    def __mul__(self, other: _Multiplicable) -> LpAffineExpression: ...
    def __rmul__(self, other: _Multiplicable) -> LpAffineExpression: ...
    def __truediv__(self, other: _Multiplicable) -> LpAffineExpression: ...
    def __le__(self, other: _Addable) -> LpConstraint: ...
    def __ge__(self, other: _Addable) -> LpConstraint: ...
    @override
    def __eq__(self, other: _Addable) -> LpConstraint: ...
    def toDataclass(self) -> list[mpslp.MPSCoefficient]:
        """
        exports the :py:class:`LpAffineExpression` into a list of dataclasses with the coefficients
        it does not export the constant

        :return: list of :py:class:`mpslp.MPSCoefficient` with the coefficients
        :rtype: list
        """
        ...

    def toDict(self) -> list[dict[str, Any]]:
        """
        exports the :py:class:`LpAffineExpression` into a list of dictionaries with the coefficients
        it does not export the constant

        :return: list of dictionaries with the coefficients
        :rtype: list
        """
        ...

    def to_dict(self) -> list[dict[str, Any]]:
        """
        exports the :py:class:`LpAffineExpression` into a list of dictionaries with the coefficients
        it does not export the constant

        :return: list of dictionaries with the coefficients
        :rtype: list
        """
        ...

class LpConstraint:
    """An LP constraint"""
    def __init__(
        self,
        e: float
        | LpAffineExpression
        | LpConstraint
        | LpElement
        | dict[LpVariable, int | float]
        | Iterable[tuple[LpVariable, int | float]]
        | None = ...,
        sense: Literal[-1, 0, 1] = ...,
        name: str | None = ...,
        rhs: int | float | None = ...,
    ) -> None:
        """
        :param e: an instance of :class:`LpAffineExpression`
        :param sense: one of :data:`~pulp.const.LpConstraintEQ`, :data:`~pulp.const.LpConstraintGE`, :data:`~pulp.const.LpConstraintLE` (0, 1, -1 respectively)
        :param name: identifying string
        :param rhs: numerical value of constraint target
        """
        ...

    def getLb(self) -> float | None: ...
    def getUb(self) -> float | None: ...
    @override
    def __str__(self) -> str: ...
    @override
    def __repr__(self) -> str: ...
    def asCplexLpConstraint(self, name: str) -> LiteralString:
        """
        Returns a constraint as a string
        """
        ...

    def asCplexLpAffineExpression(
        self, name: str, include_constant: bool = ...
    ) -> LiteralString:
        """
        returns a string that represents the Affine Expression in lp format
        """
        ...

    def changeRHS(self, RHS: float) -> None:
        """
        alters the RHS of a constraint so that it can be modified in a resolve
        """
        ...

    def copy(self) -> LpConstraint:
        """Make a copy of self"""
        ...

    def emptyCopy(self) -> LpConstraint: ...
    def addInPlace(
        self,
        other: int | float | LpConstraint | LpAffineExpression | LpVariable,
        sign: Literal[+1, -1] = ...,
    ) -> Self:
        """
        :param int sign: the sign of the operation to do other.
            if we add other => 1
            if we subtract other => -1
        """
        ...

    def subInPlace(
        self,
        other: int | float | LpConstraint | LpAffineExpression | LpVariable,
    ) -> Self: ...
    def __neg__(self) -> LpConstraint: ...
    def __add__(
        self,
        other: int | float | LpConstraint | LpAffineExpression | LpVariable,
    ) -> LpConstraint: ...
    def __radd__(
        self,
        other: int | float | LpConstraint | LpAffineExpression | LpVariable,
    ) -> LpConstraint: ...
    def __sub__(
        self,
        other: int | float | LpConstraint | LpAffineExpression | LpVariable,
    ) -> LpConstraint: ...
    def __rsub__(
        self,
        other: int | float | LpConstraint | LpAffineExpression | LpVariable,
    ) -> LpConstraint: ...
    def __mul__(self, other: int | float | LpAffineExpression) -> LpConstraint: ...
    def __rmul__(self, other: int | float | LpAffineExpression) -> LpConstraint: ...
    def __truediv__(self, other: int | float | LpAffineExpression) -> LpConstraint: ...
    def valid(self, eps: float = ...) -> bool: ...
    def makeElasticSubProblem(
        self,
        penalty: float | None = ...,
        proprtionFreeBound: float | None = ...,
        proportionFreeBoundList: tuple[float, float] | None = ...,
    ) -> FixedElasticSubProblem:
        """
        Builds an elastic subproblem by adding variables to a hard constraint

        uses FixedElasticSubProblem
        """
        ...

    def toDataclass(self) -> mpslp.MPSConstraint:
        """
        Exports constraint information into a :py:class:`mpslp.MPSConstraint` dataclass

        :return: :py:class:`mpslp.MPSConstraint` with all the constraint information
        """
        ...

    @classmethod
    def fromDataclass(
        cls, mps: mpslp.MPSConstraint, variables: dict[str, LpVariable]
    ) -> LpConstraint:
        """
        Initializes a constraint object from a :py:class:`mpslp.MPSConstraint` dataclass and variables

        :param mps: :py:class:`mpslp.MPSConstraint` containing constraint information
        :param variables: dictionary of the variables
        :return: a new :py:class:`LpConstraint`
        """
        ...

    @property
    def name(self) -> str | None: ...
    @name.setter
    def name(self, name: str | None) -> None: ...
    def isAtomic(self) -> bool: ...
    def isNumericalConstant(self) -> bool: ...
    def atom(self) -> LpVariable: ...
    def __bool__(self) -> bool: ...
    def __len__(self) -> int: ...
    def __iter__(self) -> Iterator[LpVariable]: ...
    def __getitem__(self, key: LpElement) -> int | float: ...
    def get(self, key: LpVariable, default: float | None) -> float | None: ...
    def keys(self) -> dict_keys[LpVariable, int | float]: ...
    def values(self) -> dict_values[LpVariable, int | float]: ...
    def items(self) -> dict_items[LpVariable, int | float]: ...
    def value(self) -> float | None: ...
    def valueOrDefault(self) -> float: ...

class LpFractionConstraint(LpConstraint):
    """
    Creates a constraint that enforces a fraction requirement a/b = c
    """
    def __init__(
        self, numerator, denominator=..., sense=..., RHS=..., name=..., complement=...
    ) -> None:
        """
        creates a fraction Constraint to model constraints of
        the nature
        numerator/denominator {==, >=, <=} RHS
        numerator/(numerator + complement) {==, >=, <=} RHS

        :param numerator: the top of the fraction
        :param denominator: as described above
        :param sense: the sense of the relation of the constraint
        :param RHS: the target fraction value
        :param complement: as described above
        """
        ...

    def findLHSValue(self):
        """
        Determines the value of the fraction in the constraint after solution
        """
        ...

    def makeElasticSubProblem(self, *args: Any, **kwargs: Any):
        """
        Builds an elastic subproblem by adding variables and splitting the
        hard constraint

        uses FractionElasticSubProblem
        """
        ...

class LpConstraintVar(LpElement):
    """A Constraint that can be treated as a variable when constructing
    a LpProblem by columns
    """
    def __init__(self, name=..., sense=..., rhs=..., e=...) -> None: ...
    def addVariable(self, var, coeff):
        """
        Adds a variable to the constraint with the
        activity coeff
        """
        ...

    def value(self): ...

class LpProblem:
    """An LP Problem"""
    def __init__(self, name: str = ..., sense: Literal[-1, 1] = ...) -> None:
        """
        Creates an LP Problem

        This function creates a new LP Problem  with the specified associated parameters

        :param name: name of the problem used in the output .lp file
        :param sense: of the LP problem objective.  \
                Either :data:`~pulp.const.LpMinimize` (default) \
                or :data:`~pulp.const.LpMaximize`.
        :return: An LP Problem
        """
        ...

    @override
    def __repr__(self): ...
    @override
    def __getstate__(self) -> dict[str, Any]: ...
    def __setstate__(self, state: dict[str, Any]): ...
    def copy(self) -> LpProblem:
        """Make a copy of self. Expressions are copied by reference"""
        ...

    def deepcopy(self) -> LpProblem:
        """Make a copy of self. Expressions are copied by value"""
        ...

    def toDataclass(self) -> mpslp.MPS:
        """
        Creates a :py:class:`mpslp.MPS` from the model with as much data as possible.
        It replaces variables by variable names.
        So it requires to have unique names for variables.

        :return: :py:class:`mpslp.MPS` with model data
        :rtype: mpslp.MPS
        """
        ...

    @classmethod
    def fromDataclass(cls, mps: mpslp.MPS) -> tuple[dict[str, LpVariable], LpProblem]:
        """
        Takes a :py:class:`mpslp.MPS` with all necessary information to build a model.
        And returns a dictionary of variables and a problem object

        :param mps: :py:class:`mpslp.MPS` with the model stored
        :return: a tuple with a dictionary of variables and a :py:class:`LpProblem`
        """
        ...

    def toDict(self) -> dict[str, Any]: ...
    def to_dict(self) -> dict[str, Any]: ...
    @classmethod
    def fromDict(cls, data: dict[Any, Any]) -> LpProblem: ...
    @classmethod
    def from_dict(cls, data: dict[Any, Any]) -> LpProblem: ...
    def toJson(self, filename: str, *args: Any, **kwargs: Any) -> None:
        """
        Creates a json file from the LpProblem information

        :param str filename: filename to write json
        :param args: additional arguments for json function
        :param kwargs: additional keyword arguments for json function
        :return: None
        """
        ...

    def to_json(self, filename: str, *args: Any, **kwargs: Any) -> None: ...
    @classmethod
    def fromJson(cls, filename: str) -> tuple[dict[str, LpVariable], LpProblem]:
        """
        Creates a new LpProblem from a json file with information

        :param str filename: json file name
        :return: a tuple with a dictionary of variables and an LpProblem
        :rtype: (dict, :py:class:`LpProblem`)
        """
        ...

    @classmethod
    def from_json(cls, filename: str) -> tuple[dict[str, LpVariable], LpProblem]: ...
    @classmethod
    def fromMPS(
        cls, filename: str, sense: int = ..., dropConsNames: bool = ...
    ) -> tuple[dict[str, LpVariable], LpProblem]: ...
    def normalisedNames(
        self,
    ) -> tuple[dict[str, str], dict[str, str], Literal["OBJ"]]: ...
    def isMIP(self) -> Literal[0, 1]: ...
    def roundSolution(self, epsInt: float = ..., eps: float = ...) -> None:
        """
        Rounds the lp variables

        Inputs:
            - none

        Side Effects:
            - The lp variables are rounded
        """
        ...

    def unusedConstraintName(self) -> str: ...
    def valid(self, eps: float = ...) -> bool: ...
    def infeasibilityGap(self, mip: int = ...) -> float | Literal[0]: ...
    def addVariable(self, variable: LpVariable) -> None:
        """
        Adds a variable to the problem before a constraint is added

        :param variable: the variable to be added
        """
        ...

    def addVariables(self, variables: Iterable[LpVariable]) -> None:
        """
        Adds variables to the problem before a constraint is added

        :param variables: the variables to be added
        """
        ...

    def variables(self) -> list[LpVariable]:
        """
        Returns the problem variables

        :return: A list containing the problem variables
        :rtype: (list, :py:class:`LpVariable`)
        """
        ...

    def variablesDict(self) -> dict[str, LpVariable]: ...
    def add(self, constraint: LpConstraint, name: str | None = ...) -> None: ...
    def addConstraint(
        self, constraint: LpConstraint, name: str | None = ...
    ) -> None: ...
    def setObjective(
        self, obj: LpVariable | LpConstraint | LpConstraintVar | LpAffineExpression
    ) -> None:
        """
        Sets the input variable as the objective function. Used in Columnwise Modelling

        :param obj: the objective function of type :class:`LpConstraintVar`

        Side Effects:
            - The objective function is set
        """
        ...

    def __iadd__(
        self, other: _AddableToProblem | tuple[_AddableToProblem, str]
    ) -> Self: ...
    def extend(
        self,
        other: (
            LpProblem
            | dict[str, LpConstraint]
            | Iterable[tuple[str, LpConstraint] | LpConstraint]
        ),
        use_objective: bool = ...,
    ) -> None:
        """
        extends an LpProblem by adding constraints either from a dictionary
        a tuple or another LpProblem object.

        :param bool use_objective: determines whether the objective is imported from
        the other problem

        For dictionaries the constraints will be named with the keys
        For tuples an unique name will be generated
        For LpProblems the name of the problem will be added to the constraints
        name
        """
        ...

    def coefficients(
        self, translation: dict[str, str] | None = ...
    ) -> list[tuple[str, str, int | float]]: ...
    def writeMPS(
        self,
        filename: str,
        mpsSense: int = ...,
        rename: bool = ...,
        mip: bool = ...,
        with_objsense: bool = ...,
    ) -> (
        list[LpVariable]
        | tuple[list[LpVariable], dict[str, str], dict[str, str], str | None]
    ):
        """
        Writes an mps files from the problem information

        :param str filename: name of the file to write
        :param int mpsSense:
        :param bool rename: if True, normalized names are used for variables and constraints
        :param mip: variables and variable renames
        :return:

        Side Effects:
            - The file is created
        """
        ...

    def writeLP(
        self,
        filename: str,
        writeSOS: bool = ...,
        mip: bool = ...,
        max_length: int = ...,
    ) -> list[LpVariable]:
        """
        Write the given Lp problem to a .lp file.

        This function writes the specifications (objective function,
        constraints, variables) of the defined Lp problem to a file.

        :param str filename: the name of the file to be created.
        :return: variables

        Side Effects:
            - The file is created
        """
        ...

    def checkDuplicateVars(self) -> None:
        """
        Checks if there are at least two variables with the same name
        :return: 1
        :raises `const.PulpError`: if there ar duplicates
        """
        ...

    def checkLengthVars(self, max_length: int) -> None:
        """
        Checks if variables have names smaller than `max_length`
        :param int max_length: max size for variable name
        :return:
        :raises const.PulpError: if there is at least one variable that has a long name
        """
        ...

    def assignVarsVals(self, values: dict[str, float | None]) -> None: ...
    def assignVarsDj(self, values: dict[str, float | None]) -> None: ...
    def assignConsPi(self, values: dict[str, float]) -> None: ...
    def assignConsSlack(
        self, values: dict[str, float], activity: bool = ...
    ) -> None: ...
    def get_dummyVar(self) -> LpVariable: ...
    def fixObjective(self) -> tuple[bool, LpVariable | None]: ...
    def restoreObjective(self, wasNone: bool, dummyVar: LpVariable | None) -> None: ...
    def solve(self, solver: LpSolver | None = ..., **kwargs) -> int:
        """
        Solve the given Lp problem.

        This function changes the problem to make it suitable for solving
        then calls the solver.actualSolve() method to find the solution

        :param solver:  Optional: the specific solver to be used, defaults to the
              default solver.

        Side Effects:
            - The attributes of the problem object are changed in
              :meth:`~pulp.solver.LpSolver.actualSolve()` to reflect the Lp solution
        """
        ...

    def startClock(self) -> None:
        "initializes properties with the current time"
        ...

    def stopClock(self) -> None:
        "updates time wall time and cpu time"
        ...

    def sequentialSolve(
        self,
        objectives: Collection[
            LpVariable | LpConstraint | LpConstraintVar | LpAffineExpression
        ],
        absoluteTols: Iterable[float] | None = ...,
        relativeTols: Iterable[float] | None = ...,
        solver: LpSolver | None = ...,
        debug: bool = ...,
    ) -> list[int]:
        """
        Solve the given Lp problem with several objective functions.

        This function sequentially changes the objective of the problem
        and then adds the objective function as a constraint

        :param objectives: the list of objectives to be used to solve the problem
        :param absoluteTols: the list of absolute tolerances to be applied to
           the constraints should be +ve for a minimise objective
        :param relativeTols: the list of relative tolerances applied to the constraints
        :param solver: the specific solver to be used, defaults to the default solver.

        """
        ...

    def resolve(self, solver: LpSolver | None = ..., **kwargs) -> int | None:
        """
        resolves an Problem using the same solver as previously
        """
        ...

    def setSolver(self, solver: LpSolver = ...) -> None:
        """Sets the Solver for this problem useful if you are using
        resolve
        """
        ...

    def numVariables(self) -> int:
        """

        :return: number of variables in model
        """
        ...

    def numConstraints(self) -> int:
        """

        :return: number of constraints in model
        """
        ...

    def getSense(self) -> Literal[-1, 1]: ...
    def assignStatus(
        self,
        status: Literal[-3, -2, -1, 0, 1],
        sol_status: Literal[-2, -1, 0, 1, 2] | None = ...,
    ) -> Literal[True]:
        """
        Sets the status of the model after solving.
        :param status: code for the status of the model
        :param sol_status: code for the status of the solution
        :return:
        """
        ...

class FixedElasticSubProblem(LpProblem):
    """
    Contains the subproblem generated by converting a fixed constraint
    :math:`\\sum_{i}a_i x_i = b` into an elastic constraint.

    :param constraint: The LpConstraint that the elastic constraint is based on
    :param penalty: penalty applied for violation (+ve or -ve) of the constraints
    :param proportionFreeBound:
        the proportional bound (+ve and -ve) on
        constraint violation that is free from penalty
    :param proportionFreeBoundList: the proportional bound on \
        constraint violation that is free from penalty, expressed as a list\
        where [-ve, +ve]
    """
    def __init__(
        self,
        constraint: LpConstraint,
        penalty: float | None = ...,
        proportionFreeBound: float | None = ...,
        proportionFreeBoundList: tuple[float, float] | None = ...,
    ) -> None: ...
    def isViolated(self) -> bool:
        """
        returns true if the penalty variables are non-zero
        """
        ...

    def findDifferenceFromRHS(self) -> float:
        """
        The amount the actual value varies from the RHS (sense: LHS - RHS)
        """
        ...

    def findLHSValue(self) -> float:
        """
        for elastic constraints finds the LHS value of the constraint without
        the free variable and or penalty variable assumes the constant is on the
        rhs
        """
        ...

    def deElasticize(self) -> None:
        """de-elasticize constraint"""
        ...

    def reElasticize(self) -> None:
        """
        Make the Subproblem elastic again after deElasticize
        """
        ...

    def alterName(self, name: str) -> None:
        """
        Alters the name of anonymous parts of the problem
        """
        ...

class FractionElasticSubProblem(FixedElasticSubProblem):
    """
    Contains the subproblem generated by converting a Fraction constraint
    numerator/(numerator+complement) = b
    into an elastic constraint

    :param name: The name of the elastic subproblem
    :param penalty: penalty applied for violation (+ve or -ve) of the constraints
    :param proportionFreeBound: the proportional bound (+ve and -ve) on
        constraint violation that is free from penalty
    :param proportionFreeBoundList: the proportional bound on
        constraint violation that is free from penalty, expressed as a list
        where [-ve, +ve]
    """
    def __init__(
        self,
        name,
        numerator,
        RHS,
        sense,
        complement=...,
        denominator=...,
        penalty=...,
        proportionFreeBound=...,
        proportionFreeBoundList=...,
    ) -> None: ...
    def findLHSValue(self) -> float:
        """
        for elastic constraints finds the LHS value of the constraint without
        the free variable and or penalty variable assumes the constant is on the
        rhs
        """
        ...

    @override
    def isViolated(self) -> bool | None:
        """
        returns true if the penalty variables are non-zero
        """
        ...

def lpSum(
    vector: (
        Iterable[LpAffineExpression | LpVariable | int | float]
        | Iterable[tuple[LpElement, float]]
        | int
        | float
        | LpElement
    ),
) -> LpAffineExpression:
    """
    Calculate the sum of a list of linear expressions

    :param vector: A list of linear expressions
    """
    ...

def lpDot(
    v1: Collection[LpAffineExpression] | LpAffineExpression,
    v2: Collection[LpAffineExpression] | LpAffineExpression,
) -> LpAffineExpression:
    """Calculate the dot product of two lists of linear expressions"""
    ...
