from __future__ import annotations

import os
import warnings

import requests
from semantic_version import Version

from quantagonia.__about__ import __version__

# quantagonia imports for convenience usage
from quantagonia.cloud.cloud_runner import CloudRunner as HybridSolver  # noqa: F401
from quantagonia.parameters import HybridSolverParameters  # noqa: F401


# setup warnings
def custom_formatwarning(msg: str | Warning, *_unused_args, **_unused_kwargs) -> str:
    # ignore everything except the message
    return str(msg) + "\n"


warnings.formatwarning = custom_formatwarning


def check_version_compatibility() -> None:
    """Check if installed client version is compatible to server."""
    try:
        package = "quantagonia"
        response = requests.get(f"https://pypi.org/pypi/{package}/json", timeout=1)
        latest_version = Version(response.json()["info"]["version"])
        current_version = Version(__version__)

        is_supported = current_version.major >= latest_version.major
        is_latest = current_version >= latest_version
    except:  # noqa: E722
        warnings.warn("Unable to collect latest version information, skipping check.", stacklevel=2)
        is_supported = True
        is_latest = True
        latest_version = Version("0.0.0")

    # throw error if installed version not compatible
    if not is_supported:
        message = (
            f"Installed version {__version__} of quantagonia is not compatible "
            f"due to breaking changes in version {latest_version}. "
        )
        message += f"Please update to the latest version {latest_version}."

        raise ImportError(message)

    # print warning if update available
    if not is_latest:
        message = f"Installed version {__version__} of quantagonia is outdated. "
        message += f"Consider updating to the latest version {latest_version}."

        warnings.warn(message, stacklevel=2)


# skip version check for development
if "SKIP_VERSION_CHECK" not in os.environ or os.environ["SKIP_VERSION_CHECK"] != "1":
    check_version_compatibility()
