import base64
import gc
import json
import logging
import os
import tempfile
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from sentineltoolbox._utils import split_protocol
from sentineltoolbox.readers.raw_loaders import load_toml

logger = logging.getLogger("sentineltoolbox")


class Configuration:
    _current: "Configuration | None" = None

    def __init__(self, **kwargs: Any) -> None:
        self._map_secret_alias_path: dict[str, list[str]] = {}
        self.config_path = kwargs.get("path", Path.home() / ".eopf/sentineltoolbox.toml")
        self._data: dict[Any, Any] = {}
        self._temporary_directories: dict[str, TemporaryDirectory[str]] = {}
        self.cache: dict[str, dict[Any, Any]] = {"resource_db": {}, "resource_file": {}}
        self.plugins_hotfix: list[Any] = []
        self.reload()

    def get_cached_data(self, cache_group: str, cache_identifier: Any, data_factory: Any = None, **kwargs: Any) -> Any:
        """
        Parameters
        ----------
        cache_group : str
            Name of the cache group or namespace used to partition cached values
        cache_identifier : Any
            Key within the group that identifies the cached value. Must be hashable
            to be used as a dictionary key.
        data_factory : Callable[[], Any], optional
            Zero-argument callable used to compute the value when it is not present
            in the cache or when a forced refresh is requested. If not provided and
            no cached value exists, the method returns None
        **kwargs : Any
            Additional keyword arguments. Supports:
            - force (bool): If True, ignore any existing cached value and recompute
              it using the factory, updating the cache. Defaults to False.

        Returns
        -------
        Any
            The cached value for the given group and identifier if present, or the
            newly created value from the factory when invoked. Returns None if no
            cached value exists and no factory is provided

        Notes
        -----
        - Initializes an empty group entry in the cache dictionary if it does not
          already exist.
        - Does not handle cache eviction or expiration; values persist for the
          lifetime of the cache container.
        """
        if cache_group not in self.cache:
            self.cache[cache_group] = {}
        if cache_identifier in self.cache[cache_group] and not kwargs.get("force", False):
            return self.cache[cache_group][cache_identifier]
        else:
            if data_factory:
                data = data_factory()
                if kwargs.get("cache", True):
                    self.cache[cache_group][cache_identifier] = data
                return data
            else:
                return None

    def cache_data(self, cache_group_name: str, cache_identifier: Any, data_to_cache: Any, **kwargs: Any) -> Any:
        if kwargs.get("cache", True):
            self.cache.setdefault(cache_group_name, {})[cache_identifier] = data_to_cache
        return data_to_cache

    def clear(self) -> None:
        self._map_secret_alias_path.clear()

    def reload(self) -> None:
        """
        Reload all reloadable data like resources or env variables

        :return:
        """
        self.clear()
        if self.config_path.exists():
            self._data.update(load_toml(self.config_path))

        env_file = os.environ.get("SENTINELTOOLBOX_JSON_BASE64")
        if env_file:
            json_str = base64.b64decode(env_file).decode("utf-8")
            conf = json.loads(json_str)
            self._data.update(conf)

        for resource in self.cache.get("resource_db", {}).values():
            try:
                resource.reload()
            except AttributeError:
                pass

        self.map_secret_aliases(self._data.get("secretsmap", {}))

    @classmethod
    def instance(cls, *, new: bool = False, **kwargs: Any) -> "Configuration":
        """

        :param new: if True, each call generate new instance, else, return default instance
        :param kwargs:
        :return:
        """
        if cls._current is None or new:
            cls._current = Configuration(**kwargs)
        return cls._current

    @property
    def data(self) -> dict[Any, Any]:
        return self._data

    def map_secret_aliases(self, map: dict[str, str]) -> None:
        if not isinstance(map, dict):
            raise ValueError(f"dict expected, got {map!r}")
        valid_paths: list[str] = []
        for alias, paths in map.items():
            if not isinstance(alias, str):
                logger.warning(f"Invalid alias. expect str, got {alias!r}")
                continue
            if isinstance(paths, str):
                valid_paths = [paths]
            elif isinstance(paths, (list, tuple)):
                # as expected, nothing to do
                valid_paths = paths
            else:
                logger.warning(f"Invalid data for {alias!r}: expect str or list, got {paths!r}")

            current_paths = self._map_secret_alias_path.get(alias, [])
            final_paths = []
            for path in valid_paths:
                if path in current_paths:
                    logger.warning(f"path {path!r} already registered for alias {alias!r}")
                elif isinstance(path, str) and path.startswith("s3://"):
                    final_paths.append(path)
                else:
                    logger.warning(f"Invalid data for {alias!r}: expect str starting with s3://, got {path!r}")

            if final_paths:
                self._map_secret_alias_path.setdefault(alias, []).extend(final_paths)
            else:
                logger.warning(f"Invalid data {valid_paths!r}: alias {alias!r} not updated")

    def get_secret_alias(self, path: str) -> str | None:
        protocols, relurl = split_protocol(path)
        strurl = f"s3://{relurl}"
        for secret_alias, secret_paths in self._map_secret_alias_path.items():
            for secret_path in secret_paths:
                if strurl.startswith(secret_path):
                    return secret_alias
        return None

    @property
    def secret_aliases(self) -> dict[str, list[str]]:
        return {k: v for k, v in self._map_secret_alias_path.items()}

    def get_temporary_directory(self, identifier: str = "") -> TemporaryDirectory[str]:
        if identifier and identifier in self._temporary_directories:
            tmpdir = self._temporary_directories[identifier]
            if Path(tmpdir.name).exists():
                return tmpdir

        tmpdir = tempfile.TemporaryDirectory(prefix="sentineltoolbox_")
        if not identifier:
            identifier = Path(tmpdir.name).name
        self._temporary_directories[identifier] = tmpdir
        return tmpdir

    def clean_temporary_directories(self) -> None:
        removed = []
        for identifier, tmpdir in self._temporary_directories.items():
            logger.info(f"clean tmp dir {tmpdir.name} used for {identifier!r}")
            try:
                tmpdir.cleanup()
            except PermissionError:
                pass
            else:
                removed.append(identifier)

        for identifier in removed:
            del self._temporary_directories[identifier]

    def __del__(self) -> None:
        gc.collect()
        self.clean_temporary_directories()


def get_config(**kwargs: Any) -> Configuration:
    return kwargs.get("configuration", Configuration.instance(**kwargs))
