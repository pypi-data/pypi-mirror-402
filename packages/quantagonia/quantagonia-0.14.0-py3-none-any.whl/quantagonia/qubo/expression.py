from __future__ import annotations

from quantagonia.extras import QUBO_EXTRA_ENABLED, raise_qubo_extras_error

if not QUBO_EXTRA_ENABLED:
    raise_qubo_extras_error()

if not QUBO_EXTRA_ENABLED:
    error_message = "The qubo extra is not enabled. Please install via 'pip install quantagonia[qubo]'."
    raise ImportError(error_message)

from functools import singledispatchmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from quantagonia.qubo.term import QuboTerm
    from quantagonia.qubo.variable import QuboVariable


class QuboExpression:
    def __init__(self):
        super().__init__()

        # hash -> (term with coefficient)
        self.terms = {}

    def clone(self) -> QuboExpression:
        q = QuboExpression()
        for k in self.terms:
            q.terms[k] = self.terms[k].clone()

        return q

    ###
    # ADDITION + SUBTRACTION
    ###

    # join clones of term dictionaries
    @staticmethod
    def _join_terms(
        terms0: dict[str, QuboTerm], terms1: dict[str, QuboTerm], op_coefficient: float
    ) -> dict[str, QuboTerm]:
        joint_terms = {}
        for key, term in terms0.items():
            joint_terms[key] = term.clone()
        for term in terms1.values():
            QuboExpression._left_join_term(joint_terms, term, op_coefficient)

        return joint_terms

    # join second dictionary into first
    @staticmethod
    def _left_join_terms(
        terms0: dict[str, QuboTerm], terms1: dict[str, QuboTerm], op_coefficient: float
    ) -> dict[str, QuboTerm]:
        for right_term in terms1.values():
            QuboExpression._left_join_term(terms0, right_term, op_coefficient)

        return terms0

    @staticmethod
    def _left_join_term(term0: dict[str, QuboTerm], term1: QuboTerm, op_coefficient: float) -> dict[str, QuboTerm]:
        if term1.key() in term0:
            term0[term1.key()].coefficient += op_coefficient * term1.coefficient
        else:
            term0[term1.key()] = term1.clone()
        return term0

    @singledispatchmethod
    def __iadd__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    @singledispatchmethod
    def __isub__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    def __add__(self, other: float | QuboVariable | QuboTerm | QuboExpression):
        q = self.clone()
        return q.__iadd__(other)

    def __sub__(self, other: float | QuboVariable | QuboTerm | QuboExpression):
        q = self.clone()
        return q.__isub__(other)

    @singledispatchmethod
    def __radd__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    @singledispatchmethod
    def __rsub__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    @singledispatchmethod
    def __imul__(self, other):  # noqa ANN001, ANN201
        return NotImplemented

    def __mul__(self, other: float | QuboVariable | QuboTerm | QuboExpression):
        q = self.clone()
        q *= other
        return q

    def __rmul__(self, other: float):
        q = self.clone()
        for term_key in q.terms:
            q.terms[term_key] *= other
        return q

    def eval(self, shift: float = 0) -> float:
        evaluation = shift

        for term in self.terms:
            evaluation += self.terms[term].eval()

        return evaluation

    def is_valid(self) -> bool:
        valid = True

        for term in self.terms.values():
            valid &= term.is_valid()

        return valid

    def __str__(self):
        return " ".join([str(self.terms[t]) for t in self.terms])
