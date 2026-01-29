import ast
import operator
import re
from copy import copy
from pathlib import Path, PurePosixPath
from typing import Any

import numpy as np

from sentineltoolbox.typedefs import (
    T_Attributes,
    T_ContainerWithAttributes,
    is_attributes,
    is_container_with_attributes,
)


def to_posix_str(path: PurePosixPath | Path | str) -> str:
    if isinstance(path, (PurePosixPath, Path)):
        pathstr = path.as_posix()
    else:
        pathstr = PurePosixPath(path).as_posix()
    if ":\\" in pathstr:
        parts = pathstr.split(":\\")
        drive = parts[0]
        relpath = ":\\".join(parts[1:])
        posix_str = drive + ":\\" + relpath.replace("\\", "/")
    else:
        posix_str = pathstr.replace("\\", "/")
    return posix_str


def split_protocol(url: str) -> tuple[set[str], PurePosixPath]:
    """
    Split a URL into its protocol(s) and path component.

    This function takes a URL string and splits it into a set of protocols
    and the corresponding file path in POSIX format. It supports multiple protocols
    (separated by `::`) and assumes the "file" protocol if no protocol is explicitly provided.

    Parameters
    ----------
    url : str
        The input URL or file path to be split into protocol(s) and a path.

    Returns
    -------
    tuple[set[str], PurePosixPath]
        A tuple containing:
        - A set of protocols (e.g., {"file"}, {"s3"}, {"zip", "s3"}).
        - A `PurePosixPath` object representing the file path in POSIX format.

    Example
    -------
    >>> protocols, path = split_protocol("s3::zip://my-bucket/my-folder/myfile.zip")
    >>> path
    PurePosixPath('my-bucket/my-folder/myfile.zip')
    >>> protocols # doctest: +SKIP
    {'s3', 'zip'}

    Notes
    -----
    - If no protocol is specified (i.e., the URL does not contain "://"), it defaults to the "file" protocol.
    - Supports multiple protocols chained together using "::" (e.g., "s3::zip://").
    """
    url_str = str(url)
    # Check if the URL contains a protocol (indicated by "://").
    if "://" in url_str:
        parts = url_str.split("://")
        protocol = parts[0]
        path = parts[1]
        # If no protocol is explicitly specified, default to "file".
        if not protocol:
            protocol = "file"
    else:
        # If there is no "://", assume the entire string is a local path.
        protocol = "file"
        path = url_str
    return set(protocol.split("::")), PurePosixPath(path)


def build_url(protocols: set[str], relurl: PurePosixPath) -> str:
    # build valid_protocol list
    # remove conflicts like zip::file
    # force order like zip::s3
    protocols = copy(protocols)
    valid_protocols = []
    for p in ["zip", "s3"]:
        if p in protocols:
            valid_protocols.append(p)
            protocols.remove(p)
    valid_protocols += list(protocols)
    protocol = "::".join(valid_protocols)
    if str(relurl) == ".":
        return f"{protocol}://"
    else:
        return f"{protocol}://{to_posix_str(relurl)}"


def fix_url(url: str) -> str:
    """
    Fix url to get always same protocols and protocol order.

    >>> fix_url("test.txt")
    'file://test.txt'
    >>> fix_url("/d/test.txt")
    'file:///d/test.txt'
    >>> fix_url("D:\\test.txt")
    'file://D:\\test.txt'
    >>> fix_url("s3://test")
    's3://test'
    >>> fix_url("s3://")
    's3://'
    >>> fix_url("://test")
    'file://test'
    >>> fix_url("://")
    'file://'
    >>> fix_url("zip::s3://")
    'zip::s3://'
    >>> fix_url("s3::zip://")
    'zip::s3://'
    >>> fix_url("s3://test.zip")
    'zip::s3://test.zip'


    :param url:
    :return:
    """
    protocols, relurl = split_protocol(url)
    # add protocols based on extensions
    if Path(str(url)).suffix == ".zip":
        protocols.add("zip")

    return build_url(protocols, relurl)


def _is_s3_url(url: str) -> bool:
    protocols, path = split_protocol(url)
    return "s3" in protocols


def string_to_slice(s: str) -> slice:
    """
    Convert a string in the format "start:stop:step" to a Python slice object.

    :param s: String representing the slice.
    :return: Corresponding Python slice object.
    """
    # Split the string by colon to get start, stop, and step parts
    parts: list[str | Any] = s.split(":")
    parts = [int(part) for part in parts]

    # If the string contains fewer than three parts, append None for missing values
    while len(parts) < 3:
        parts.append(None)

    # Convert the parts to integers or None
    start = int(parts[0]) if parts[0] else None
    stop = int(parts[1]) if parts[1] else None
    step = int(parts[2]) if parts[2] else None

    if start is None and stop is None and step is None:
        raise ValueError(s)

    # Create and return the slice object
    return slice(start, stop, step)


def patch(instance: Any, manager_class: Any, **kwargs: Any) -> None:
    manager = manager_class(instance, **kwargs)

    for attr_name in dir(manager):
        if attr_name.startswith("_"):
            continue
        attr = getattr(manager, attr_name)
        if callable(attr):
            try:  # if method existed before, save it to _method
                setattr(instance, "_" + attr_name, getattr(instance, attr_name))
            except AttributeError:
                pass
            setattr(instance, attr_name, attr)


def _get_attr_dict(data: T_ContainerWithAttributes | T_Attributes) -> T_Attributes:
    if is_container_with_attributes(data):
        return data.attrs  # type: ignore
    elif is_attributes(data):
        return data  # type: ignore
    else:
        raise ValueError(f"type {type(data)} is not supported")


def to_snake_case(string: str) -> str:
    """


    Convert a camelCase or PascalCase string to snake_case.

    Args:
        string (str): The input string in camelCase or PascalCase.

    Returns:
        str: The converted string in snake_case.

    """
    # Step 1: Insert an underscore before any uppercase letter
    # that is preceded by a lowercase letter or number
    pattern = re.compile(r"(?<!^)(?=[A-Z][a-z])")
    string = pattern.sub("_", string)

    # Step 2: Insert an underscore before any sequence of uppercase letters
    # that is followed by a lowercase letter
    pattern = re.compile(r"(?<=[a-z0-9])(?=[A-Z])")
    string = pattern.sub("_", string)

    # Step 3: Convert to lowercase
    return string.lower()


def numpy_dtype_to_python(dtype: Any = None) -> type[Any]:
    """
    Converts a NumPy dtype into a corresponding Python primitive type.

    This function determines the Python equivalent for a given NumPy dtype
    based on its data type category.

    :param dtype: NumPy dtype or any value convertible to dtype, e.g., np.int32.
    :type dtype: numpy.dtype or compatible

    :raises TypeError: If the provided dtype is not a valid NumPy dtype or convertible.

    :return: Corresponding Python type, such as `int`, `float`, `bool`, or `str`.

    :example values:
        - For `np.int32`, it will return `int`.
        - For `np.float64`, it will return `float`.
        - For `np.bool_`, it will return `bool`.
        - For `np.string_`, it will return `str`.

    >>> import numpy as np
    >>> numpy_dtype_to_python('int32')
    <class 'int'>
    >>> numpy_dtype_to_python('short')
    <class 'int'>
    >>> numpy_dtype_to_python('i8')
    <class 'int'>
    >>> numpy_dtype_to_python(np.int8)
    <class 'int'>
    >>> numpy_dtype_to_python(int)
    <class 'int'>
    """
    if dtype is None or dtype is type(None):
        raise TypeError("dtype cannot be None")
    elif str(dtype).lower() in ("str", "string"):
        dtype = str

    dtype = np.dtype(dtype)
    if np.issubdtype(dtype, np.integer):
        return int
    elif np.issubdtype(dtype, np.floating):
        return float
    elif np.issubdtype(dtype, np.bool_):
        return bool
    else:
        return str


def str_to_python_type(s: str, dtype: Any = None) -> tuple[Any, str]:
    """
    Converts a string to a Python data type. Returns the converted value and its corresponding data type
    as a string. Automatically handles boolean, None, numeric, and list types, and attempts conversion
    based on the provided `dtype`. Defaults to `int` if `dtype` is not specified.

    :param s: The input string to be converted. Example: "true", "123", "1.23", or "1, 2, 3".
    :param dtype: The specific type to attempt for the conversion. Example: int, float, str, or None.
                  Defaults to `None`, which uses `int` as the assumed type.

    :return: A tuple where the first element is the converted value and the second is the data type's
             string representation (e.g., "bool", "int", "float").

    :raises ValueError: If the string cannot be converted to the specified or default data type.

    .. doctest::

       >>> str_to_python_type("true")
       (True, 'bool')

       >>> str_to_python_type("42")
       (42, 'int64')

       >>> str_to_python_type("1.0")
       (1.0, 'float64')

       >>> str_to_python_type("1, 2, 3", float)
       ([1.0, 2.0, 3.0], 'float64')
    """
    if s == "":
        return None, "None"
    s = s.strip().lower()
    if s == "false":
        return False, "bool"
    if s == "true":
        return True, "bool"
    if s in ("null", "none"):
        return None, "None"

    if dtype is None:
        dtype = int

    try:
        v = dtype(s)
        return v, np.dtype(type(v)).name
    except ValueError:
        try:
            v = float(s)
            dtype = float
            return v, np.dtype(dtype).name
        except ValueError:
            if "," in s:
                v_list = [i.strip() for i in s.split(",")]
            else:
                v_list = [i.strip() for i in s.split()]
                if len(v_list) <= 1:
                    return v_list[0], np.dtype(str).name
            v = []
            for item in v_list:
                t = str_to_python_type(item, dtype=dtype)
                if t is None:
                    return None, "None"
                else:
                    v.append(t[0])
            return v, np.dtype(type(v[0])).name


def filter_dict(
    d: dict[str, dict[str, Any]],
    condition: str,
) -> list[str]:
    """
    Filters the keys of the given dictionary based on specified conditions.

    This function supports conditions for:
    - Key presence or absence (`"key"`, `"not key"`)
    - Boolean/equality checks (`"key is True"`, `"key is None"`)
    - Membership (`"key in [value1, value2]"`)
    - Comparison operations (`"key >= value"`, `"key != value"`)

    :param d: The dictionary to filter. Example: `{"key1": {"a": 1}, "key2": {"b": 2}}`
    :param condition: The filtering rule as a string. Example: `"a >= 1"`, `"not b"`, `"a is None"`
    :return: A list of keys from the dictionary that satisfy the given condition.

    :raises TypeError: If `condition` is not a string.
    :raises ValueError: If the condition syntax or its value cannot be parsed.
    """
    if not isinstance(condition, str):
        raise TypeError(f"str condition expected, got {condition!r}")
    if not condition.strip():
        return list(d.keys())

    condition = condition.strip()

    try:
        # Parse simple conditions first
        if condition.startswith("not "):
            key = condition[4:].strip()
            return [k for k, v in d.items() if key not in v]

        if " " not in condition and not any(op in condition for op in [">=", "<=", "==", "!=", ">", "<"]):
            return [k for k, v in d.items() if condition in v]

        # Parse more complex conditions
        if " is " in condition:
            key, value = [x.strip() for x in condition.split(" is ", 1)]
            if value not in ("True", "False", "None"):
                raise ValueError(f"Unsupported 'is' value: {value}")
            value_check = {"True": True, "False": False, "None": None}[value]
            return [k for k, v in d.items() if key in v and v.get(key) is value_check]

        if " in " in condition:
            key, values = [x.strip() for x in condition.split(" in ", 1)]
            try:
                values = ast.literal_eval(values)
                return [k for k, v in d.items() if key in v and v[key] in values]
            except (ValueError, SyntaxError):
                raise ValueError(f"Invalid list format in condition: {condition}")

        # Handle comparison operators
        ops = {
            ">=": operator.ge,
            "<=": operator.le,
            "==": operator.eq,
            "!=": operator.ne,
            ">": operator.gt,
            "<": operator.lt,
        }
        for op_str, op_func in sorted(ops.items(), key=lambda x: len(x[0]), reverse=True):
            if op_str in condition:
                parts = condition.replace(op_str, f" {op_str} ").split()
                key = parts[0].strip()
                value_str = " ".join(parts[2:]).strip()
                try:
                    value = ast.literal_eval(value_str)
                    if op_str == "!=":
                        return [k for k, v in d.items() if key in v and (v.get(key) is None or op_func(v[key], value))]
                    return [k for k, v in d.items() if key in v and v.get(key) is not None and op_func(v[key], value)]
                except (ValueError, SyntaxError) as e:
                    raise ValueError(f"Error parsing value in condition: {e}")

        raise ValueError(f"Unsupported operator in: {condition}")

    except (ValueError, SyntaxError) as e:
        raise ValueError(f"Error parsing condition: {e}")
