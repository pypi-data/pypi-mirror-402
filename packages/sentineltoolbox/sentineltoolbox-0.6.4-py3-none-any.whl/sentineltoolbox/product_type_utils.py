from typing import Any

from sentineltoolbox._utils import _get_attr_dict
from sentineltoolbox.metadata_utils import STAC_PRODUCT_TYPE
from sentineltoolbox.models.filename_generator import extract_ptype_from_filename
from sentineltoolbox.typedefs import (
    T_Attributes,
    T_ContainerWithAttributes,
    as_attributes,
    as_dpr_tree,
    is_dpr_tree,
    is_eoproduct,
)


def guess_product_type(obj: T_ContainerWithAttributes | T_Attributes, **kwargs: Any) -> str:
    """
    Attempt to determine the product type for a given object.

    This function tries to extract the product type from the provided object using these strategies in this order:
    1. [user] If a 'product_type' keyword argument is provided, it is used directly
    2. [filename] attempts to extract the product type from the filename.
        filename is available only if object was open with stb.open_datatree function
    3. [metadata] attempts to extract the product type from the metadata
        (generally in stac_discovery/properties/product:type)

    You can change order and choose strategies to use thanks to metadata_extractors kwarg.
    For example:
      - metadata_extractors=["user", "metadata"]
      - metadata_extractors=["filename"]

    Parameters
    ----------
    obj : T_ContainerWithAttributes | T_Attributes
        The object from which to guess the product type. Must support attribute access or dictionary-like access.
    **kwargs : Any
        Optional keyword arguments. If 'product_type' is provided, it will be used as the product type.

    Returns
    -------
    str
        The guessed product type. Returns an empty string if the product type cannot be determined.
    """

    extractors = kwargs.get("metadata_extractors", ["user", "filename", "metadata", "fixed-metadata"])
    ptype: str = ""
    attrs = _get_attr_dict(obj)
    for extractor in extractors:
        if extractor == "user":
            # use product_type passby user as argument
            ptype = kwargs.get("product_type", "")
        elif extractor == "filename":
            # extract product type from filename. Filename is store if datatree is open with stb.open_datatree
            try:
                info = obj.reader_info  # type: ignore
            except AttributeError:
                info = attrs

            ptype = extract_ptype_from_filename(info.get("filename", info.get("name", "")), error="ignore")

        elif extractor == "eopf":
            if is_eoproduct(obj):
                ptype = obj.product_type  # type: ignore

        elif extractor == "metadata":
            # extract product form stac attributes
            ptype = attrs.get("stac_discovery", {}).get("properties", {}).get(STAC_PRODUCT_TYPE, "")

        elif extractor == "fixed-metadata":
            from sentineltoolbox.attributes import AttributeHandler
            from sentineltoolbox.datatree_utils import DataTreeHandler

            if is_dpr_tree(obj):
                handler: AttributeHandler = DataTreeHandler(as_dpr_tree(obj))
            else:
                handler = AttributeHandler(as_attributes(obj))
            ptype = handler.datatype

        if ptype:
            return ptype

    return ptype
