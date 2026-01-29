from __future__ import annotations

from typing import TYPE_CHECKING

from pyscipopt import Expr as Expression

if TYPE_CHECKING:
    from quantagonia.mip.variable import Variable


class tupledict(dict):  # noqa: N801
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def select(self, *pattern: str | int) -> list[Variable]:
        """Returns a list of values whose keys match the specified tuple pattern.

        Args:
            pattern (tuple): Tuple of keys to match against.

        Returns:
            List of variables that match the pattern.
        """
        if not pattern:
            return list(self.values())

        matches = []
        for key, value in self.items():
            if self._match_key_pattern(key, pattern):
                matches.append(value)
        return matches

    def sum(self, *pattern: str | int) -> Expression:
        """Returns the sum of values whose keys match the specified pattern.

        If values are objects like Variables, this returns an Expression.
        '*' acts as a wildcard in the pattern.

        Args:
            pattern (tuple): Tuple of keys to match against.

        Returns:
            Sum of the variables that match the pattern.
        """
        list_of_vars = self.select(*pattern)

        expr = Expression()
        for var in list_of_vars:
            expr = expr + 1 * var
        return expr

    def prod(self, coeff: dict, *pattern: str | int) -> Expression:
        """Returns a linear expression where each term is a product of a value with a coefficient.

        Args:
            coeff (dict): Dictionary that maps tuples to coefficients.
            pattern (tuple): Tuple of keys to match against.

        Returns:
            Linear expression with coefficients and monomials as described above.
        """
        # check if pattern is not given by the user
        if not pattern:
            expr = Expression()
            for key, value in self.items():
                if key in coeff:
                    expr = expr + coeff[key] * value
            return expr
        expr = Expression()
        for key, value in self.items():
            if key in coeff and self._match_key_pattern(key, pattern):
                expr = expr + coeff[key] * value
        return expr

    def clean(self) -> None:
        """Clears the internal cache used for efficient selection."""
        self.clear()

    def _match_key_pattern(self, key: tuple[str | int], pattern: tuple[str | int]) -> bool:
        """Helper method to check if a key matches a pattern with wildcards.

        Args:
            key: Tuple of keys to check.
            pattern: Tuple of keys to match against.

        Returns:
            True if the key matches the pattern, False otherwise.
        """
        # if exactly one element is missing in the pattern, we append a wildcard
        if len(pattern) == len(key) - 1:
            pattern = (*pattern, "*")
        if len(key) != len(pattern):
            return False
        return all(p in ("*", k) for k, p in zip(key, pattern))
