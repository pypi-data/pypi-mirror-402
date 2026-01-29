from __future__ import annotations

from enum import Enum


class HybridSolverOptSenses(Enum):
    """An enumeration class representing the optimization senses for the hybrid solver.

    Attributes:
    ----------
        MAXIMIZE: Holds a string representing maximization.
        MINIMIZE: Holds a string representing minimization.

    """

    MAXIMIZE = "MAXIMIZE"
    MINIMIZE = "MINIMIZE"


class HybridSolverProblemType(str, Enum):
    MIP = "MIP"
    QUBO = "QUBO"


class VarType(Enum):
    """An enumeration class representing the types of variables.

    Attributes:
    ----------
    CONTINUOUS : str
        Represents a continuous variable.
    INTEGER : str
        Represents an integer variable.
    BINARY : str
        Represents a binary variable.
    """

    CONTINUOUS = "C"
    INTEGER = "I"
    BINARY = "B"


class HybridSolverStatus(str, Enum):
    OPTIMAL = "Optimal"
    OBJECTIVE_LIMIT_REACHED = "Objective Limit Reached"
    FEASIBLE = "Feasible"
    INFEASIBLE = "Infeasible"
    UNBOUNDED = "Unbounded"
    INFEASIBLE_OR_UNBOUNDED = "Infeasible or Unbounded"
    UNSUITABLE = "Unsuitable"
    TIMELIMIT = "Time Limit"
    ABORTED = "Aborted"  # This means that the user aborted the run
    NUMERICAL_ERROR = "Numerical Error"
    READERROR = "Read Error"
    TERMINATED = "Terminated"
    FAILED = "Failed"
    COMPLETE = "Complete"
    UNKNOWN = "Unknown"

    @classmethod
    def _missing_(cls, value: any) -> None | HybridSolverStatus:
        if isinstance(value, str):
            for member in cls:
                if member.value.lower() == value.strip().lower():
                    return member
        return None
