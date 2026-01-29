import copy
import importlib.resources
import logging
from importlib.abc import Traversable
from pathlib import Path
from typing import Any, Literal, Self

from sentineltoolbox.configuration import get_config
from sentineltoolbox.exceptions import S3BucketCredentialNotFoundError
from sentineltoolbox.filesystem_utils import get_universal_path
from sentineltoolbox.models.upath import PathFsspec
from sentineltoolbox.readers.raw_loaders import load_json_fp, load_toml_fp, load_yaml_fp

logger = logging.getLogger("sentineltoolbox")


class ReloadableDict(dict):  # type: ignore
    def __init__(self, data: Any = None, **kwargs: Any):
        self._loader_kwargs = kwargs
        if data is None:
            dict.__init__(self)
            kwargs = copy.copy(kwargs)
            kwargs["recursive"] = False
            self.reload(**kwargs)
        else:
            dict.__init__(self, copy.copy(data))

    def reload(self, **kwargs: Any) -> Self:
        self.clear()
        _kwargs = copy.copy(self._loader_kwargs)
        _kwargs.update(kwargs)
        replace_data = kwargs.get("replace")
        if replace_data:
            self.update(replace_data)
        else:
            # force reload is necessary:
            #   - dict has been cleaned (self.clear at the beginning of the function), so cached data has been cleared
            #   - by default load_resources use cached data, so ti will return cleared data (empty data)
            _kwargs["force"] = True
            self.update(load_resource_file(**_kwargs))

        extend_data = kwargs.get("extend", {})
        self.update(extend_data)
        return self


def _load_path(path: Path | PathFsspec, fmt: Literal[".json", ".toml", ".txt", None] = None, **kwargs: Any) -> Any:
    if fmt is None:
        real_fmt = path.suffix
    else:
        real_fmt = fmt

    if not kwargs.get("disable_log", False):
        # at this step, logging conf is not fully initialized so we need to disable logging manually is some cases
        logger.info(f"load {real_fmt!r} resource file '{path}'")

    if real_fmt == ".json":
        with path.open("r", encoding="utf-8") as f:
            return load_json_fp(f)
    elif real_fmt == ".toml":
        with path.open("rb") as f:
            return load_toml_fp(f)
    elif real_fmt == ".yaml":
        with path.open("r", encoding="utf-8") as f:
            return load_yaml_fp(f)
    else:
        with path.open() as f:
            return f.read()


def get_resource_paths(
    relpath: str | Path,
    *,
    module: str = "sentineltoolbox.resources",
    **kwargs: Any,
) -> list[PathFsspec | Path]:
    conf = kwargs.get("configuration", get_config())
    user_resources = conf.data.get("resources", {}).get(module, [])
    if isinstance(relpath, Path):
        relpath = relpath.as_posix()
    else:
        relpath = str(relpath)

    invalid_paths: list[Any] = []

    # First, read extra user paths (default: empty)
    resource_files: list[Path | PathFsspec | Traversable] = []
    for user_resource_dir in user_resources:
        try:
            upath = get_universal_path(user_resource_dir) / relpath
        except (FileNotFoundError, S3BucketCredentialNotFoundError):
            invalid_paths.append(
                (f"{user_resource_dir}/{relpath}", f"get_universal_path failed on {user_resource_dir}"),
            )
        else:
            resource_files.append(upath)

    # Then, read resources in config path (default: empty)
    resource_files.append(conf.config_path.parent / "resources" / module / relpath)

    # Then read package builtin resources
    # Get path to resource.
    # Remember, in some cases path can be inside a zip or wheel and not usable directly
    traversable: Traversable = importlib.resources.files(module) / str(relpath)
    resource_files.append(traversable)

    # To get a path that can be open, we must use as_file
    # See warning above!
    paths = []
    for filepath in resource_files:
        if isinstance(filepath, (PathFsspec, Path)):
            try:
                if filepath.exists():
                    paths.append(filepath)
            except PermissionError:
                logger.warning("Permission error on file '%s'. Please check credentials and permissions", filepath)
        elif isinstance(filepath, Traversable):
            with importlib.resources.as_file(filepath) as real_file_path:
                if real_file_path.exists():
                    paths.append(real_file_path)
                else:
                    invalid_paths.append((real_file_path, "path does not exist"))
                    continue
        else:
            invalid_paths.append((filepath, f"type {type(filepath)} is not supported"))
            continue
    if paths:
        return paths
    else:
        invalid_paths_str = ""
        for filepath, error in invalid_paths:
            invalid_paths_str += f" - '{filepath}': {error}\n"
        raise FileNotFoundError(f"{relpath} not found.\n{invalid_paths_str}")


def get_resource_path(
    relpath: str | Path,
    *,
    module: str = "sentineltoolbox.resources",
    **kwargs: Any,
) -> Path | PathFsspec:
    return get_resource_paths(relpath, module=module, **kwargs)[0]


# @lru_cache(maxsize=20)
def load_resource_file(
    relpath: str | Path,
    *,
    fmt: Literal[".json", ".toml", ".txt", None] = None,
    module: str = "sentineltoolbox.resources",
    target_type: Any = None,
    **kwargs: Any,
) -> Any:
    """
    Function to load resource files. Resource file are files provided by python packages or by user.
    You do not need to know exactly where file is, you only need to know:
      - the package providing resources. For example "sentineltoolbox.resources"
      - the relative path of file you want to load. For example: "info.json" or "metadata/product_properties"

    This function search resources in different path, following this order:
      - path defined in sentineltoolbox configuration (if defined, see "Software Configuration")
      - ~/.eopf/resources/<module>/
      - python package defined by "module" keyword

    and return the first object found

    :param relpath: path relative to resource package
    :param fmt: file format. If not specified, tries to guess
    :param module: python module path containing resources. Default sentineltoolbox.resources
    :param target_type: if specified, ensure returned type correspond to expected type. If not raise error
    :return: loaded data. Can be dict (JSON), str (text file), ...
    """
    resource_id = (module, relpath)
    conf = kwargs.get("configuration", get_config())

    if resource_id in conf.cache.get("resource_file", {}) and not kwargs.get("force", False):
        return conf.cache["resource_file"][resource_id]
    else:
        path = get_resource_path(relpath, module=module, **kwargs)
        data = _load_path(path, fmt=fmt, **kwargs)
        conf.cache.setdefault("resource_file", {})[resource_id] = data

        if target_type and not isinstance(data, target_type):
            raise IOError(f"data {path} doesn't match expected type {target_type!r}")

        return data
