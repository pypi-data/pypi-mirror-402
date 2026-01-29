import copy
from typing import Any, Hashable

from packaging.version import Version
from xarray import DataTree

from sentineltoolbox import __version__
from sentineltoolbox.attributes import AttributeHandler
from sentineltoolbox.hotfix import (
    ConverterDateTime,
    HotfixAttrs,
    HotfixDataTree,
    HotfixPath,
    HotfixPathInput,
    HotfixValue,
    HotfixValueInput,
    HotfixWrapper,
    to_int,
    to_lower,
)
from sentineltoolbox.metadata_utils import to_canonical_type
from sentineltoolbox.models.filename_generator import filename_generator
from sentineltoolbox.product_type_utils import guess_product_type
from sentineltoolbox.resources.data import DATAFILE_METADATA, PRODUCT_TREE
from sentineltoolbox.typedefs import (
    AttrsVisitor,
    Converter,
    DataTreeVisitor,
    MetadataType_L,
    T_Attributes,
)

STAC_PRODUT_TYPE = "product:type"
STAC_TIMELINE_CAT = "product:timeliness_category"
STAC_TIMELINESS = "product:timeliness"

#################################################
# WRAPPERS
#################################################
# A wrapper simplifies the user's experience by automatically converting raw data into
# high-level Python types on the fly. For example, a date string is returned as a datetime object.
# It also performs the reverse conversion: if the user sets a datetime object, it is converted
# back to a string to support serialization.

# category / relative path -> Wrapper
WRAPPERS_GENERIC_FUNCTIONS: dict[MetadataType_L, dict[str, Converter]] = {
    "stac_properties": {
        "created": ConverterDateTime(),
        "end_datetime": ConverterDateTime(),
        "start_datetime": ConverterDateTime(),
    },
    "stac_discovery": {},
    "metadata": {},
    "root": {},
}

#################################################
# PATHS FIXES & SHORT NAMES
#################################################
# A "path fix" automatically replaces outdated or incorrect paths with valid ones.
# This is useful for all metadata where the name has changed.

# alias -> valid_category, valid_path
HOTFIX_PATHS_ALIASES: HotfixPathInput = {
    # {"name": ("category", None)}  if short name is equal to attribute path relative to category.
    #  This is equivalent to {"name": ("category", "name")}
    # {"short name": ("category", "relative path name")}  if short name is different
    # Ex: {"b0_id": ("stac_properties", "bands/0/name")}
    # {"/absolute/wrong/path": ("category", "relative/path")}
    # Ex: {"other_metadata/start_time": ("stac_properties", None)}
    # short names
    "bands": ("stac_properties", None),
    "bbox": ("stac_discovery", None),
    "created": ("stac_properties", None),
    "datatake_id": ("stac_properties", None),
    "datetime": ("stac_properties", None),
    "end_datetime": ("stac_properties", None),
    "eo:bands": ("stac_properties", "bands"),
    "eopf": ("stac_properties", None),
    "eopf:datastrip_id": ("stac_properties", None),
    "eopf:instrument_mode": ("stac_properties", None),
    "eopf:timeline": ("stac_properties", STAC_TIMELINE_CAT),
    "product:timeline": ("stac_properties", STAC_TIMELINE_CAT),
    "eopf:type": ("stac_properties", STAC_PRODUT_TYPE),
    "geometry": ("stac_discovery", None),
    "gsd": ("stac_properties", None),
    "instrument": ("stac_properties", None),
    "constellation": ("stac_properties", None),
    "mission": ("stac_properties", None),
    "platform": ("stac_properties", None),
    "processing:level": ("stac_properties", None),
    "processing:version": ("stac_properties", None),
    STAC_TIMELINE_CAT: ("stac_properties", None),
    STAC_TIMELINESS: ("stac_properties", None),
    STAC_PRODUT_TYPE: ("stac_properties", None),
    "providers": ("stac_properties", None),
    "start_datetime": ("stac_properties", None),
    "updated": ("stac_properties", None),
}

# wrong path -> valid_category, valid_path
HOTFIX_PATHS_WRONG: HotfixPathInput = {
    # {"name": ("category", None)}  if short name is equal to attribute path relative to category.
    #  This is equivalent to {"name": ("category", "name")}
    # {"short name": ("category", "relative path name")}  if short name is different
    # Ex: {"b0_id": ("stac_properties", "bands/0/name")}
    # {"/absolute/wrong/path": ("category", "relative/path")}
    # Ex: {"other_metadata/start_time": ("stac_properties", None)}
    # short names
    "stac_discovery/properties/date_created": ("stac_properties", "created"),
    "stac_discovery/properties/eo:bands": ("stac_properties", "bands"),
    "stac_discovery/properties/eopf:type": ("stac_properties", STAC_PRODUT_TYPE),
    "stac_discovery/properties/eopf:timeline": ("stac_properties", STAC_TIMELINE_CAT),
    "stac_discovery/properties/product:timeline": ("stac_properties", STAC_TIMELINE_CAT),
}


#################################################
# VALUE FIXES
#################################################
# Function used to fix definitely value


def fix_04x(attrs: T_Attributes, product_type: str = "") -> bool:
    """
    Apply some hotfix only if we are using sentineltoolbox >= 0.4.0.
    Reason is that sentinel processors are linked to older STAC specs and we don't want to break validation with
    STAC fixes. So keep old values, even if wrong.

    For most recent package using sentineltoolbox >= 0.4.0, we want up-to-date attributes so all fixes are applied

    :return:
    """
    return Version(__version__) > Version("0.4.0")


def is_dpr_product(attrs: T_Attributes, product_type: str = "", **kwargs: Any) -> bool:
    """
    Determines whether the given product type corresponds to a DPR product.

    A DPR product is identified by its inclusion in specific product categories
    related to PRODUCT_TREE.s2 or PRODUCT_TREE.s3.

    :param attrs: Auxiliary Data File (ADF) attributes from the product.
    :param product_type: Type of the product to be validated.
    :param kwargs: Additional arguments for customization or future use.
    :return: Boolean indicating if the product type is categorized as a DPR product.
    """
    return product_type in PRODUCT_TREE.s2 or product_type in PRODUCT_TREE.s3


def fix_bands_stac_names(value: Any, **kwargs: Any) -> Any:
    """
    Rename common_name, center_wavelength, full_width_half_max, solar_illumination, ...
    to eo:common_name, ...

    Fix unit. If wavelength is in nm, convert to µm. All value > 100 is considered to be in nm and is converted.

    https://github.com/stac-extensions/eo/blob/main/CHANGELOG.md#v200-beta1---2024-08-01

    :param value:
    :param kwargs:
    :return:
    """
    changed = False
    if isinstance(value, list):
        new_value = copy.deepcopy(value)
        for band in new_value:
            for field in ("common_name", "center_wavelength", "full_width_half_max", "solar_illumination"):
                if field in band:
                    changed = True
                    band[f"eo:{field}"] = band.pop(field)
        if changed:
            value = new_value
    return value


def fix_bands_in_nm(value: Any, **kwargs: Any) -> Any:
    """
    Rename common_name, center_wavelength, full_width_half_max, solar_illumination, ...
    to eo:common_name, ...

    Fix unit. If wavelength is in nm, convert to µm. All value > 100 is considered to be in nm and is converted.

    https://github.com/stac-extensions/eo/blob/main/CHANGELOG.md#v200-beta1---2024-08-01

    :param value:
    :param kwargs:
    :return:
    """
    changed = False
    if isinstance(value, list):
        new_value = copy.deepcopy(value)
        for band in new_value:
            length = band.get("eo:center_wavelength", 0)
            # wavelength is in nm
            if isinstance(length, (int, float)) and length > 100000:
                changed = True
                band["eo:center_wavelength"] /= 1e6
                if "eo:full_width_half_max" in band:
                    band["eo:full_width_half_max"] /= 1e6
            # wavelength is in nm
            elif isinstance(length, (int, float)) and length > 100:
                changed = True
                band["eo:center_wavelength"] /= 1e3
                if "eo:full_width_half_max" in band:
                    band["eo:full_width_half_max"] /= 1e3

        if changed:
            value = new_value
    return value


def fix_adf_type(value: Any, **kwargs: Any) -> Any:
    c = kwargs.get("attrs", {}).get("stac_discovery", {}).get("properties", {}).get("constellation", None)
    num = None
    if isinstance(c, str):
        try:
            num = int(c.split("-")[-1])
        except ValueError:
            pass

    return to_canonical_type(value, num=num)


# category / relative path -> fix functions
HOTFIX_VALUES_GENERIC: HotfixValueInput = {
    "stac_properties": {
        "platform": to_lower,
        "mission": lambda value, **kwargs: "copernicus",
        "constellation": to_lower,
        "instrument": to_lower,
        "sat:relative_orbit": to_int,
        "datetime": lambda value, **kwargs: None,
        "bands": fix_bands_stac_names,
    },
    "stac_discovery": {},
    "metadata": {},
    "root": {},
}

# category / relative path -> fix functions
HOTFIX_VALUES_ADF_TYPE: HotfixValueInput = {
    "stac_properties": {
        "product:type": fix_adf_type,
    },
}

HOTFIX_VALUES_BANDS_NM: HotfixValueInput = {
    "stac_properties": {
        "bands": fix_bands_in_nm,
    },
}


class FixSentinelDataTree(DataTreeVisitor):
    """
    Add missing metadata like processing:level, mission, instruments.
    Metadata are extracted ...
      - from sentineltoolbox db
      - from product filenames
    """

    def visit_attrs(
        self,
        root: DataTree,
        path: str,
        obj: dict[Hashable, Any],
        node: Any = None,
    ) -> None | dict[Hashable, Any]:
        if "long_name" in obj:
            obj["description"] = obj.pop("long_name")
        attrs = AttributeHandler(obj, builtins=False)

        if path == "/":
            ptype = guess_product_type(root)
            if isinstance(ptype, str):
                metadata = DATAFILE_METADATA.get_metadata(ptype)
                if metadata:
                    for attr_name in (STAC_PRODUT_TYPE, "processing:level", "mission", "instrument"):
                        value = metadata.get(attr_name)
                        if value:
                            if attr_name == "mission":
                                attr_name = "constellation"
                            attrs.set_stac_property(attr_name, value)

            # extract information from filename if not already set in metadata
            if hasattr(root, "reader_info"):
                name = root.reader_info.get("name")
                if name:
                    try:
                        fgen, fdata = filename_generator(name)
                    except NotImplementedError:
                        pass
                    else:
                        metadata = attrs.get_stac_property(default={})
                        for k, v in fgen.stac().get("stac_discovery", {}).get("properties", {}).items():
                            if k not in metadata:
                                attrs.set_stac_property(k, v)
            return obj
        return None


class FixSentinelRootAttrs(AttrsVisitor):
    """
    Fix mission, constellation
    """

    def visit_node(self, root: T_Attributes, path: str, obj: T_Attributes) -> None:
        if path == "/":
            ptype = guess_product_type(root)
            # volountary extend only known products.
            # do not replace by "!ADF"
            if DATAFILE_METADATA.get_metadata(ptype).get("adf_or_product") == "product":
                # Add eopf_category if not exists
                other = obj.setdefault("other_metadata", {})
                other["eopf_category"] = other.get("eopf_category", "eoproduct")

            properties = obj.get("stac_discovery", {}).get("properties", {})
            mission = properties.get("mission")
            is_sentinel = isinstance(mission, str) and mission.lower().startswith("sentinel")
            if mission is None:
                constellation = properties.get("constellation")
                is_sentinel |= isinstance(constellation, str) and constellation.lower().startswith("sentinel")
                if is_sentinel:
                    obj.setdefault("stac_discovery", {}).setdefault("properties", {})["mission"] = "copernicus"
            elif is_sentinel:
                obj.setdefault("stac_discovery", {}).setdefault("properties", {})["mission"] = "copernicus"
                obj["stac_discovery"]["properties"]["constellation"] = mission


HOTFIX = [
    HotfixValue(
        HOTFIX_VALUES_GENERIC,
        name="Generic Metadata Fix",
        description="Fix platform, instrument, bands, ...",
        category="fix",
    ),
    HotfixValue(
        HOTFIX_VALUES_ADF_TYPE,
        name="Fix Adf Type",
        description="Fix ADF product:type to convention S03_ADF_XXXXX",
        category="fix",
    ),
    HotfixValue(
        HOTFIX_VALUES_BANDS_NM,
        name="Fix nm bands",
        description="Convert bands in nm to µm (s2 and s3 DPR products only)",
        is_applicable_func=is_dpr_product,
        category="fix",
    ),
    HotfixPath(
        HOTFIX_PATHS_WRONG,
        priority=10,
        name="Fix wrong paths",
        description="Fix eopf:type, ...",
        category="fix",
    ),
    HotfixPath(
        HOTFIX_PATHS_ALIASES,
        priority=10,
        name="Generic Path Fix",
        description="Fix eopf:type, ...",
        category="convenience",
    ),
    HotfixWrapper(
        WRAPPERS_GENERIC_FUNCTIONS,
        priority=10,
        name="Generic Wrappers",
        description="wrap dates<->datetime.",
        category="convenience",
    ),
    HotfixDataTree(
        FixSentinelDataTree(),
        priority=15,
        name="Fix sentinel datatree",
        description="Add product:type, level, ...",
        category="fix",
    ),
    HotfixAttrs(
        FixSentinelRootAttrs(),
        priority=5,
        name="Fix sentinel metadata",
        description="Add mission=copernicus, ...",
        is_applicable_func=fix_04x,
        category="fix",
    ),
]
