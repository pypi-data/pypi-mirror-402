from typing import Literal

import xarray as xr
from xarray import DataTree
from xarray.core.datatree_mapping import map_over_datasets


def map_over_subtree(func):  # type: ignore

    def wrapper_map_over_subtree(*args, **kwargs):  # type: ignore
        return map_over_datasets(func, *args, **kwargs)

    return wrapper_map_over_subtree


@map_over_subtree
def filter_flags(ds: xr.Dataset) -> xr.Dataset:
    """Filter only flags variable while preserving the whole structure
    Following the CF convention, flag variables are filtered based on the presence of "flag_masks" attribute

    Parameters
    ----------
    ds
        input xarray.Dataset or DataTree

    Returns
    -------
        xarray.Dataset or DataTree
    """
    return xr.merge(
        [
            ds.filter_by_attrs(flag_masks=lambda v: v is not None),
            ds.filter_by_attrs(flag_values=lambda v: v is not None),
        ],
    )


def filter_datatree(
    dt: DataTree,
    vars_grps: list[str],
    type: Literal["variables", "groups", "flags"],
) -> DataTree:
    """Filter datatree by selecting a list of given variables or groups

    Parameters
    ----------
    dt
        input DataTree
    vars_grps
        List of variable or group paths
    type
        Defines if the list is made of variables or groups ("variables" or "groups")

    Returns
    -------
        Filtered DataTree

    Raises
    ------
    ValueError
        if incorrect type is provided
    """
    if type == "variables":
        dt = dt.filter(
            lambda node: any(
                "/".join([node.path, var]) in vars_grps for var in node.variables  # type: ignore[list-item]
            ),
        )
        for tree in dt.subtree:
            variables = list(tree.data_vars)
            drop_variables = [v for v in variables if "/".join([tree.path, v]) not in vars_grps]
            if drop_variables:
                # Create a new DataTree node with the updated dataset
                updated_dataset = tree.dataset.drop_vars(drop_variables)
                new_node = DataTree(dataset=updated_dataset)
                new_node.attrs.update(tree.attrs)
                dt[tree.path] = new_node
    elif type == "groups":
        # We use startswith to keep also all descendants groups.
        # Append "/" to node.path in filter to allow vars_grps ending with "/".
        dt = dt.filter(lambda node: any((node.path + "/").startswith(grp_path) for grp_path in vars_grps))
    elif type == "flags":
        for tree in dt.subtree:
            variables = list(tree.data_vars)
            drop_variables = [v for v in variables if "flag_masks" in tree[v].attrs or "flag_values" in tree[v].attrs]
            if drop_variables:
                # Create a new DataTree node with the updated dataset
                updated_dataset = tree.dataset.drop_vars(drop_variables)
                new_node = DataTree(dataset=updated_dataset)
                new_node.attrs.update(tree.attrs)
                dt[tree.path] = new_node
    else:
        raise ValueError("type as incorrect value: ", type)

    return dt


def drop_empty_vars_from_dataset(ds: xr.Dataset, *, drop_coords: bool = False) -> xr.Dataset:
    """
    Return a Dataset with data variables removed that have any dimension of length 0.
    By default coordinates are preserved; set drop_coords=True to remove coordinates
    that are empty as well.
    """
    # find empty data variables: any dim length == 0
    empty_data_vars = [name for name, da in ds.data_vars.items() if any(sz == 0 for sz in da.sizes.values())]
    if empty_data_vars:
        ds = ds.drop_vars(empty_data_vars)

    if drop_coords:
        # also drop coords that have any zero-sized dimension
        empty_coords = [name for name, coord in ds.coords.items() if any(sz == 0 for sz in coord.sizes.values())]
        if empty_coords:
            ds = ds.drop_vars(empty_coords)  # coords are stored as variables -> drop_vars works

    return ds


def drop_empty_vars(dt: DataTree, *, drop_coords: bool = False) -> DataTree:
    """
    Return a DataTree with data variables removed that have any dimension of length 0.
    By default coordinates are preserved; set drop_coords=True to remove coordinates
    that are empty as well.
    """
    return dt.map_over_datasets(lambda ds: drop_empty_vars_from_dataset(ds, drop_coords=drop_coords))
