from __future__ import annotations

from quantagonia.extras import QUBO_EXTRA_ENABLED, raise_qubo_extras_error

if not QUBO_EXTRA_ENABLED:
    raise_qubo_extras_error()

import warnings
from functools import singledispatchmethod
from typing import Literal

from quantagonia.errors.errors import AssignmentError
from quantagonia.qubo.expression import QuboExpression
from quantagonia.qubo.term import QuboTerm


class QuboVariable:
    def __init__(self, name: str, pos: int, initial: Literal[0, 1] | None = None, fixing: Literal[0, 1] | None = None):
        self.name = name
        self._pos = pos
        if initial and initial not in [0, 1]:
            warnings.warn(f"Initial variable value {initial} not binary. Ignore initial assignment.", stacklevel=2)
            initial = None
        if fixing is not None and fixing not in [0, 1]:
            warnings.warn(f"Fixing variable value {fixing} not binary. Ignore fixing.", stacklevel=2)
            fixing = None
        if initial is not None and fixing is not None and initial != fixing:
            warnings.warn("Initial != fixing, discard initial and use fixing", stacklevel=2)
            initial = fixing
        self.fixing: Literal[0, 1] | None = fixing
        self._assignment: Literal[0, 1] | None = initial

    @property
    def assignment(self) -> Literal[0, 1] | None:
        return self._assignment

    @assignment.setter
    def assignment(self, value: Literal[0, 1]) -> None:
        # check against fixing
        if self.fixing and self.fixing != value:
            error_message = f"Assigning {value} to {self.name} contradicts fixing {self.fixing}"
            raise AssignmentError(error_message)
        self._assignment = value

    def id(self) -> int:
        return self._pos

    def eval(self) -> Literal[0, 1]:
        if self.assignment is None:
            raise AssignmentError("Variable " + self.name + " is still unassigned.")
        return self.assignment

    def __str__(self) -> str:
        return str(self.name)

    def key(self) -> str:
        return str(self)

    @singledispatchmethod
    def __add__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    @singledispatchmethod
    def __sub__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    def __radd__(self, other: float) -> QuboExpression:
        q = QuboExpression()
        q += QuboTerm(other, [])
        q += self
        return q

    def __rsub__(self, other: float) -> QuboExpression:
        q = QuboExpression()
        q += QuboTerm(other, [])
        q -= self
        return q

    @singledispatchmethod
    def __mul__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    # other * var -> term
    def __rmul__(self, other: float) -> QuboTerm:
        return QuboTerm(other, [self])
