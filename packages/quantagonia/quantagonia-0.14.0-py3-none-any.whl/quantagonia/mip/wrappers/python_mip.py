from __future__ import annotations

import warnings

from pyscipopt import Expr as Expression

from quantagonia.errors.errors import ModelError
from quantagonia.mip.model import Model as BaseModel
from quantagonia.mip.variable import Variable as BaseVariable
from quantagonia.mip.wrappers.wrapper_enums import (
    PythonMipEnum,
    hybridsolver_sense_to_python_mip,
    hybridsolver_status_to_python_mip,
    hybridsolver_variable_type_to_python_mip,
)
from quantagonia.mip.wrappers.wrapper_enums import PythonMipStatus as OptimizationStatus


class Var(BaseVariable):
    """Wrapper for a Python-MIP variable."""

    def __init__(self, variable: BaseVariable) -> None:
        super().__init__(variable._variable, variable._model)  # noqa: SLF001

    @property
    def var_type(self) -> PythonMipEnum:
        """The type of the variable.

        This property allows getting and setting the type of the variable.

        Returns:
            PythonMipEnum: The type of the variable (PythonMipEnum.BINARY,
            PythonMipEnum.INTEGER, or PythonMipEnum.CONTINUOUS).

        Raises:
            ModelError: If the variable type is unsupported or if setting the type
            fails or if the variable data are not set.
        """
        variable_type = super().var_type
        return hybridsolver_variable_type_to_python_mip[variable_type]

    @var_type.setter
    def var_type(self, value: PythonMipEnum) -> None:
        """Set the type of the variable."""
        if self._model is None:
            msg = "Model is not set."
            raise ModelError(msg)
        # Set the var_type of the parent class
        super(BaseVariable, self.__class__).var_type.fset(self, value.value)


class Model(BaseModel):
    def __init__(
        self,
        name: str = "Model",
        sense: PythonMipEnum | None = None,
    ) -> None:
        super().__init__(name)
        if sense is not None:
            self.sense = sense

    @property
    def sense(self) -> PythonMipEnum:
        """The optimization sense of the model.

        Returns:
            PythonMipEnum: The optimization sense of the model.
        """
        return hybridsolver_sense_to_python_mip[super().sense]

    @sense.setter
    def sense(self, sense: PythonMipEnum) -> None:
        """The optimization sense of the model.

        Args:
            sense (PythonMipEnum): The optimization sense to be set.

        Raises:
            ModelError: If the provided sense is unsupported.
        """
        if sense not in [PythonMipEnum.MINIMIZE, PythonMipEnum.MAXIMIZE]:
            error_message = "Unsupported sense."
            raise ModelError(error_message)
        super(Model, self.__class__).sense.fset(self, sense.value)

    @property
    def objective(self) -> tuple[Expression, PythonMipEnum]:
        """The objective function of the model.

        Returns:
            tuple[Expression, HybridSolverOptSenses]: A tuple containing the objective expression and sense.
        """
        return self._objective_function, hybridsolver_sense_to_python_mip[self.sense]

    @objective.setter
    def objective(self, obj_info: Expression | tuple[Expression, PythonMipEnum]) -> None:
        """Sets the objective function of the model.

        Args:
            obj_info (Expression | Tuple[Expression, PythonMipEnum]): The objective function to be set.
        """
        if isinstance(obj_info, Expression):
            expr = obj_info
            sense = self.sense
        elif isinstance(obj_info, tuple):
            expr, sense = obj_info
        else:
            error_message = "Unsupported objective information."
            raise ModelError(error_message)
        self.set_objective(expr, sense.value)

    @property
    def status(self) -> OptimizationStatus:
        """The solution status of the model.

        Returns:
            HybridSolverStatus: The current solution status of the model.
        """
        return hybridsolver_status_to_python_mip[self.solution_status]

    @property
    def num_solutions(self) -> int:
        """The number of solutions found during optimization.

        Returns:
            int: The number of solutions found during the MIP search.
        """
        return 1 if self._solution is not None else 0

    @property
    def objective_const(self) -> float:
        """The offset of the objective function.

        Returns:
            float: The constant offset value of the objective function.
        """
        return self.objective_offset

    @property
    def num_cols(self) -> int:
        """The number of variables in the model.

        Returns:
            int: The number of variables in the model.
        """
        return self.n_vars

    @property
    def num_int(self) -> int:
        """The number of integer variables in the model.

        Returns:
            int: The number of integer variables in the model.
        """
        return self.n_int_vars

    @property
    def vars(self) -> list[Var]:
        """The list of variables in the model.

        Returns:
            list[Variable]: A list of Variable instances in the model.
        """
        return self.get_variables()

    @property
    def max_mip_gap(self) -> float:
        """The maximum MIP gap for the model.

        Returns:
            float: The maximum MIP gap for the model.
        """
        if "relative_gap" not in self.parameters:
            return None
        return self.parameters["relative_gap"]

    @max_mip_gap.setter
    def max_mip_gap(self, gap: float) -> None:
        """The maximum relative MIP gap for the model.

        Args:
            gap (float): The maximum MIP gap to be set.
        """
        self.set_relative_gap(gap)

    @property
    def max_mip_gap_abs(self) -> float:
        """The maximum absolute MIP gap for the model.

        Returns:
            float: The maximum absolute MIP gap for the model.
        """
        if "absolute_gap" not in self.parameters:
            return None
        return self.parameters["absolute_gap"]

    @max_mip_gap_abs.setter
    def max_mip_gap_abs(self, gap: float) -> None:
        """The maximum absolute MIP gap for the model.

        Args:
            gap (float): The maximum absolute MIP gap to be set.
        """
        self.set_absolute_gap(gap)

    @property
    def infeas_tol(self) -> float:
        """The feasibility tolerance for the model.

        Returns:
            float: The feasibility tolerance for the model.
        """
        # check if "feasibility_tolerance" is a valid key in the parameters dictionary
        if "feasibility_tolerance" not in self.parameters:
            return None
        return self.parameters["feasibility_tolerance"]

    @infeas_tol.setter
    def infeas_tol(self, tol: float) -> None:
        """The feasibility tolerance for the model.

        Args:
            tol (float): The feasibility tolerance to be set.
        """
        self.set_feasibility_tolerance(tol)

    @property
    def integer_tol(self) -> float:
        """The integer tolerance for the model.

        Returns:
            float: The integer tolerance for the model.
        """
        if "integrality_tolerance" not in self.parameters:
            return None
        return self.parameters["integrality_tolerance"]

    @integer_tol.setter
    def integer_tol(self, tol: float) -> None:
        """The integer tolerance for the model.

        Args:
            tol (float): The integer tolerance to be set.
        """
        self.set_integrality_tolerance(tol)

    @property
    def max_seconds(self) -> float:
        """The maximum time limit for the model.

        Returns:
            float: The maximum time limit for the model.
        """
        if "time_limit" not in self.parameters:
            return None
        return self.parameters["time_limit"]

    @max_seconds.setter
    def max_seconds(self, seconds: float) -> None:
        """The maximum time limit for the model.

        Args:
            seconds (float): The maximum time limit to be set.
        """
        self.set_time_limit(seconds)

    def add_var(
        self,
        name: str = "",
        lb: float = 0,
        ub: float = float("Inf"),
        obj: float = 0,
        var_type: PythonMipEnum = PythonMipEnum.CONTINUOUS,
        column: int | None = None,
    ) -> Var:
        """Adds a new variable to the model.

        Args:
            lb (float): The lower bound of the variable. Defaults to 0.
            ub (float): The upper bound of the variable. Defaults to positive infinity.
            obj (float): The coefficient of the variable in the objective function. Defaults to 0.
            name (str): The name of the variable. Defaults to an empty string.
            var_type (PythonMipEnum): The type of the variable. Defaults to PythonMipEnum.CONTINUOUS.
            column (int): (optional) Not supported. Defaults to None.

        Returns:
            Variable: The Variable instance that was added to the MIP model.

        Raises:
            ModelError: If the variable type is unsupported or if the variable addition fails.
        """
        if column is not None:
            msg = "Input variable `column` is not supported in `add_var` method."
            warnings.warn(msg, stacklevel=2)
        return Var(self.add_variable(lb, ub, name, obj, var_type.value))

    def var_by_name(self, name: str) -> Var:
        """Returns the variable with the given name.

        Args:
            name (str): The name of the variable to be retrieved.

        Returns:
            Returns a variable if it finds one with exactly this name, or None.
        """
        var = None
        for var_ in self._model.getVars():
            if var_.name == name:
                var = Var(BaseVariable(var_, self))
                break
        return var

    def add_constr(self, lin_expr: Expression, name: str = "", priority: int | None = None) -> None:
        """Adds a constraint to the model.

        Args:
            lin_expr (Expression): The expression representing the constraint.
            name (str): (optional) The name of the constraint.
            priority (int): (optional) The priority of the constraint. Not supported.

        Raises:
            ModelError: If the constraint addition fails.
        """
        if priority is not None:
            msg = "Input variable `priority` is not supported in `add_constr` method."
            warnings.warn(msg, stacklevel=2)
        self.add_constraint(lin_expr, name)

    def optimize(self) -> OptimizationStatus:
        """Sends the model to the HybridSolver and solves it on the cloud.

        Returns:
            OptimizationStatus: The solution status after optimization.

        Raises:
            ValueError: If the solution status cannot be cast to HybridSolverStatus.
        """
        return hybridsolver_status_to_python_mip[self._optimize()]

    def __iadd__(self, constraint: Expression) -> Model:  # noqa: PYI034
        """Adds a constraint to the model using the += operator."""
        self.add_constraint(constraint)
        return self


def minimize(objective: Expression) -> tuple[Expression, PythonMipEnum]:
    """Minimize the objective function.

    Args:
        objective (Expression): The objective function to minimize.

    Returns:
        tuple[Expression, PythonMipEnum]: The objective function and the optimization sense.
    """
    return objective, PythonMipEnum.MINIMIZE


def maximize(objective: Expression) -> tuple[Expression, PythonMipEnum]:
    """Maximize the objective function.

    Args:
        objective (Expression): The objective function to maximize.

    Returns:
        tuple[Expression, HybridSolverOptSenses | GRB | CplexSenses | str]: The objective
        function and the optimization sense.
    """
    return objective, PythonMipEnum.MAXIMIZE


def xsum(terms: list[Expression]) -> Expression:
    """Sum of a list of expressions.

    Args:
        terms (list[Expression]): The list of expressions to sum.

    Returns:
        Expression: The sum of the expressions.
    """
    final_expr = 1 * terms[0]
    for expr in terms[1:]:
        final_expr = final_expr + 1 * expr
    return final_expr
