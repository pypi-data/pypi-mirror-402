__all__ = [
    "copy_static_files",
    "get_source_path",
    "get_static_path",
    "init",
    "init_ipython",
    "init_ipython",
    "init_jupyter_env",
    "run_after_build",
    "run_before_build",
]


import warnings

from ..env import init, init_jupyter_env
from ..sphinxenv import (
    copy_static_files,
    get_source_path,
    get_static_path,
    init_ipython,
    run_after_build,
    run_before_build,
)

warnings.warn(
    "Module sentineltoolbox.autodoc.sphinxenv is deprecated. "
    "Instead, use sentineltoolbox.api or sentineltoolbox.env for advanced usages",
    DeprecationWarning,
)
