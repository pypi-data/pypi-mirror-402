from __future__ import annotations

from quantagonia.extras import QUBO_EXTRA_ENABLED, raise_qubo_extras_error

if not QUBO_EXTRA_ENABLED:
    raise_qubo_extras_error()

import copy
from functools import singledispatchmethod
from typing import TYPE_CHECKING

from quantagonia.qubo.expression import QuboExpression

if TYPE_CHECKING:
    from quantagonia.qubo.variable import QuboVariable


class QuboTerm:
    def __init__(self, coefficient: float, variables: list[QuboVariable]):
        super().__init__()
        self.coefficient = coefficient

        # by convention, we only store the upper triangular part of the QUBO ->
        # need to sort the variables ascendingly by their IDs
        self.vars = self._unique_vars(variables)

    def clone(self) -> QuboTerm:
        return QuboTerm(self.coefficient, copy.copy(self.vars))

    def _join_vars(self, set0: list[QuboVariable], set1: list[QuboVariable]) -> list[QuboVariable]:
        return self._unique_vars([*set0, *set1])

    def _unique_vars(self, variables: list[QuboVariable]) -> list[QuboVariable]:
        joint = [(i.key(), i) for i in variables]
        joint = dict(joint)

        return sorted(joint.values(), key=lambda v: v.id())

    def key(self) -> str:
        return "_".join([str(v) for v in self.vars])

    def order(self) -> int:
        return len(self.vars)

    def check_is_qubo(self) -> bool:
        return self.order() <= 2

    def is_valid(self) -> bool:
        valid = self.check_is_qubo()

        if len(self.vars) > 1:
            valid &= self.vars[0].id() < self.vars[1].id()

        return valid

    def eval(self) -> float:
        # if term represents just the constant shift
        if self.order() == 0:
            return self.coefficient

        evaluation = self.coefficient * self.vars[0].eval()

        for var in self.vars[1:]:
            evaluation *= var.eval()

        return evaluation

    def __add__(self, other: float | QuboTerm | QuboExpression) -> QuboExpression:
        q = QuboExpression()
        q += self
        q += other

        return q

    def __sub__(self, other: float | QuboTerm | QuboExpression) -> QuboExpression:
        q = QuboExpression()
        q += self
        q -= other

        return q

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
    def __imul__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    @singledispatchmethod
    def __mul__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    def __rmul__(self, other: float):
        q = self.clone()
        q.coefficient *= other

        return q

    def __str__(self):
        s = ""
        if self.coefficient >= 0:
            s += "+ "
        else:
            s += "- "

        s += str(abs(self.coefficient))

        if self.order() > 0:
            s += " * " + str(self.vars[0])
            for var in self.vars[1:]:
                s += " * " + str(var)

        return s
