__all__ = ["xDataTree", "xDataTreeType"]

from typing import TypeAlias

from xarray import DataTree as xDataTree
from xarray import map_over_datasets

xDataTreeType: TypeAlias = xDataTree


def map_over_subtree(func):  # type: ignore

    def wrapper_map_over_subtree(*args, **kwargs):  # type: ignore
        return map_over_datasets(func, *args, **kwargs)

    return wrapper_map_over_subtree
