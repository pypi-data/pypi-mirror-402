from __future__ import annotations

import warnings
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pyscipopt import Expr as Expression

from quantagonia.enums import HybridSolverOptSenses, HybridSolverStatus
from quantagonia.errors.errors import ModelError
from quantagonia.mip.model import Model as BaseModel
from quantagonia.mip.variable import Variable as BaseVariable
from quantagonia.mip.wrappers.wrapper_enums import (
    CplexEnum,
    hybridsolver_sense_to_cplex_enum,
    hybridsolver_status_to_cplex_enum,
    hybridsolver_variable_type_to_cplex_enum,
)


class Variable(BaseVariable):
    """Wrapper for a CPLEX variable."""

    def __init__(self, variable: Variable) -> None:
        super().__init__(variable._variable, variable._model)  # noqa: SLF001

    @property
    def var_type(self) -> CplexEnum:
        """The type of the variable.

        This property allows getting and setting the type of the variable.

        Returns:
            CplexEnum: The type of the variable (CplexEnum.BINARY, CplexEnum.INTEGER, or CplexEnum.CONTINUOUS).

        Raises:
            ModelError: If the variable type is unsupported or if setting the type
            fails or if the variable data are not set.
        """
        variable_type = super().var_type
        return hybridsolver_variable_type_to_cplex_enum[variable_type]

    @var_type.setter
    def var_type(self, value: CplexEnum) -> None:
        """Set the type of the variable."""
        if self._model is None:
            msg = "Model is not set."
            raise ModelError(msg)
        # Set the var_type of the parent class
        super(Variable, self.__class__).var_type.fset(self, value.value)


class Parameter:
    """A descriptor for individual parameters."""

    def __init__(self) -> None:
        self.value = None  # Default value is None

    def set(self, value) -> None:  # noqa: ANN001
        """Sets the value of the parameter."""
        self.value = value

    def get(self):  # noqa: ANN201
        """Gets the value of the parameter."""
        return self.value


class Model(BaseModel):
    """Wrapper for a CPLEX model."""

    class Parameters:
        """A class for storing the parameters of the model."""

        class Mip:
            """A class for storing the MIP parameters of the model."""

            class Tolerances:
                """A class for storing the tolerances of the MIP parameters."""

                def __init__(self):
                    self.absmipgap = Parameter()
                    self.integrality = Parameter()
                    self.mipgap = Parameter()

            class Limits:
                """A class for storing the limits of the MIP parameters."""

                def __init__(self):
                    self.lowerobjstop = Parameter()

            def __init__(self):
                self.tolerances = Model.Parameters.Mip.Tolerances()
                self.limits = Model.Parameters.Mip.Limits()

        class Feasopt:
            """A class for storing the Feasopt parameters of the model."""

            def __init__(self):
                self.tolerance = Parameter()

        class Preprocessing:
            """A class for storing the preprocessing parameters of the model."""

            def __init__(self):
                self.presolve = Parameter()

        class Simplex:
            """A class for storing the simplex parameters of the model."""

            class Tolerances:
                """A class for storing the tolerances of the simplex parameters."""

                def __init__(self):
                    self.feasibility = Parameter()

            def __init__(self):
                self.tolerances = Model.Parameters.Simplex.Tolerances()

        def __init__(self):
            self.mip = Model.Parameters.Mip()
            self.feasopt = Model.Parameters.Feasopt()
            self.preprocessing = Model.Parameters.Preprocessing()
            self.simplex = Model.Parameters.Simplex()
            self.timelimit = Parameter()

    def __init__(self, name: str = "Model") -> None:
        super().__init__(name)
        self._params = Model.Parameters()

    @property
    def parameters(self) -> Model.Parameters:
        """The parameters of the model."""
        return self._params

    @property
    def objective_sense(self) -> CplexEnum:
        """The optimization sense of the model.

        Returns:
            HybridSolverOptSenses: The current optimization sense of the model.

        Raises:
            ModelError: If the current sense is unsupported.
        """
        return hybridsolver_sense_to_cplex_enum[self.sense]

    @objective_sense.setter
    def objective_sense(self, sense: CplexEnum) -> None:
        """Sets the optimization sense of the model.

        Args:
            sense (CplexEnum): The optimization sense to be set.

        Raises:
            ModelError: If the provided sense is unsupported.
        """
        self.sense = sense.value

    @property
    def number_of_variables(self) -> int:
        """The number of variables in the model.

        Returns:
            int: The number of variables in the model.
        """
        return self.n_vars

    @property
    def number_of_binary_variables(self) -> int:
        """The number of binary variables in the model.

        Returns:
            int: The number of binary variables in the model.
        """
        return self.n_bin_vars

    @property
    def number_of_integer_variables(self) -> int:
        """The number of integer variables in the model.

        Returns:
            int: The number of integer variables in the model.
        """
        return self.n_int_vars

    @property
    def number_of_continuous_variables(self) -> int:
        """The number of continuous variables in the model.

        Returns:
            int: The number of continuous variables in the model.
        """
        return self.n_cont_vars

    @property
    def binary_vartype(self) -> CplexEnum:
        """Returns the binary variable type.

        Returns:
            CplexEnum: The binary variable type.
        """
        return CplexEnum.BINARY

    @property
    def continuous_vartype(self) -> CplexEnum:
        """Returns the continuous variable type.

        Returns:
            CplexEnum: The continuous variable type.
        """
        return CplexEnum.CONTINUOUS

    @property
    def integer_vartype(self) -> CplexEnum:
        """Returns the integer variable type.

        Returns:
            CplexEnum: The integer variable type.
        """
        return CplexEnum.INTEGER

    @property
    def problem_type(self) -> str:
        """The type of the problem.

        Returns:
            str: The type of the problem.
        """
        return "MILP"

    @property
    def infinity(self) -> float:
        """The positive infinity value.

        Returns:
            float: The positive infinity value.
        """
        return float("Inf")

    def continuous_var(self, lb: float = 0, ub: float = float("Inf"), name: str = "", coeff: float = 0) -> Variable:
        """Adds a new continuous variable to the model.

        Args:
            lb (float): The lower bound of the variable. Defaults to 0.
            ub (float): The upper bound of the variable. Defaults to positive infinity.
            name (str): The name of the variable. Defaults to an empty string.
            coeff (float): The coefficient of the variable in the objective function. Defaults to 0.

        Returns:
            Variable: The Variable instance that was added to the MIP model.

        Raises:
            ModelError: If the variable addition fails.
        """
        return Variable(self.add_variable(lb, ub, name, coeff, CplexEnum.CONTINUOUS.value))

    def integer_var(self, lb: float = 0, ub: float = float("Inf"), name: str = "", coeff: float = 0) -> Variable:
        """Adds a new integer variable to the model.

        Args:
            lb (float): The lower bound of the variable. Defaults to 0.
            ub (float): The upper bound of the variable. Defaults to positive infinity.
            name (str): The name of the variable. Defaults to an empty string.
            coeff (float): The coefficient of the variable in the objective function. Defaults to 0.

        Returns:
            Variable: The Variable instance that was added to the MIP model.

        Raises:
            ModelError: If the variable addition fails.
        """
        return Variable(self.add_variable(lb, ub, name, coeff, CplexEnum.INTEGER.value))

    def binary_var(self, name: str = "", coeff: float = 0) -> Variable:
        """Adds a new binary variable to the model.

        Args:
            name (str): The name of the variable. Defaults to an empty string.
            coeff (float): The coefficient of the variable in the objective function. Defaults to 0.

        Returns:
            Variable: The Variable instance that was added to the MIP model.

        Raises:
            ModelError: If the variable addition fails.
        """
        return Variable(self.add_variable(0, 1, name, coeff, CplexEnum.BINARY.value))

    def binary_var_dict(
        self,
        keys: list | tuple | range | int,
        name: str | None = None,
        key_format: str | None = None,
    ) -> dict[str, Variable]:
        """Creates a dictionary of binary decision variables, indexed by key objects.

        Args:
            keys: Either a sequence of objects, an iterator, or a positive integer. If passed an integer,
                  it is interpreted as the number of variables to create.
            name (str): A string used to name variables. The variable name is formed by appending the
                        string to the string representation of the key object. Defaults to None.
            key_format (str): A format string or None. This format string describes how keys
                              contribute to variable names. The default is “_%s”. For example if
                              name is “x” and each key object is represented by a string
                              like “k1”, “k2”, … then variables will be named “x_k1”, “x_k2”,…

        Returns:
            dict[str, Variable]: A dictionary of binary decision variables indexed by key objects.
        """
        if key_format is None:
            key_format = "_%s"
        if name is None:
            name = ""
        binary_vars = {}
        if isinstance(keys, int):
            keys = range(keys)
        for _, key in enumerate(keys):
            var_name = f"{name}{key_format % key}"
            binary_vars[var_name] = Variable(self.binary_var(var_name))
        return binary_vars

    def binary_var_list(
        self,
        keys: list | tuple | range | int,
        name: str | None = None,
        key_format: str | None = None,
    ) -> list[Variable]:
        """Creates a list of binary decision variables, indexed by key objects.

        Args:
            keys: Either a sequence of objects, an iterator, or a positive integer. If passed an integer,
                  it is interpreted as the number of variables to create.
            name (str): A string used to name variables. The variable name is formed by appending the
                        string to the string representation of the key object. Defaults to None.
            key_format (str): A format string or None. This format string describes how keys
                              contribute to variable names. The default is “_%s”. For example if
                              name is “x” and each key object is represented by a string
                              like “k1”, “k2”, … then variables will be named “x_k1”, “x_k2”,…

        Returns:
            list[Variable]: A list of binary decision variables indexed by key objects.
        """
        return list(self.binary_var_dict(keys, name, key_format).values())

    def continuous_var_dict(
        self,
        keys: list | tuple | range | int,
        lb: float | list[float] | None = None,
        ub: float | list[float] | None = None,
        name: str | None = None,
        key_format: str | None = None,
    ) -> dict[str, Variable]:
        """Creates a dictionary of continuous decision variables, indexed by key objects.

        Args:
            keys: Either a sequence of objects, an iterator, or a positive integer. If passed an integer,
                  it is interpreted as the number of variables to create.
            lb (float): The lower bound of the variables. Defaults to None.
            ub (float): The upper bound of the variables. Defaults to None.
            name (str): A string used to name variables. The variable name is formed by appending the
                        string to the string representation of the key object. Defaults to None.
            key_format (str): A format string or None. This format string describes how keys
                              contribute to variable names. The default is “_%s”. For example if
                              name is “x” and each key object is represented by a string
                              like “k1”, “k2”, … then variables will be named “x_k1”, “x_k2”,…

        Returns:
            dict[str, Variable]: A dictionary of continuous decision variables indexed by key objects.
        """
        if key_format is None:
            key_format = "_%s"
        if name is None:
            name = ""
        continuous_vars = {}
        if isinstance(keys, int):
            keys = range(keys)
        if isinstance(lb, float):
            lb = [lb] * len(keys)
        if isinstance(ub, float):
            ub = [ub] * len(keys)
        for i, key in enumerate(keys):
            var_name = f"{name}{key_format % key}"
            continuous_vars[var_name] = Variable(self.continuous_var(lb[i], ub[i], var_name))
        return continuous_vars

    def continuous_var_list(
        self,
        keys: list | tuple | range | int,
        lb: float | list[float] | None = None,
        ub: float | list[float] | None = None,
        name: str | None = None,
        key_format: str | None = None,
    ) -> list[Variable]:
        """Creates a list of continuous decision variables, indexed by key objects.

        Args:
            keys: Either a sequence of objects, an iterator, or a positive integer. If passed an integer,
                  it is interpreted as the number of variables to create.
            lb (float): The lower bound of the variables. Defaults to None.
            ub (float): The upper bound of the variables. Defaults to None.
            name (str): A string used to name variables. The variable name is formed by appending the
                        string to the string representation of the key object. Defaults to None.
            key_format (str): A format string or None. This format string describes how keys
                              contribute to variable names. The default is “_%s”. For example if
                              name is “x” and each key object is represented by a string
                              like “k1”, “k2”, … then variables will be named “x_k1”, “x_k2”,…

        Returns:
            list[Variable]: A list of continuous decision variables indexed by key objects.
        """
        return list(self.continuous_var_dict(keys, lb, ub, name, key_format).values())

    def integer_var_dict(
        self,
        keys: list | tuple | range | int,
        lb: float | list[float] | None = None,
        ub: float | list[float] | None = None,
        name: str | None = None,
        key_format: str | None = None,
    ) -> dict[str, Variable]:
        """Creates a dictionary of integer decision variables, indexed by key objects.

        Args:
            keys: Either a sequence of objects, an iterator, or a positive integer. If passed an integer,
                  it is interpreted as the number of variables to create.
            lb (float): The lower bound of the variables. Defaults to None.
            ub (float): The upper bound of the variables. Defaults to None.
            name (str): A string used to name variables. The variable name is formed by appending the
                        string to the string representation of the key object. Defaults to None.
            key_format (str): A format string or None. This format string describes how keys
                              contribute to variable names. The default is “_%s”. For example if
                              name is “x” and each key object is represented by a string
                              like “k1”, “k2”, … then variables will be named “x_k1”, “x_k2”,…

        Returns:
            dict[str, Variable]: A dictionary of integer decision variables indexed by key objects.
        """
        if key_format is None:
            key_format = "_%s"
        if name is None:
            name = ""
        integer_vars = {}
        if isinstance(keys, int):
            keys = range(keys)
        if isinstance(lb, float):
            lb = [lb] * len(keys)
        if isinstance(ub, float):
            ub = [ub] * len(keys)
        for i, key in enumerate(keys):
            var_name = f"{name}{key_format % key}"
            integer_vars[var_name] = Variable(self.integer_var(lb[i], ub[i], var_name))
        return integer_vars

    def integer_var_list(
        self,
        keys: list | tuple | range | int,
        lb: float | list[float] | None = None,
        ub: float | list[float] | None = None,
        name: str | None = None,
        key_format: str | None = None,
    ) -> list[Variable]:
        """Creates a list of integer decision variables, indexed by key objects.

        Args:
            keys: Either a sequence of objects, an iterator, or a positive integer. If passed an integer,
                  it is interpreted as the number of variables to create.
            lb (float): The lower bound of the variables. Defaults to None.
            ub (float): The upper bound of the variables. Defaults to None.
            name (str): A string used to name variables. The variable name is formed by appending the
                        string to the string representation of the key object. Defaults to None.
            key_format (str): A format string or None. This format string describes how keys
                              contribute to variable names. The default is “_%s”. For example if
                              name is “x” and each key object is represented by a string
                              like “k1”, “k2”, … then variables will be named “x_k1”, “x_k2”,…

        Returns:
            list[Variable]: A list of integer decision variables indexed by key objects.
        """
        return list(self.integer_var_dict(keys, lb, ub, name, key_format).values())

    def change_var_upper_bounds(
        self, dvars: list[Variable], ubs: float | list[float] | None, check_bounds: bool = True
    ) -> None:
        """Changes the upper bounds of variables.

        Args:
            dvars (list[Variable]): A list of variables to change the upper
            ubs (float | list[float] | None): The new upper bounds for the variables.
            check_bounds (bool): If True, the function checks that the new upper bounds are valid.
        """
        if isinstance(ubs, float):
            ubs = [ubs] * len(dvars)
        for i, var in enumerate(dvars):
            if check_bounds and ubs[i] < var.lb:
                error_message = "Upper bound cannot be less than lower bound."
                raise ModelError(error_message)
            var.ub = ubs[i]

    def change_var_lower_bounds(
        self, dvars: list[Variable], lbs: float | list[float] | None, check_bounds: bool = True
    ) -> None:
        """Changes the lower bounds of variables.

        Args:
            dvars (list[Variable]): A list of variables to change the lower
            lbs (float | list[float] | None): The new lower bounds for the variables.
            check_bounds (bool): If True, the function checks that the new lower bounds are valid.
        """
        if isinstance(lbs, float):
            lbs = [lbs] * len(dvars)
        for i, var in enumerate(dvars):
            if check_bounds and lbs[i] > var.ub:
                error_message = "Lower bound cannot be greater than upper bound."
                raise ModelError(error_message)
            var.lb = lbs[i]

    def objective_coef(self, var: Variable) -> float:
        """Returns the coefficient of a variable in the objective function.

        Args:
            var (Variable): The variable whose coefficient is to be retrieved.

        Returns:
            float: The coefficient of the variable in the objective function.
        """
        return var.obj

    def get_var_by_name(self, name: str) -> Variable:
        """Returns the variable with the given name.

        Args:
            name (str): The name of the variable to be retrieved.

        Returns:
            Returns a variable if it finds one with exactly this name, or None.
        """
        var = None
        for var_ in self._model.getVars():
            if var_.name == name:
                var = Variable(BaseVariable(var_, self))
                break
        return var

    def add_constraint_(self, expr: Expression, name: str = "") -> None:
        """Adds a constraint to the model.

        Args:
            expr (Expression): The expression representing the constraint.
            name (str): (optional) The name of the constraint.

        Raises:
            ModelError: If the constraint addition fails.
        """
        self.add_constraint(expr, name)

    def linear_constraint(self, lhs: Expression, ctsense: str, rhs: float, name: str = "") -> None:
        """Adds a linear constraint to the model.

        Args:
            lhs (Expression): The left-hand side of the constraint.
            ctsense (str): The sense of the constraint (e.g., "<=", "==", or ">=").
            rhs (float): The right-hand side of the constraint.
            name (str): (optional) The name of the constraint.

        Raises:
            ModelError: If the constraint addition fails.
        """
        if ctsense in ["<=", "le"]:
            final_expr = lhs <= rhs
        elif ctsense in ["==", "eq"]:
            final_expr = lhs == rhs
        elif ctsense in [">=", "ge"]:
            final_expr = lhs >= rhs
        else:
            error_message = "Unsupported sense."
            raise ModelError(error_message)
        self.add_constraint(final_expr, name)

    def eq_constraint(self, lhs: Expression, rhs: float, name: str = "") -> None:
        """Adds an equality constraint to the model.

        Args:
            lhs (Expression): The left-hand side of the constraint.
            rhs (float): The right-hand side of the constraint.
            name (str): (optional) The name of the constraint.

        Raises:
            ModelError: If the constraint addition fails.
        """
        self.linear_constraint(lhs, "==", rhs, name)

    def le_constraint(self, lhs: Expression, rhs: float, name: str = "") -> None:
        """Adds a less-than-or-equal constraint to the model.

        Args:
            lhs (Expression): The left-hand side of the constraint.
            rhs (float): The right-hand side of the constraint.
            name (str): (optional) The name of the constraint.

        Raises:
            ModelError: If the constraint addition fails.
        """
        self.linear_constraint(lhs, "<=", rhs, name)

    def ge_constraint(self, lhs: Expression, rhs: float, name: str = "") -> None:
        """Adds a greater-than-or-equal constraint to the model.

        Args:
            lhs (Expression): The left-hand side of the constraint.
            rhs (float): The right-hand side of the constraint.
            name (str): (optional) The name of the constraint.

        Raises:
            ModelError: If the constraint addition fails.
        """
        self.linear_constraint(lhs, ">=", rhs, name)

    def is_maximized(self) -> bool:
        """Checks if the model is maximized.

        Returns:
            bool: True if the model is maximized, False otherwise.
        """
        return self.sense == HybridSolverOptSenses.MAXIMIZE

    def is_minimized(self) -> bool:
        """Checks if the model is minimized.

        Returns:
            bool: True if the model is minimized, False otherwise.
        """
        return self.sense == HybridSolverOptSenses.MINIMIZE

    def solve(self, log_output: bool = False) -> CplexEnum:
        """Solves the model.

        Returns:
            HybridSolverStatus: The solution status after optimization.
        """
        if log_output:
            msg = "The log output mode is not available in the CPLEX wrapper."
            warnings.warn(msg, stacklevel=2)
        return self.optimize()

    def set_objective(self, expr: Expression, sense: CplexEnum = CplexEnum.Minimize) -> None:
        """Sets the objective function for the model.

        Args:
            expr (Expression): The expression representing the objective function.
            sense (CplexEnum): The optimization sense (minimize or maximize).
                Defaults to CplexEnum.Minimize.

        Raises:
            ModelError: If the sense is unsupported or if setting the objective fails.
        """
        super().set_objective(expr, sense.value)

    def minimize(self, expr: Expression) -> CplexEnum:
        """Solves the model by minimizing the objective function.

        Args:
            expr (Expression): The expression representing the objective function.

        Returns:
            HybridSolverStatus: The solution status after optimization.
        """
        super().set_objective(expr, HybridSolverOptSenses.MINIMIZE)
        return self.optimize()

    def maximize(self, expr: Expression) -> CplexEnum:
        """Solves the model by maximizing the objective function.

        Args:
            expr (Expression): The expression representing the objective function.

        Returns:
            HybridSolverStatus: The solution status after optimization.
        """
        super().set_objective(expr, HybridSolverOptSenses.MAXIMIZE)
        return self.optimize()

    def get_solve_status(self) -> CplexEnum:
        """Returns the solution status after optimization.

        Returns:
            HybridSolverStatus: The solution status after optimization.
        """
        return hybridsolver_status_to_cplex_enum[self._sol_status]

    def sum(self, args: list[Expression]) -> Expression:
        """Sum of a list of expressions.

        Args:
            args (list[Expression]): The list of expressions to sum.

        Returns:
            Expression: The sum of the expressions.
        """
        final_expr = 1 * args[0]
        for expr in args[1:]:
            final_expr = final_expr + 1 * expr
        return final_expr

    def sum_vars(self, dvars: list[Variable]) -> Expression:
        """Creates a linear expression that sums variables.

        Args:
            dvars (list[Variable]): The list of variables to sum.

        Returns:
            Expression: The linear expression that sums the variables.
        """
        return sum([1 * var for var in dvars])

    def _set_parameters(self) -> None:
        """Sets the parameters of the model."""

        # get all parameters from the parameters object
        def _get_param_recursive(
            obj: Model.Parameters | Parameter, prefix: str | None = None
        ) -> dict[str, float | bool | int]:
            params = {}
            for name, param in vars(obj).items():
                full_name = f"{prefix}.{name}" if prefix is not None else name
                if isinstance(param, Parameter):
                    value = param.get()
                    if value is not None:
                        params[full_name] = value
                else:
                    params.update(_get_param_recursive(param, prefix=full_name))
            return params

        for name, value in _get_param_recursive(self._params).items():
            if name == "mip.tolerances.mipgap":
                self.set_relative_gap(value)
            elif name == "mip.tolerances.integrality":
                self.set_integrality_tolerance(value)
            elif name == "mip.tolerances.absmipgap":
                self.set_absolute_gap(value)
            elif name == "mip.limits.lowerobjstop":
                self.set_objective_limit(value)
            elif name in ["feasopt.tolerance", "simplex.tolerances.feasibility"]:
                self.set_feasibility_tolerance(value)
            elif name == "timelimit":
                self.set_time_limit(value)
            elif name == "preprocessing.presolve":
                if self._params.preprocessing.presolve.get() == 0:
                    self.set_presolve(False)
                else:
                    self.set_presolve(True)
            else:
                msg = f"Unsupported parameter: {name}"
                raise ModelError(msg)

    def optimize(self) -> CplexEnum:
        """Sends the model to the HybridSolver and solves it on the cloud.

        Returns:
            CplexEnum: The solution status after optimization.

        Raises:
            ValueError: If the solution status cannot be cast to HybridSolverStatus.
        """
        self._set_parameters()
        return hybridsolver_status_to_cplex_enum[self._optimize()]

    def print_solution(self) -> None:
        """Prints the values of the model variables after a solve.

        Only valid after a successful solve. If the model has not been
        solved successfully, an exception is raised.
        """
        if self._sol_status != HybridSolverStatus.OPTIMAL:
            msg = "Model has not been successfully solved."
            raise ModelError(msg)
        for var in self.get_variables():
            print(f"{var.name}: {var.sol_value}")
