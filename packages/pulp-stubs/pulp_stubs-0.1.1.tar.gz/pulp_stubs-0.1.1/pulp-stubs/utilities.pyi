from collections.abc import Iterable
from itertools import chain
from typing import SupportsIndex, TypeGuard, overload

from pulp.pulp import (
    LpAffineExpression,
    LpConstraint,
    LpConstraintVar,
    LpVariable,
)

def resource_clock() -> float: ...
def isNumber(x: object) -> TypeGuard[int | float]:
    """Returns true if x is an int or a float"""
    ...

@overload
def value(x: int) -> int: ...
@overload
def value(x: float) -> float: ...
@overload
def value(
    x: LpVariable | LpAffineExpression | LpConstraint | LpConstraintVar,
) -> float | None:
    """Returns the value of the variable/expression x, or x if it is a number"""
    ...

@overload
def valueOrDefault(x: int) -> int: ...
@overload
def valueOrDefault(x: float) -> float: ...
@overload
def valueOrDefault(
    x: LpVariable | LpAffineExpression | LpConstraint | LpConstraintVar,
) -> float | int:
    """Returns the value of the variable/expression x, or x if it is a number
    Variable without value (None) are affected a possible value (within their
    bounds)."""
    ...

def allpermutations[T](orgset: Iterable[T], k: SupportsIndex) -> chain[tuple[T, ...]]:
    """
    returns all permutations of orgset with up to k items

    :param orgset: the list to be iterated
    :param k: the maxcardinality of the subsets

    :return: an iterator of the subsets

    example:

    >>> c = allpermutations([1,2,3,4],2)
    >>> for s in c:
    ...     print(s)
    (1,)
    (2,)
    (3,)
    (4,)
    (1, 2)
    (1, 3)
    (1, 4)
    (2, 1)
    (2, 3)
    (2, 4)
    (3, 1)
    (3, 2)
    (3, 4)
    (4, 1)
    (4, 2)
    (4, 3)
    """
    ...

def allcombinations[T](orgset: Iterable[T], k: SupportsIndex) -> chain[tuple[T, ...]]:
    """
    returns all combinations of orgset with up to k items

    :param orgset: the list to be iterated
    :param k: the maxcardinality of the subsets

    :return: an iterator of the subsets

    example:

    >>> c = allcombinations([1,2,3,4],2)
    >>> for s in c:
    ...     print(s)
    (1,)
    (2,)
    (3,)
    (4,)
    (1, 2)
    (1, 3)
    (1, 4)
    (2, 3)
    (2, 4)
    (3, 4)
    """
    ...

def makeDict(headers, array, default=...):
    """
    makes a list into a dictionary with the headings given in headings
    headers is a list of header lists
    array is a list with the data
    """
    ...

def splitDict(data):
    """
    Split a dictionary with lists as the data, into smaller dictionaries

    :param dict data: A dictionary with lists as the values

    :return: A tuple of dictionaries each containing the data separately,
            with the same dictionary keys
    """
    ...

def read_table(data, coerce_type, transpose=...):
    """
    Reads in data from a simple table and forces it to be a particular type

    This is a helper function that allows data to be easily constained in a
    simple script
    ::return: a dictionary of with the keys being a tuple of the strings
       in the first row and colum of the table
    :param str data: the multiline string containing the table data
    :param coerce_type: the type that the table data is converted to
    :param bool transpose: reverses the data if needed

    Example:
    >>> table_data = '''
    ...         L1      L2      L3      L4      L5      L6
    ... C1      6736    42658   70414   45170   184679  111569
    ... C2      217266  227190  249640  203029  153531  117487
    ... C3      35936   28768   126316  2498    130317  74034
    ... C4      73446   52077   108368  75011   49827   62850
    ... C5      174664  177461  151589  153300  59916   135162
    ... C6      186302  189099  147026  164938  149836  286307
    ... '''
    >>> table = read_table(table_data, int)
    >>> table[("C1","L1")]
    6736
    >>> table[("C6","L5")]
    149836
    """
    ...
