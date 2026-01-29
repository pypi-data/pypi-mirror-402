import copy
from typing import Any

import xarray as xr

from sentineltoolbox.logging_utils import init_logging
from sentineltoolbox.sphinxenv import init_ipython, logger
from sentineltoolbox.typedefs import UserExecutionEnvironment

XARRAY_DEFAULT_CONF = {}
# XARRAY_CONF["arithmetic_join"] = "inner"
# XARRAY_CONF["chunk_manager"] = "dask"
# XARRAY_CONF["cmap_divergent"] = "RdBu_r"
# XARRAY_CONF["cmap_sequential"] = "viridis"
XARRAY_DEFAULT_CONF["display_expand_attrs"] = False
XARRAY_DEFAULT_CONF["display_expand_coords"] = False
XARRAY_DEFAULT_CONF["display_expand_data"] = False
XARRAY_DEFAULT_CONF["display_expand_data_vars"] = False
XARRAY_DEFAULT_CONF["display_expand_indexes"] = False
# XARRAY_CONF["display_max_children"] = 6
# XARRAY_CONF["display_max_rows"] = 12
# XARRAY_CONF["display_style"] = "html"
# XARRAY_CONF["display_values_threshold"] = 200
# XARRAY_CONF["display_width"] = 80
# XARRAY_CONF["file_cache_maxsize"] = 128
# XARRAY_CONF["keep_attrs"] = "default"
# XARRAY_CONF["use_bottleneck"] = None
# XARRAY_CONF["use_flox"] = None
# XARRAY_CONF["use_numbagg"] = None
# XARRAY_CONF["use_opt_einsum"] = None
# XARRAY_CONF["warn_for_unclosed_files"] = False


def init_xarray_env(user_env: UserExecutionEnvironment = "notebook") -> None:
    """
    By default collapse all fields (attrs, vars, ...)

    :param user_env:
    :return:
    """
    xarray_conf = copy.copy(XARRAY_DEFAULT_CONF)
    if user_env == "debug":
        xarray_conf["display_expand_attrs"] = True
        xarray_conf["display_expand_coords"] = True
        xarray_conf["display_expand_data"] = True
        xarray_conf["display_expand_data_vars"] = True
        xarray_conf["display_expand_indexes"] = True
    xr.set_options(**xarray_conf)


def init(
    logging_conf: str | None = None,
    ipy_formatters: bool = False,
    env: UserExecutionEnvironment | None = None,
    **kwargs: Any,
) -> None:
    """
    Update logging configuration with logging conf

    We can use this function to associate custome __repr_html__ to any object (including read-only, third party objects)
    using this code:
    html = ipython.display_formatter.formatters['text/html']
    html.for_type(ClassToExtend, repr_html_function)

    Example of use

    >>> init(env="cli")

    Parameters
    ----------
    logging_conf
        conf to use to customize logging, by default "myst.json"
    ipy_formatters
        if set, update IPython to use sentineltoolbox builtins formatters to represent data
    env
        Load predefined environment.
        - doc: use this env for HTML doc generators, for example in autodoc, PDFS/ADFS doc, ... (conf "myst.json")
        - notebook: use this env in interactive jupyter notebooks (default logging conf "tools.json")
        - cli: use this env for command line interfaces. Colorize logs (default logging conf "tools.json")
        - debug: add maximum of information for debug
    """
    if logging_conf is None and env is None:
        env = "doc"

    init_logging_conf(env, logging_conf=logging_conf)

    if env:
        init_xarray_env(env)

    if ipy_formatters is True:
        from sentineltoolbox.autodoc.rendering import IpythonHtmlFormatter

        IpythonHtmlFormatter().ipython_install("text/html")

    try:
        ipython = get_ipython()  # type: ignore
    except NameError:
        pass
    else:
        if env is not None:
            init_ipython(ipython=ipython, env=env)


def init_logging_conf(env: UserExecutionEnvironment | None, logging_conf: str | None = None, **kwargs: Any) -> None:
    if logging_conf is None and env:
        if env == "notebook":
            logging_conf = "tools.json"
        elif env == "doc":
            logging_conf = "myst.json"
        elif env == "cli":
            try:
                import colorlog  # noqa: F401
            except ImportError:
                logging_conf = "tools.json"
                logger.warning("Please install colorlog to use cli environment")
            else:
                logging_conf = "cli.json"
        elif env == "debug":
            logging_conf = "debug.json"
    if logging_conf is not None:
        init_logging(logging_conf, disable_log=env == "doc")


def init_jupyter_env(user_env: UserExecutionEnvironment = "notebook", **kwargs: Any) -> None:
    init(env=user_env, **kwargs)
