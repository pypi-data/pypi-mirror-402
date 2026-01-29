from enum import Enum

from quantagonia.enums import HybridSolverOptSenses, HybridSolverStatus, VarType


class GRB(Enum):
    """An enumeration class representing the types of variables and senses gurobi-like.

    Attributes:
    ----------
    CONTINUOUS : str
        Represents a continuous variable.
    INTEGER : str
        Represents an integer variable.
    BINARY : str
        Represents a binary variable.
    MAXIMIZE : str
        Represents maximization.
    MINIMIZE : str
        Represents minimization.
    OPTIMAL : str
        Represents optimal solution.
    OBJECTIVE_LIMIT_REACHED : str
        Represents objective limit reached.
    FEASIBLE : str
        Represents feasible solution.
    INFEASIBLE : str
        Represents infeasible solution.
    UNBOUNDED : str
        Represents unbounded objective function.
    INFEASIBLE_OR_UNBOUNDED : str
        Represents infeasible or unbounded problem.
    UNSUITABLE : str
        Represents unsuitable problem.
    TIMELIMIT : str
        Represents time limit reached.
    ABORTED : str
        Represents aborted run.
    NUMERICAL_ERROR : str
        Represents numerical error occured.
    READERROR : str
        Represents read error.
    TERMINATED : str
        Represents terminated run.
    FAILED : str
        Represents failed run.
    COMPLETE : str
        Represents complete run.
    UNKNOWN : str
        Represents unknown status.
    """

    CONTINUOUS = VarType.CONTINUOUS
    INTEGER = VarType.INTEGER
    BINARY = VarType.BINARY

    MAXIMIZE = HybridSolverOptSenses.MAXIMIZE
    MINIMIZE = HybridSolverOptSenses.MINIMIZE

    OPTIMAL = HybridSolverStatus.OPTIMAL
    OBJECTIVE_LIMIT_REACHED = HybridSolverStatus.OBJECTIVE_LIMIT_REACHED
    FEASIBLE = HybridSolverStatus.FEASIBLE
    INFEASIBLE = HybridSolverStatus.INFEASIBLE
    UNBOUNDED = HybridSolverStatus.UNBOUNDED
    INFEASIBLE_OR_UNBOUNDED = HybridSolverStatus.INFEASIBLE_OR_UNBOUNDED
    UNSUITABLE = HybridSolverStatus.UNSUITABLE
    TIMELIMIT = HybridSolverStatus.TIMELIMIT
    ABORTED = HybridSolverStatus.ABORTED
    NUMERICAL_ERROR = HybridSolverStatus.NUMERICAL_ERROR
    READERROR = HybridSolverStatus.READERROR
    TERMINATED = HybridSolverStatus.TERMINATED
    FAILED = HybridSolverStatus.FAILED
    COMPLETE = HybridSolverStatus.COMPLETE
    UNKNOWN = HybridSolverStatus.UNKNOWN


# dictionary that maps hybridsolver status to cplex status
hybridsolver_status_to_grb = {
    HybridSolverStatus.OPTIMAL: GRB.OPTIMAL,
    HybridSolverStatus.OBJECTIVE_LIMIT_REACHED: GRB.OBJECTIVE_LIMIT_REACHED,
    HybridSolverStatus.FEASIBLE: GRB.FEASIBLE,
    HybridSolverStatus.INFEASIBLE: GRB.INFEASIBLE,
    HybridSolverStatus.UNBOUNDED: GRB.UNBOUNDED,
    HybridSolverStatus.INFEASIBLE_OR_UNBOUNDED: GRB.INFEASIBLE_OR_UNBOUNDED,
    HybridSolverStatus.UNSUITABLE: GRB.UNSUITABLE,
    HybridSolverStatus.TIMELIMIT: GRB.TIMELIMIT,
    HybridSolverStatus.ABORTED: GRB.ABORTED,
    HybridSolverStatus.NUMERICAL_ERROR: GRB.NUMERICAL_ERROR,
    HybridSolverStatus.READERROR: GRB.READERROR,
    HybridSolverStatus.TERMINATED: GRB.TERMINATED,
    HybridSolverStatus.FAILED: GRB.FAILED,
    HybridSolverStatus.COMPLETE: GRB.COMPLETE,
    HybridSolverStatus.UNKNOWN: GRB.UNKNOWN,
}

# dictionary that maps the hybrisolver senses to cplex senses
hybridsolver_sense_to_grb = {HybridSolverOptSenses.MAXIMIZE: GRB.MAXIMIZE, HybridSolverOptSenses.MINIMIZE: GRB.MINIMIZE}

hybridsolver_variable_type_to_grb = {
    VarType.CONTINUOUS: GRB.CONTINUOUS,
    VarType.INTEGER: GRB.INTEGER,
    VarType.BINARY: GRB.BINARY,
}


class CplexEnum(Enum):
    """An enumeration class representing the types of variables and senses cplex-like.

    Attributes:
    ----------
    MAXIMIZE : str
        Represents maximization.
    MINIMIZE : str
        Represents minimization.
    """

    CONTINUOUS = VarType.CONTINUOUS
    INTEGER = VarType.INTEGER
    BINARY = VarType.BINARY

    Minimize = HybridSolverOptSenses.MINIMIZE
    Maximize = HybridSolverOptSenses.MAXIMIZE

    OPTIMAL = HybridSolverStatus.OPTIMAL
    OBJECTIVE_LIMIT_REACHED = HybridSolverStatus.OBJECTIVE_LIMIT_REACHED
    FEASIBLE = HybridSolverStatus.FEASIBLE
    INFEASIBLE = HybridSolverStatus.INFEASIBLE
    UNBOUNDED = HybridSolverStatus.UNBOUNDED
    INFEASIBLE_OR_UNBOUNDED = HybridSolverStatus.INFEASIBLE_OR_UNBOUNDED
    UNSUITABLE = HybridSolverStatus.UNSUITABLE
    TIMELIMIT = HybridSolverStatus.TIMELIMIT
    ABORTED = HybridSolverStatus.ABORTED
    NUMERICAL_ERROR = HybridSolverStatus.NUMERICAL_ERROR
    READERROR = HybridSolverStatus.READERROR
    TERMINATED = HybridSolverStatus.TERMINATED
    FAILED = HybridSolverStatus.FAILED
    COMPLETE = HybridSolverStatus.COMPLETE
    UNKNOWN = HybridSolverStatus.UNKNOWN


# dictionary that maps hybridsolver status to cplex status
hybridsolver_status_to_cplex_enum = {
    HybridSolverStatus.OPTIMAL: CplexEnum.OPTIMAL,
    HybridSolverStatus.OBJECTIVE_LIMIT_REACHED: CplexEnum.OBJECTIVE_LIMIT_REACHED,
    HybridSolverStatus.FEASIBLE: CplexEnum.FEASIBLE,
    HybridSolverStatus.INFEASIBLE: CplexEnum.INFEASIBLE,
    HybridSolverStatus.UNBOUNDED: CplexEnum.UNBOUNDED,
    HybridSolverStatus.INFEASIBLE_OR_UNBOUNDED: CplexEnum.INFEASIBLE_OR_UNBOUNDED,
    HybridSolverStatus.UNSUITABLE: CplexEnum.UNSUITABLE,
    HybridSolverStatus.TIMELIMIT: CplexEnum.TIMELIMIT,
    HybridSolverStatus.ABORTED: CplexEnum.ABORTED,
    HybridSolverStatus.NUMERICAL_ERROR: CplexEnum.NUMERICAL_ERROR,
    HybridSolverStatus.READERROR: CplexEnum.READERROR,
    HybridSolverStatus.TERMINATED: CplexEnum.TERMINATED,
    HybridSolverStatus.FAILED: CplexEnum.FAILED,
    HybridSolverStatus.COMPLETE: CplexEnum.COMPLETE,
    HybridSolverStatus.UNKNOWN: CplexEnum.UNKNOWN,
}

# dictionary that maps the hybrisolver senses to cplex senses
hybridsolver_sense_to_cplex_enum = {
    HybridSolverOptSenses.MAXIMIZE: CplexEnum.Maximize,
    HybridSolverOptSenses.MINIMIZE: CplexEnum.Minimize,
}

hybridsolver_variable_type_to_cplex_enum = {
    VarType.CONTINUOUS: CplexEnum.CONTINUOUS,
    VarType.INTEGER: CplexEnum.INTEGER,
    VarType.BINARY: CplexEnum.BINARY,
}


class PythonMipEnum(Enum):
    """An enumeration class representing the optimization senses and variable classes for the hybrid solver.

    Attributes:
    ----------
        CONTINUOUS : str
            Represents a continuous variable.
        INTEGER : str
            Represents an integer variable.
        BINARY : str
            Represents a binary variable.
        MAXIMIZE : str
            Represents maximization.
        MINIMIZE : str
            Represents minimization.

    """

    CONTINUOUS = VarType.CONTINUOUS
    INTEGER = VarType.INTEGER
    BINARY = VarType.BINARY
    MAXIMIZE = HybridSolverOptSenses.MAXIMIZE
    MINIMIZE = HybridSolverOptSenses.MINIMIZE


class PythonMipStatus(Enum):
    """An enumeration class representing the status of the hybrid solver after run.

    OPTIMAL : str
        Represents optimal solution.
    OBJECTIVE_LIMIT_REACHED : str
        Represents objective limit reached.
    FEASIBLE : str
        Represents feasible solution.
    INFEASIBLE : str
        Represents infeasible solution.
    UNBOUNDED : str
        Represents unbounded objective function.
    INFEASIBLE_OR_UNBOUNDED : str
        Represents infeasible or unbounded problem.
    UNSUITABLE : str
        Represents unsuitable problem.
    TIMELIMIT : str
        Represents time limit reached.
    ABORTED : str
        Represents aborted run.
    NUMERICAL_ERROR : str
        Represents numerical error occured.
    READERROR : str
        Represents read error.
    TERMINATED : str
        Represents terminated run.
    FAILED : str
        Represents failed run.
    COMPLETE : str
        Represents complete run.
    UNKNOWN : str
        Represents unknown status.
    """

    OPTIMAL = HybridSolverStatus.OPTIMAL
    OBJECTIVE_LIMIT_REACHED = HybridSolverStatus.OBJECTIVE_LIMIT_REACHED
    FEASIBLE = HybridSolverStatus.FEASIBLE
    INFEASIBLE = HybridSolverStatus.INFEASIBLE
    UNBOUNDED = HybridSolverStatus.UNBOUNDED
    INFEASIBLE_OR_UNBOUNDED = HybridSolverStatus.INFEASIBLE_OR_UNBOUNDED
    UNSUITABLE = HybridSolverStatus.UNSUITABLE
    TIMELIMIT = HybridSolverStatus.TIMELIMIT
    ABORTED = HybridSolverStatus.ABORTED
    NUMERICAL_ERROR = HybridSolverStatus.NUMERICAL_ERROR
    READERROR = HybridSolverStatus.READERROR
    TERMINATED = HybridSolverStatus.TERMINATED
    FAILED = HybridSolverStatus.FAILED
    COMPLETE = HybridSolverStatus.COMPLETE
    UNKNOWN = HybridSolverStatus.UNKNOWN


# dictionary that maps hybridsolver status to python-mip status
hybridsolver_status_to_python_mip = {
    HybridSolverStatus.OPTIMAL: PythonMipStatus.OPTIMAL,
    HybridSolverStatus.OBJECTIVE_LIMIT_REACHED: PythonMipStatus.OBJECTIVE_LIMIT_REACHED,
    HybridSolverStatus.FEASIBLE: PythonMipStatus.FEASIBLE,
    HybridSolverStatus.INFEASIBLE: PythonMipStatus.INFEASIBLE,
    HybridSolverStatus.UNBOUNDED: PythonMipStatus.UNBOUNDED,
    HybridSolverStatus.INFEASIBLE_OR_UNBOUNDED: PythonMipStatus.INFEASIBLE_OR_UNBOUNDED,
    HybridSolverStatus.UNSUITABLE: PythonMipStatus.UNSUITABLE,
    HybridSolverStatus.TIMELIMIT: PythonMipStatus.TIMELIMIT,
    HybridSolverStatus.ABORTED: PythonMipStatus.ABORTED,
    HybridSolverStatus.NUMERICAL_ERROR: PythonMipStatus.NUMERICAL_ERROR,
    HybridSolverStatus.READERROR: PythonMipStatus.READERROR,
    HybridSolverStatus.TERMINATED: PythonMipStatus.TERMINATED,
    HybridSolverStatus.FAILED: PythonMipStatus.FAILED,
    HybridSolverStatus.COMPLETE: PythonMipStatus.COMPLETE,
    HybridSolverStatus.UNKNOWN: PythonMipStatus.UNKNOWN,
}

# dictionary that maps the hybrisolver senses to python-mip senses
hybridsolver_sense_to_python_mip = {
    HybridSolverOptSenses.MAXIMIZE: PythonMipEnum.MAXIMIZE,
    HybridSolverOptSenses.MINIMIZE: PythonMipEnum.MINIMIZE,
}

hybridsolver_variable_type_to_python_mip = {
    VarType.CONTINUOUS: PythonMipEnum.CONTINUOUS,
    VarType.INTEGER: PythonMipEnum.INTEGER,
    VarType.BINARY: PythonMipEnum.BINARY,
}
