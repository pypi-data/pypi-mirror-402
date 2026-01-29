# ruff: noqa: SLF001 we allow private access in this file because pulp requires it
import pulp

from quantagonia.mip.pulp_adapter import HybridSolver_CMD

# inject Quantagonia's solver into PuLP's list
if HybridSolver_CMD not in pulp.apis._all_solvers:
    pulp.apis._all_solvers.append(HybridSolver_CMD)
