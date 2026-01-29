# ruff: noqa: ANN001 self is not recognized as self by ruff, hence we disable forced type hints for this file

from quantagonia.extras import QUBO_EXTRA_ENABLED, raise_qubo_extras_error

if not QUBO_EXTRA_ENABLED:
    raise_qubo_extras_error()

from quantagonia.errors.errors import ModelError
from quantagonia.qubo.expression import QuboExpression
from quantagonia.qubo.term import QuboTerm
from quantagonia.qubo.variable import QuboVariable

###
## QuboVariable - add
###


@QuboVariable.__add__.register
def _(self, other: int) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q += QuboTerm(float(other), [])

    return q


@QuboVariable.__add__.register
def _(self, other: float) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q += QuboTerm(other, [])

    return q


@QuboVariable.__add__.register
def _(self, other: QuboVariable) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q += QuboTerm(1.0, [other])

    return q


@QuboVariable.__add__.register
def _(self, other: QuboTerm) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q += other

    return q


@QuboVariable.__add__.register
def _(self, other: QuboExpression) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q += other

    return q


###
## QuboVariable - sub
###


@QuboVariable.__sub__.register
def _(self, other: int) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q -= QuboTerm(float(other), [])

    return q


@QuboVariable.__sub__.register
def _(self, other: float) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q -= QuboTerm(other, [])

    return q


@QuboVariable.__sub__.register
def _(self, other: QuboVariable) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q -= QuboTerm(1.0, [other])

    return q


@QuboVariable.__sub__.register
def _(self, other: QuboTerm) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q -= other

    return q


@QuboVariable.__sub__.register
def _(self, other: QuboExpression) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(1.0, [self])
    q -= other

    return q


###
## QuboVariable - mul
###


@QuboVariable.__mul__.register
def _(self, other: int) -> QuboTerm:
    return QuboTerm(float(other), [self])


@QuboVariable.__mul__.register
def _(self, other: float) -> QuboTerm:
    return QuboTerm(other, [self])


@QuboVariable.__mul__.register
def _(self, other: QuboVariable) -> QuboTerm:
    return QuboTerm(1.0, [self, other])


@QuboVariable.__mul__.register
def _(self, other: QuboTerm) -> QuboExpression:
    q = other.clone()
    q *= QuboTerm(1.0, [self])

    return q


@QuboVariable.__mul__.register
def _(self, other: QuboExpression) -> QuboExpression:
    q = other.clone()
    q *= QuboTerm(1.0, [self])

    return q


###
## QuboTerm - imul
###


@QuboTerm.__imul__.register
def _(self, other: int) -> QuboTerm:
    self.coefficient *= other
    return self


@QuboTerm.__imul__.register
def _(self, other: float) -> QuboTerm:
    self.coefficient *= other
    return self


@QuboTerm.__imul__.register
def _(self, other: QuboVariable) -> QuboTerm:
    return self.__imul__(QuboTerm(1.0, [other]))


@QuboTerm.__imul__.register
def _(self, other: QuboTerm) -> QuboTerm:
    self.coefficient *= other.coefficient
    self.vars = self._join_vars(self.vars, other.vars)

    if self.order() > 2:
        error_message = "Only QuboTerms with order <= 2 are supported."
        raise ModelError(error_message)

    return self


###
## QuboTerm - mul
###


@QuboTerm.__mul__.register
def _(self, other: int) -> QuboTerm:
    q = self.clone()
    q *= other
    return q


@QuboTerm.__mul__.register
def _(self, other: float) -> QuboTerm:
    q = self.clone()
    q *= other
    return q


@QuboTerm.__mul__.register
def _(self, other: QuboVariable) -> QuboTerm:
    q = self.clone()
    q *= other
    return q


@QuboTerm.__mul__.register
def _(self, other: QuboTerm) -> QuboTerm:
    q = self.clone()
    q *= other
    return q


@QuboTerm.__mul__.register
def _(self, other: QuboExpression) -> QuboExpression:
    q = other.clone()
    q *= self
    return q


###
## QuboExpression - iadd
###


@QuboExpression.__iadd__.register
def _(self, other: int) -> QuboExpression:
    if "" in self.terms:
        self.terms[""].coefficient += other
    else:
        self.terms[""] = QuboTerm(float(other), [])
    return self


@QuboExpression.__iadd__.register
def _(self, other: float) -> QuboExpression:
    if "" in self.terms:
        self.terms[""].coefficient += other
    else:
        self.terms[""] = QuboTerm(float(other), [])
    return self


@QuboExpression.__iadd__.register
def _(self, other: QuboVariable) -> QuboExpression:
    return self.__iadd__(QuboTerm(1.0, [other]))


@QuboExpression.__iadd__.register
def _(self, other: QuboTerm) -> QuboExpression:
    q = QuboExpression()
    q.terms[other.key()] = other

    return self.__iadd__(q)


@QuboExpression.__iadd__.register
def _(self, other: QuboExpression) -> QuboExpression:
    self.terms = self._left_join_terms(self.terms, other.terms, 1.0)
    return self


###
## QuboExpression - isub
###


@QuboExpression.__isub__.register
def _(self, other: int) -> QuboExpression:
    return self.__iadd__(-1.0 * other)


@QuboExpression.__isub__.register
def _(self, other: float) -> QuboExpression:
    return self.__iadd__(-1.0 * other)


@QuboExpression.__isub__.register
def _(self, other: QuboVariable) -> QuboExpression:
    return self.__isub__(QuboTerm(1.0, [other]))


@QuboExpression.__isub__.register
def _(self, other: QuboTerm) -> QuboExpression:
    q = QuboExpression()
    q.terms[other.key()] = other.clone()
    q.terms[other.key()].coefficient *= -1.0

    return self.__iadd__(q)


@QuboExpression.__isub__.register
def _(self, other: QuboExpression) -> QuboExpression:
    self.terms = self._left_join_terms(self.terms, other.terms, -1.0)
    return self


###
## QuboExpression - imul
###


@QuboExpression.__imul__.register
def _(self, other: int) -> QuboExpression:
    for term_key in self.terms:
        self.terms[term_key] *= other
    return self


@QuboExpression.__imul__.register
def _(self, other: float) -> QuboExpression:
    for term_key in self.terms:
        self.terms[term_key] *= other
    return self


@QuboExpression.__imul__.register
def _(self, other: QuboTerm) -> QuboExpression:
    new_terms = {}
    for term in self.terms.values():
        new_term = term * other
        # Actually not a private access due to dispatching, hence the noqa
        QuboExpression._left_join_term(new_terms, new_term, 1.0)  # noqa SLF001
    self.terms = new_terms
    return self


@QuboExpression.__imul__.register
def _(self, other: QuboVariable) -> QuboExpression:
    new_terms = {}
    for term in self.terms.values():
        new_term = term * other
        # Actually not a private access due to dispatching, hence the noqa
        QuboExpression._left_join_term(new_terms, new_term, 1.0)  # noqa: SLF001
    self.terms = new_terms
    return self


@QuboExpression.__imul__.register
def _(self, other: QuboExpression) -> QuboExpression:
    q = QuboExpression()
    for s_term in self.terms.values():
        for o_term in other.terms.values():
            q += s_term * o_term

    self.terms = q.terms
    return self


###
## QuboExpression - radd
###


@QuboExpression.__radd__.register
def _(self, other: int) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(other, [])
    q += self
    return q


@QuboExpression.__radd__.register
def _(self, other: float) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(other, [])
    q += self
    return q


###
## QuboExpression - rsub
###


@QuboExpression.__rsub__.register
def _(self, other: int) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(other, [])
    q -= self
    return q


@QuboExpression.__rsub__.register
def _(self, other: float) -> QuboExpression:
    q = QuboExpression()
    q += QuboTerm(other, [])
    q -= self
    return q
