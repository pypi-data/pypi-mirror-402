from __future__ import annotations

import json
from typing import Any


class HybridSolverParameters:
    """Class with setter options that allows to pass parameters to the solver."""

    def __init__(self):
        self._parameters = {}

    def to_str(self) -> str:
        """Returns solver options as string.

        Returns:
            str: Json string containing solver parameters.
        """
        return json.dumps(self._parameters)

    def to_dict(self) -> dict:
        """Returns solver options as dictionary.

        Returns:
            dict: Dictionary containing solver parameters.
        """
        return self._parameters

    def set_relative_gap(self, rel_gap: float) -> None:
        """Set the relative gap.

        The relative gap corresponds to the improvement potential of the objective value relative
        to the best-known objective value. It is defined as :math:`|f^* - f^-| / |f^*|`, where  :math:`f^*` is
        the best-known objective value and :math:`f^-` is the best-known bound on the objective value.
        The solver terminates once the relative gap falls below the specified value for :code:`rel_gap`.
        The default value is set to 1e-4 (0.01%).

        Args:
            rel_gap (float): A float representing the relative gap for termination.

        Returns:
            None.

        Raises:
            ValueError: If :code:`rel_gap` is not a float or integer.

        Example::

            rel_gap = 1e-2
            params.set_relative_gap(rel_gap)
        """
        param_name = "relative_gap"
        check_type(param_name, rel_gap, (float, int), type_name="numeric")
        check_numeric_value(param_name, rel_gap, lb=0)
        self._parameters[param_name] = rel_gap

    def set_absolute_gap(self, abs_gap: float) -> None:
        """Set the absolute gap.

        The absolute gap is the difference between the objective value :math:`f^*` of the best solution found
        and the best bound :math:`f^-` on the objective value.
        Hence, the absolute gap tells by how much the objective value could potentially still be improved.
        The solver terminates if the absolute gap falls below the specified value for :code:`abs_gap`.
        The default value is set to 1e-9.

        Args:
            abs_gap (float): A float representing the absolute gap for termination.

        Returns:
            None.

        Raises:
            ValueError: If :code:`abs_gap` is not a float or integer.

        Example::

            abs_gap = 1e-6
            params.set_absolute_gap(abs_gap)

        """
        param_name = "absolute_gap"
        check_type(param_name, abs_gap, (float, int), type_name="numeric")
        check_numeric_value(param_name, abs_gap, lb=0)
        self._parameters[param_name] = abs_gap

    def set_feasibility_tolerance(self, feas_tolerance: float) -> None:
        """Set the feasibility tolerance.

        The feasibility tolerance represents the acceptable deviation from feasibility for constraints.
        It is defined as the maximum allowable constraint violation.
        Specifically, the solver ensures that all constraints are satisfied within this tolerance.
        The solver accepts a solution as feasible if all constraint violations are within the specified tolerance.
        The default value is typically set to 1e-6.

        Args:
            feas_tolerance (float): A float representing the feasibility tolerance for constraints.

        Returns:
            None.

        Raises:
            ValueError: If :code:`feas_tolerance` is not a float or integer.

        Example::

            feas_tolerance = 1e-8
            params.set_feasibility_tolerance(feas_tolerance)
        """
        param_name = "feasibility_tolerance"
        check_type(param_name, feas_tolerance, (float, int), type_name="numeric")
        check_numeric_value(param_name, feas_tolerance, lb=1e-9)
        self._parameters[param_name] = feas_tolerance

    def set_integrality_tolerance(self, int_tolerance: float) -> None:
        """Set the integrality tolerance.

        The integrality tolerance represents the acceptable deviation from feasibility for integrality conditions.
        It is defined as the maximum allowable integrality violation.
        Specifically, the solver ensures that all integer variables deviate no more than this tolerance \
        from their nearest integer value.
        The solver accepts a solution as feasible if all integrality conditions are within the specified tolerance.
        The default value is typically set to 1e-5.

        Args:
            int_tolerance (float): A float representing the integrality tolerance for integrality.

        Returns:
            None.

        Raises:
            ValueError: If :code:`int_tolerance` is not a float or integer.

        Example::

            int_tolerance = 1e-7
            params.set_integrality_tolerance(int_tolerance)
        """
        param_name = "integrality_tolerance"
        check_type(param_name, int_tolerance, (float, int), type_name="numeric")
        check_numeric_value(param_name, int_tolerance, lb=1e-10)
        self._parameters[param_name] = int_tolerance

    def set_time_limit(self, time_limit: float) -> None:
        """Sets time limit.

        The solver runs at most for 'time_limit' seconds and returns the best found solution along with the
        optimality gap. The optimality gap tells you by how much the solution could possibly be improved,
        if the solver continues to run.

        Returns:
            None

        Example::

            time_limit = 10  # seconds
            params.set_time_limit(time_limit)
        """
        param_name = "time_limit"
        check_type(param_name, time_limit, (float, int), type_name="numeric")
        check_numeric_value(param_name, time_limit, lb=0)
        self._parameters[param_name] = time_limit

    def set_performance_code(self, performance_code: str) -> None:
        """Sets a performance code for a specific solver version.

        The performance code parameter enables optimizations tailored to a specific solver version,
        enhancing performance for instances that are similar or belong to a defined class.
        When applied, the solver may find solutions and prove optimality faster
        by leveraging these targeted adjustments.

        Returns:
            None

        Example::

            performance_code = "Quantagonia-42"
            params.set_performance_code(performance_code)
        """
        param_name = "performance_code"
        check_type(param_name, performance_code, (str), type_name="string")
        self._parameters[param_name] = performance_code

    def set_as_qubo(self, as_qubo: bool) -> None:
        """Set the as_qubo option (IP only).

        If true, the HybridSolver attempts to reformulate the given IP to a QUBO.
        If successful, the problem is solved as such.

        Note that this is an experimental feature which is expected to solve the problem (significantly)
        slower compared to the default (without reformulation to QUBO).

        Args:
            as_qubo (bool): A bool that enables or disables the as_qubo option.

        Returns:
            None.

        Raises:
            ValueError: If :code:`as_qubo` is not a bool.

        """
        param_name = "as_qubo"
        check_type(param_name, as_qubo, bool)
        self._parameters[param_name] = as_qubo

    def set_qubo_decomposition(self, qubo_decomposition: bool) -> None:
        """Set the qubo_decomposition option (MIP only).

        If true, the HybridSolver attempts to decompose the MIP into MIP and QUBO subproblems.
        If successful, the original problem is solved to global optimality by solving a series of smaller
        MIPs and QUBOs.

        Note that this is an experimental feature which is expected to solve the problem (significantly)
        slower compared to the default (without decomposition).

        Args:
            qubo_decomposition (bool): A bool that enables or disables the qubo_decomposition option.

        Returns:
            None.

        Raises:
            ValueError: If :code:`qubo_decomposition` is not a bool.

        """
        param_name = "qubo_decomposition"
        check_type(param_name, qubo_decomposition, bool)
        self._parameters[param_name] = qubo_decomposition

    def set_presolve(self, presolve: bool) -> None:
        """Enable or disable presolve.

        Args:
            presolve (bool): A boolean indicating whether to enable or disable presolve.

        Returns:
            None.

        Raises:
            ValueError: If :code:`presolve` is not a boolean.

        Example::

            params.set_presolve(False)

        """
        param_name = "presolve"
        check_type(param_name, presolve, bool)
        self._parameters[param_name] = presolve

    def set_seed(self, seed: float) -> None:
        """Set the random number seed.

        This acts as a small perturbation to some subroutines of the solver and may lead to different solution paths.

        Args:
            seed (float): The random number seed.

        Returns:
            None.

        """
        param_name = "seed"
        check_type(param_name, seed, (float, int), type_name="numeric")
        self._parameters[param_name] = seed

    def set_heuristics_only(self, heuristics_only: bool) -> None:
        """Only apply the root node primal heuristics and then terminate (QUBO only).

        This waits until *all* primal heuristics are finished and displays a table with
        objective value and runtime per heuristic.

        Args:
            heuristics_only (bool): Flag to enable or disable heuristics_only mode.

        Returns:
            None
        """
        param_name = "heuristics_only"
        check_type(param_name, heuristics_only, bool)
        self._parameters[param_name] = heuristics_only

    def set_objective_limit(self, objective_value: float) -> None:
        """Sets a limit on the objective value to terminate optimization.

        The solver terminates as soon as it finds a feasible solution with an objective value at least as
        good as the specified :code:`objective_value`.

        Args:
            objective_value (float): A float representing the termination value for the objective.

        Returns:
            None.

        Raises:
            ValueError: If :code:`objective_value` is not a float or integer.

        """
        param_name = "objective_limit"
        check_type(param_name, objective_value, (float, int), type_name="numeric")
        self._parameters[param_name] = objective_value


def check_type(
    option_name: str,
    option_value: Any,  # noqa ANN401
    type_: type | tuple[type, ...],
    type_name: str | None = None,
) -> None:
    if not isinstance(option_value, type_):
        if type_name is None:
            type_name = type_.__name__
        error_message = f"Value for {option_name} is set to {option_value} but must be a {type_name}."
        raise TypeError(error_message)


def check_numeric_value(
    option_name: str, option_value: float, lb: float | None = None, ub: float | None = None
) -> None:
    if lb is not None and option_value < lb:
        error_message = f"Value for {option_name} must be >= {lb}"
        raise ValueError(error_message)
    if ub is not None and option_value > ub:
        error_message = f"Value for {option_name} must be <= {ub}"
        raise ValueError(error_message)
