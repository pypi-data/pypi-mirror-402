import json
from typing import Any, BinaryIO, Callable, TextIO

import tomli
import yaml


def _load_data(path: Any, load_fp_func: Callable[[TextIO], Any]) -> Any:
    if hasattr(path, "open"):
        with path.open("r", encoding="utf-8") as data_fp:
            return load_fp_func(data_fp)
    else:
        with open(str(path), "r", encoding="utf-8") as data_fp:
            return load_fp_func(data_fp)


def _load_data_bytes(path: Any, load_fp_func: Callable[[BinaryIO], Any]) -> Any:
    if hasattr(path, "open"):
        with path.open("rb") as data_fp:
            return load_fp_func(data_fp)
    else:
        with open(str(path), "rb") as data_fp:
            return load_fp_func(data_fp)


def load_toml_fp(fp: BinaryIO) -> dict[str, Any]:
    """
    Load data from a TOML file.

    Provides functionality to read and parse the content of a TOML file
    from a BinaryIO stream and return it as a Python dictionary.

    :param fp: File-like object opened in binary mode, containing the TOML content.
    :return: Parsed TOML data as a dictionary.
    """
    with fp:
        return tomli.load(fp)


def load_yaml_fp(fp: TextIO) -> dict[str, Any]:
    """
    Loads a YAML file from a given file pointer and returns its parsed content.

    :param fp: A file pointer to the YAML file.
    :return: The parsed content of the YAML file as a dictionary.
    """
    with fp:
        dic = yaml.safe_load(fp)
        if dic is None:
            dic = {}
        return dic


def load_json_fp(fp: TextIO) -> dict[str, Any]:
    """
    Loads a JSON file from a given file pointer and returns its parsed content.

    :param fp: A file pointer to the JSON file.
    :return: The parsed content of the JSON file as a dictionary.
    """
    with fp:
        return json.load(fp)


def load_toml(path: Any) -> dict[str, Any]:
    """
    Loads a TOML file from the given file path and returns its content as a dictionary.

    :param path: Path to the TOML file to be loaded.
    :return: Parsed TOML data as a dictionary.
    """
    return _load_data_bytes(path, load_toml_fp)


def load_yaml(path: Any) -> dict[str, Any]:
    """
    Load a YAML file from the given path and parse its content into a dictionary.

    This function reads and parses a YAML file provided through the specified
    file path, converting it into a Python dictionary.

    :param path: The path to the YAML file.
    :return: A dictionary containing parsed YAML data.
    """
    return _load_data(path, load_yaml_fp)


def load_json(path: Any) -> dict[str, Any]:
    """
    Loads and parses a JSON file from the specified path. This function use builtin module json.

    :param path: Path to the JSON file to load.
    :return: Parsed JSON content as a dictionary.
    """
    return _load_data(path, load_json_fp)
