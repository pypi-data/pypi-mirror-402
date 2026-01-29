from __future__ import annotations

import os
import tempfile

from pyscipopt import Expr as Expression
from pyscipopt import Model as _Model

from quantagonia import HybridSolver, HybridSolverParameters
from quantagonia.enums import HybridSolverOptSenses, HybridSolverStatus, VarType
from quantagonia.errors.errors import ModelError
from quantagonia.extras import SuppressScipOutput
from quantagonia.mip.variable import Variable


class Model:
    """A class representing a Mixed Integer Programming (MIP) problem instance.

    Args:
        name (str): (optional) The name of the MIP model. Defaults to "model".

    """

    def __init__(self, name: str = "Model") -> None:
        """Initializes the Model instance with a given name.

        Args:
            name (str): (optional) The name of the model. Defaults to "Model".

        Raises:
            ValueError: If the QUANTAGONIA_API_KEY environment variable is not set.
        """
        api_key = os.getenv("QUANTAGONIA_API_KEY")
        if api_key is None:
            msg = "QUANTAGONIA_API_KEY not found"
            raise ValueError(msg)
        self._hybrid_solver = HybridSolver(api_key)

        self._name = name
        self._model = _Model(name)
        self._model.redirectOutput()  # Redirect output to stdout
        self._sol_status = HybridSolverStatus.UNKNOWN
        self._best_bound = None
        self._solution = None
        self._best_objective = None
        self._best_time = None
        self._total_time = None
        self._objective_function = None
        self._parameters = HybridSolverParameters()

    @property
    def type(self) -> str:
        """The type of the model.

        Returns:
            str: The type of the model.
        """
        return self._type

    @property
    def model(self) -> _Model:
        return self._model

    @property
    def name(self) -> str:
        """The name of the model.

        Returns:
            str: The name of the model.
        """
        return self._name

    @property
    def sense(self) -> HybridSolverOptSenses:
        """The optimization sense of the model.

        Returns:
            HybridSolverOptSenses: The current optimization sense of the model.

        Raises:
            ModelError: If the current sense is unsupported.
        """
        if self._model.getObjectiveSense() == "minimize":
            return HybridSolverOptSenses.MINIMIZE
        if self._model.getObjectiveSense() == "maximize":
            return HybridSolverOptSenses.MAXIMIZE
        error_message = "Unsupported sense."
        raise ModelError(error_message)

    @sense.setter
    def sense(self, sense: HybridSolverOptSenses) -> None:
        """Sets the optimization sense of the model.

        Args:
            sense (HybridSolverOptSenses): The optimization sense to be set.

        Raises:
            ModelError: If the provided sense is unsupported.
        """
        if sense in [HybridSolverOptSenses.MINIMIZE]:
            self._model.setMinimize()
        elif sense in [HybridSolverOptSenses.MAXIMIZE]:
            self._model.setMaximize()
        else:
            error_message = "Unsupported sense."
            raise ModelError(error_message)

    @property
    def objective_value(self) -> float:
        """The objective value of the model's best solution.

        Returns:
            float: The objective value of the best solution found.
        """
        return self._best_objective

    @property
    def solution_status(self) -> HybridSolverStatus:
        """The solution status of the model.

        Returns:
            HybridSolverStatus: The current solution status of the model.
        """
        return self._sol_status

    @property
    def solution(self) -> dict[str, float]:
        """The solution of the model.

        Returns:
            dict[str, float]: A dictionary mapping variable names to their values in the solution.
        """
        return self._solution

    @solution.setter
    def solution(self, solution: dict[str, float]) -> None:
        """Sets the solution of the model.

        Args:
            solution (dict[str, float]): A dictionary mapping variable names to their values in the solution.
        """
        self._solution = solution

    @property
    def best_bound(self) -> float:
        """The best bound of the model.

        Returns:
            float: The best bound found during optimization.
        """
        return self._best_bound

    @property
    def best_time(self) -> float:
        """The runtime (in seconds) after which the best solution was found.

        Returns:
            float: The runtime (in seconds) after which the best solution was found.
        """
        return self._best_time

    @property
    def total_time(self) -> float:
        """The total runtime of the optimization process.

        Returns:
            float: The total runtime (in seconds) of the optimization process.
        """
        return self._total_time

    @property
    def objective_offset(self) -> float:
        """The offset of the objective function.

        Returns:
            float: The constant offset value of the objective function.
        """
        return self._model.getObjoffset()

    @property
    def n_vars(self) -> int:
        """The number of variables in the model.

        Returns:
            int: The number of variables in the model.
        """
        return self._model.getNVars()

    @property
    def n_bin_vars(self) -> int:
        """The number of binary variables in the model.

        Returns:
            int: The number of binary variables in the model.
        """
        return self._model.getNBinVars()

    @property
    def n_int_vars(self) -> int:
        """The number of integer variables in the model.

        Returns:
            int: The number of integer variables in the model.
        """
        return self._model.getNIntVars()

    @property
    def n_cont_vars(self) -> int:
        """The number of continuous variables in the model.

        Returns:
            int: The number of continuous variables in the model.
        """
        return self.n_vars - self.n_bin_vars - self.n_int_vars

    @property
    def parameters(self) -> dict:
        """The parameters of the model.

        Returns:
            dict: A dictionary containing the parameters of the model.
        """
        return self._parameters.to_dict()

    def add_variable(
        self,
        lb: float = 0,
        ub: float = float("Inf"),
        name: str = "",
        coeff: float = 0,
        var_type: VarType = VarType.CONTINUOUS,
    ) -> Variable:
        """Adds a new variable to the model.

        Args:
            lb (float): The lower bound of the variable. Defaults to 0.
            ub (float): The upper bound of the variable. Defaults to positive infinity.
            name (str): The name of the variable. Defaults to an empty string.
            coeff (float): The coefficient of the variable in the objective function. Defaults to 0.
            var_type (VarType): The type of the variable. Defaults to VarType.CONTINUOUS.

        Returns:
            Variable: The Variable instance that was added to the MIP model.

        Raises:
            ModelError: If the variable type is unsupported or if the variable addition fails.
        """
        if var_type == VarType.CONTINUOUS:
            vtype = "C"
        elif var_type == VarType.BINARY:
            vtype = "B"
        elif var_type == VarType.INTEGER:
            vtype = "I"
        else:
            error_message = "Unsupported variable type."
            raise ModelError(error_message)
        try:
            # Suppress SCIP output
            with SuppressScipOutput():
                var = self._model.addVar(name, vtype, lb, ub, coeff)
        except ValueError as e:
            error_message = f"Failed to add variable '{name}'."
            raise ModelError(error_message) from e
        return Variable(var, self)

    def get_variables(self) -> list[Variable]:
        """Returns a list of all variables in the model.

        Returns:
            list[Variable]: A list of all variables in the model.
        """
        return [Variable(var, self) for var in self._model.getVars()]

    def add_constraint(self, expr: Expression, name: str = "") -> None:
        """Adds a constraint to the model.

        Args:
            expr (Expression): The expression representing the constraint.
            name (str): (optional) The name of the constraint.

        Raises:
            ModelError: If the constraint addition fails.
        """
        try:
            # Suppress SCIP output
            with SuppressScipOutput():
                self._model.addCons(expr, name)
        except ValueError as e:
            error_message = f"Failed to add constraint '{name}'."
            raise ModelError(error_message) from e

    def add_constraints(self, constraints: list[tuple[Expression, str]]) -> None:
        """Adds multiple constraints to the model.

        Args:
            constraints (List[Tuple[Expression, str]]): A list of tuples, each containing
                an expression and a name for a constraint.
        """
        for constraint in constraints:
            try:
                # Suppress SCIP output
                with SuppressScipOutput():
                    self.add_constraint(constraint[0], constraint[1])
            except ValueError as e:
                error_message = f"Failed to add constraint '{constraint[1]}'."
                raise ModelError(error_message) from e

    def set_objective(
        self,
        expr: Expression = None,
        sense: HybridSolverOptSenses = HybridSolverOptSenses.MINIMIZE,
    ) -> None:
        """Sets the objective function for the model.

        Args:
            expr (Expression): The expression representing the objective function.
            sense (HybridSolverOptSenses): The optimization sense (minimize or maximize).
                Defaults to HybridSolverOptSenses.MINIMIZE.

        Raises:
            ModelError: If the sense is unsupported or if setting the objective fails.
        """
        if expr is None:
            error_message = "Objective expression is missing."
            raise ModelError(error_message)
        if sense == HybridSolverOptSenses.MINIMIZE:
            ref_sense = "minimize"
        elif sense == HybridSolverOptSenses.MAXIMIZE:
            ref_sense = "maximize"
        else:
            error_message = "Unsupported sense."
            raise ModelError(error_message)
        try:
            # Suppress SCIP output
            with SuppressScipOutput():
                self._objective_function = expr
                self._model.setObjective(expr=expr, sense=ref_sense, clear=False)
        except ValueError as e:
            error_message = "Failed to set objective."
            raise ModelError(error_message) from e

    def add_objective_offset(self, offset: float) -> None:
        """Adds an offset to the objective function of the model.

        Args:
            offset (float): The offset value to be added to the objective function.
        """
        self._model.addObjoffset(offset)

    def _assign_solution(self, solution: dict[str, float]) -> None:
        """Assigns the solution to the reference model.

        Args:
            solution (dict[str, float]): A dictionary mapping variable names to their values.

        Raises:
            RuntimeError: If the solution has an incorrect length or cannot be assigned to a variable.
            ValueError: If the cloud solution is not feasible for the local model.
            ModelError: If the cloud solution cannot be added to the local model.
        """
        variables = self._model.getVars()
        if len(solution) != len(variables):
            msg = "Solution has incorrect length"
            raise RuntimeError(msg)

        # create local solution
        try:
            # Suppress SCIP output
            with SuppressScipOutput():
                local_solution = self._model.createOrigSol()
        except ValueError as e:
            msg = "Model failed to assign the solution computed by HybridSolver"
            raise RuntimeError(msg) from e

        # inject cloud solution to local solution
        for var in variables:
            try:
                # Suppress SCIP output
                with SuppressScipOutput():
                    self._model.setSolVal(local_solution, var, solution[str(var)])
            except Exception as e:
                msg = f"Couldn't assign solution to variable {var}"
                raise RuntimeError(msg) from e

        # check if HybridSolver solution is feasible
        feasible = self._model.checkSol(local_solution)
        if not feasible:
            msg = "Cloud solution is not feasible for local model"
            raise ValueError(msg)

        # add cloud solution to local model
        added = self._model.addSol(local_solution)
        if not added:
            msg = "Couldn't add cloud solution to local model"
            raise ModelError(msg)

    def write(self, filename: str) -> None:
        """Writes the model to a file in the format specified by the filename suffix.

        Args:
            filename (str): The name of the file to be written.
        """
        self._model.writeProblem(filename, verbose=False)
        raw_filename = filename + ".raw"
        os.rename(filename, raw_filename)
        # Remove comment lines starting with '*' or '\\' from the captured output
        with open(raw_filename) as input_file, open(filename, "w") as output_file:
            output_file.writelines(line for line in input_file if not line.startswith(("*", "\\")))
        os.remove(raw_filename)

    def _optimize(self) -> HybridSolverStatus:
        """Optimizes the model using the HybridSolver.

        Returns:
            HybridSolverStatus: The solution status after optimization.

        Raises:
            ModelError: If the problem cannot be written to a file or if the solution
            status cannot be cast to HybridSolverStatus.
        """
        # using the context manager to ensure the tmp_path is deleted even if an error occurs
        with tempfile.TemporaryDirectory() as tmp_path:
            # the https client is taking care of gzipping before sending the file, so no gzipping here
            tmp_problem = os.path.join(tmp_path, self._model.getProbName() + ".mps")
            try:
                self.write(tmp_problem)
                res, _ = self._hybrid_solver.solve(tmp_problem, params=self._parameters)
            except ValueError as e:
                msg = "Failed to submit the problem to the HybridSolver"
                raise ModelError(msg) from e

        # assign the solution to the local model
        self._solution = res["solution"]
        # assign the solution to the _model; disabled for now
        # self._assign_solution(self._solution)  # noqa: ERA001

        self._best_objective = res["objective"]
        self._best_bound = res["bound"]
        self._best_time = res["best_time"]
        self._total_time = res["timing"]

        # assign solution status
        try:
            self._sol_status = HybridSolverStatus(res["sol_status"])
        except ValueError as exc:
            msg = f"Couldn't cast solution status {res['sol_status']}"
            raise ValueError(msg) from exc

        return self._sol_status

    def optimize(self) -> HybridSolverStatus:
        """Sends the model to the HybridSolver and solves it on the cloud.

        Returns:
            HybridSolverStatus: The solution status after optimization.

        Raises:
            ValueError: If the solution status cannot be cast to HybridSolverStatus.
        """
        return self._optimize()

    def set_absolute_gap(self, gap: float) -> None:
        """Sets the absolute gap for the model.

        Args:
            gap (float): The absolute gap to be set.
        """
        self._parameters.set_absolute_gap(gap)

    def set_relative_gap(self, gap: float) -> None:
        """Sets the relative gap for the model.

        Args:
            gap (float): The relative gap to be set.
        """
        self._parameters.set_relative_gap(gap)

    def set_time_limit(self, time_limit: float) -> None:
        """Sets the time limit for the model.

        Args:
            time_limit (float): The time limit to be set.
        """
        self._parameters.set_time_limit(time_limit)

    def set_feasibility_tolerance(self, tolerance: float) -> None:
        """Sets the feasibility tolerance for the model.

        Args:
            tolerance (float): The feasibility tolerance to be set.
        """
        self._parameters.set_feasibility_tolerance(tolerance)

    def set_integrality_tolerance(self, tolerance: float) -> None:
        """Sets the integrality tolerance for the model.

        Args:
            tolerance (float): The integrality tolerance to be set.
        """
        self._parameters.set_integrality_tolerance(tolerance)

    def set_objective_limit(self, limit: float) -> None:
        """Sets the objective limit for the model.

        Args:
            limit (float): The objective limit to be set.
        """
        self._parameters.set_objective_limit(limit)

    def set_presolve(self, presolve: bool) -> None:
        """Sets the presolve flag for the model.

        Args:
            presolve (bool): The presolve flag to be set.
        """
        self._parameters.set_presolve(presolve)
