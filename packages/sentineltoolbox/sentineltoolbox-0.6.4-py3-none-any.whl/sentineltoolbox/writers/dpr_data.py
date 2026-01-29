import gc
import json
from pathlib import Path
from typing import Any

from xarray import DataTree

from sentineltoolbox.attributes import AttributeHandler
from sentineltoolbox.datatree_utils import DataTreeHandler
from sentineltoolbox.filesystem_utils import get_universal_path
from sentineltoolbox.models.upath import PathFsspec
from sentineltoolbox.writers.json import NumpyEncoder
from sentineltoolbox.writers.zarr import write_zarr


def dump_datatree(data: dict[Any, Any] | DataTree, upath_output: PathFsspec | Path | str, **kwargs: Any) -> None:
    upath = get_universal_path(upath_output, **kwargs)
    attrs = AttributeHandler(data)
    attrs.set_stac("id", upath.stem)
    if isinstance(data, DataTree):
        hdl: AttributeHandler = DataTreeHandler(data)
        hdl.fix()
        write_zarr(data, upath)
        del data
        gc.collect()
    elif isinstance(data, dict):
        upath.path = upath.path.replace(".zarr", ".json")
        hdl = AttributeHandler(data)
        hdl.fix()
        with upath.open("w") as json_file:
            json.dump(data, json_file, indent=2, cls=NumpyEncoder)
    else:
        raise NotImplementedError(f"Cannot dump data of type {type(data)}")
