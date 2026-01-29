# ruff: noqa: F401 ignore unused imports, they are imported to check if they are available
from __future__ import annotations

import io
import sys
from typing import NoReturn

try:
    import dimod
    import dwave
    import pyqubo
    import qiskit
    import qiskit_optimization
except ImportError:
    print("QUBO extra is not enabled.")
    QUBO_EXTRA_ENABLED = False
else:
    print("QUBO extra is enabled.")
    QUBO_EXTRA_ENABLED = True


def raise_qubo_extras_error() -> NoReturn:
    error_message = "The qubo extra is not enabled. Please install via 'pip install quantagonia[qubo]'."
    raise ImportError(error_message)


# Suppress SCIP output by redirecting it to a dummy stream
class SuppressScipOutput:
    def __enter__(self):
        # Redirect both stdout and stderr to a buffer
        self._output_buffer = io.StringIO()
        self._original_stdout = sys.stdout
        self._original_stderr = sys.stderr
        sys.stdout = self._output_buffer
        sys.stderr = self._output_buffer

    def __exit__(self, exc_type, exc_val, exc_tb):  # noqa: ANN001
        # Restore original stdout and stderr
        sys.stdout = self._original_stdout
        sys.stderr = self._original_stderr

        # Optional: Close the buffer
        self._output_buffer.close()
