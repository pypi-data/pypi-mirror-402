"""Class to parse solution from file."""

from __future__ import annotations


class SolutionParser:
    def __init__(self):
        """Constructor."""

    @staticmethod
    def parse(solution_file: str) -> dict | None:
        """Parse solution from file."""
        if not len(solution_file):  # if file is empty
            return None

        sol_file_as_list = solution_file.splitlines()

        solution = {}

        # find index of 'Primal solution values' keyword
        try:
            key_idx = sol_file_as_list.index("Primal solution values:")
        except ValueError:
            # no solution
            return solution
        # get only the primal solution part
        sol_as_list = sol_file_as_list[key_idx + 1 :]

        # split entries to have var name and value
        for name_value_pair in sol_as_list:
            var_name, var_val = name_value_pair.split()
            solution[str(var_name)] = float(var_val)

        return solution
