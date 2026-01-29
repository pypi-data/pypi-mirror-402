__all__ = [
    "AUXILIARY_TREE",
    "FIELDS_DESCRIPTION",
    "DATAFILE_METADATA",
    "PRODUCT_PATTERNS",
    "PRODUCT_TREE",
    "PROPERTIES_METADATA",
    "TERMS_METADATA",
    "product_summaries",
    "term_summaries",
    "XML_NAMESPACES",
    "XML_NAMESPACES_WITH_DUPLICATES",
    "fields_headers",
    "NAMESPACES",
]

import copy
from typing import Any, Iterable, Self, Type, TypeVar

from sentineltoolbox._utils import filter_dict
from sentineltoolbox.configuration import get_config
from sentineltoolbox.exceptions import DataSemanticConversionError
from sentineltoolbox.metadata_utils import create_dpr_type_from_semantic
from sentineltoolbox.readers.resources import ReloadableDict, load_resource_file


class ResourceDb(ReloadableDict):
    def map(self, field: str) -> dict[str, Any]:
        map = {}
        for name, metadata in self.items():
            value = metadata.get(field)
            if value is not None:
                map[name] = metadata.get(field)
        return map

    def get_metadata(self, name: str, field: str | None = None, default: Any = None) -> Any:
        if isinstance(name, list):
            if len(name) == 1:
                name = name[0]
            else:
                return {}
        if field is None:
            return self.get(name, {})
        else:
            return self.get(name, {}).get(field, default)

    def summary(
        self,
        names: Iterable[str],
        fields: Iterable[str] = ("name", "description"),
    ) -> list[list[str]]:
        lst: list[list[str]] = []
        for name in names:
            item = []
            for field in fields:
                if field == "name":
                    item.append(name)
                else:
                    item.append(self.get_metadata(name, field, ""))
            lst.append(item)
        return lst


class ProductMetadataResource(ResourceDb):
    def __init__(self, data: ReloadableDict | None = None, **kwargs: Any):
        self.dpr_full_name: dict[str, str] = {}
        conf_kwargs = {}
        for k in ("configuration",):
            if k in kwargs:
                conf_kwargs[k] = kwargs[k]

        self.documentation = load_resource_file("metadata/product_documentation.toml", fmt=".toml", **conf_kwargs)
        self.legacy_to_dpr = custom_db_legacy_to_dpr(**kwargs)
        self.dpr_to_legacy: dict[str, list[str]] = {}
        self.from_split_legacy: list[str] = []
        self.from_merged_legacy: list[str] = []
        super().__init__(data, **kwargs)
        self._field_mapping = {"level": "processing:level", "name": "product:type"}

    def reload(self, **kwargs: Any) -> Self:
        super().reload(**kwargs)
        if kwargs.get("recursive", True):
            if isinstance(self.legacy_to_dpr, ReloadableDict):
                self.legacy_to_dpr.reload()
            if isinstance(self.documentation, ReloadableDict):
                self.documentation.reload()
        self.dpr_full_name.clear()
        self.dpr_to_legacy.clear()

        for dpr_name, metadata in self.items():
            metadata["product:type"] = dpr_name
            if "ADF" in dpr_name:
                semantic = dpr_name.split("_")[-1]
                self.dpr_full_name[dpr_name] = dpr_name  # S03_ADF_OLINS -> S03_ADF_OLINS
                self.dpr_full_name[f"ADF_{semantic}"] = dpr_name  # ADF_OLINS -> S03_ADF_OLINS
                self.dpr_full_name[semantic] = dpr_name  # OLINS -> S03_ADF_OLINS
            else:
                self.dpr_full_name[dpr_name[3:]] = dpr_name  # OLCEFR -> S03OLCEFR
            self.dpr_full_name[dpr_name] = dpr_name  # S03OLCEFR -> S03OLCEFR
            for obsolete_name in metadata.get("obsolete_names", []):
                # if obsolete_name already in dic, that means that it corresponds to an official name
                # ie, obsolete_name has been reused for a new product. Don't replace to not break new product.
                if obsolete_name not in self.dpr_full_name:
                    self.dpr_full_name[obsolete_name] = dpr_name  # S01RFCANC -> S01SRFANC
                    self.dpr_full_name[obsolete_name[3:]] = dpr_name  # RFCANC -> S01SRFANC

        for dpr_name, documentation in self.documentation.items():
            dpr_name = self.dpr_full_name.get(dpr_name, dpr_name)
            self.setdefault(dpr_name, {})["documentation"] = documentation

        self.from_split_legacy = []

        for legacy, dpr_outputs in self.legacy_to_dpr.items():
            if isinstance(dpr_outputs, str):
                dpr_outputs = [dpr_outputs]
            for dpr_name in dpr_outputs:
                if len(dpr_outputs) > 1:
                    self.from_split_legacy.append(dpr_name)
                self.dpr_to_legacy.setdefault(dpr_name, []).append(legacy)

        self.from_merged_legacy = []
        for dpr_name, legacies in self.dpr_to_legacy.items():
            if len(legacies) > 1:
                self.from_merged_legacy.append(dpr_name)

        return self

    def map(self, field: str) -> dict[str, Any]:
        map = {}
        for dpr_name, metadata in self.items():
            map[dpr_name] = metadata.get(field)
        return map

    def filter(self, condition: str) -> list[str]:
        """
        Filters elements in a dictionary based on the given condition.

        The condition must be a string specifying a filter criterion. This condition
        is used to evaluate which elements from the dictionary should be included
        in the result.

        :param condition: Filtering condition. For example, "active=True", "status='okay'".
        :return: Filtered list of elements matching the condition.

        :raises ValueError: If the condition is invalid or cannot be processed.
        """
        return filter_dict(self, condition)

    def get_metadata(self, name: str, field: str | None = None, default: Any = None) -> Any:
        dpr_name = self.to_dpr_ptype(name)
        if isinstance(dpr_name, list):
            if len(dpr_name) == 1:
                dpr_name = dpr_name[0]
            else:
                dpr_name = name

        if field is None:
            return self.get(dpr_name, {})
        elif field == "legacy":
            return self.to_legacy_ptypes(name)
        else:
            field = self._field_mapping.get(field, field)
            return self.get(dpr_name, {}).get(field, default)

    def to_dpr_ptype(
        self,
        product_type: str,
        default: list[str] | str | None = None,
        **kwargs: Any,
    ) -> str | list[str] | None:

        # already a dpr name following conventions SXX_ADF_ABCDE, ADF_ABCDE, ABCDE, SXXABCDEF, ABCDEF
        if isinstance(product_type, list):
            ptypes = [self.to_dpr_ptype(p, default=None, **kwargs) for p in product_type if p]
            if not ptypes:
                return default
        else:
            # convert to canonical type to transform for example S03A_ADF_ABCDE to S03_ADF_ABCDE
            dpr_type: str | list[str] | None = create_dpr_type_from_semantic(product_type, **kwargs)
            # first look if raw name found in db, then look for canonical name.
            # this order is important. For example if SAMPLE is registered in db as alias to S02_ADF_SAMPLE
            # we want to return S02_ADF_SAMPLE and not canonical name S00_ADF_SAMPLE
            if isinstance(dpr_type, str):
                dpr_type = self.dpr_full_name.get(product_type, self.dpr_full_name.get(dpr_type))
            if dpr_type is None:
                # maybe it is a legacy name ?
                dpr_type = self.legacy_to_dpr.get(product_type, default)

            if isinstance(dpr_type, (str, list)):
                return dpr_type

        return []

    def to_dpr_ptypes(self, product_type: str) -> list[str]:
        new_ptypes = self.to_dpr_ptype(product_type)
        if isinstance(new_ptypes, str):
            return [new_ptypes]
        elif isinstance(new_ptypes, list):
            return new_ptypes
        else:
            raise DataSemanticConversionError(
                f"Invalid value for legacy {product_type!r}.\n"
                f"Please specify correct semantic with semantic='XXXXX' Or fix db (wrong value: {new_ptypes!r})",
            )

    def to_legacy_ptype(self, product_type: str) -> list[str] | str:
        dpr_name = self.to_dpr_ptype(product_type)
        if product_type in self.legacy_to_dpr:
            # already a legacy name
            result: list[str] = [product_type]
        elif product_type in self.dpr_to_legacy:
            result = self.dpr_to_legacy[product_type]
        elif isinstance(dpr_name, str) and dpr_name in self.dpr_to_legacy:
            result = self.dpr_to_legacy[dpr_name]
        else:
            result = []

        if len(result) == 1:
            return result[0]
        else:
            return result

    def to_legacy_ptypes(self, product_type: str) -> list[str] | str:
        new_ptypes = self.to_legacy_ptype(product_type)
        if isinstance(new_ptypes, str):
            return [new_ptypes]
        elif isinstance(new_ptypes, list):
            return new_ptypes
        else:
            raise DataSemanticConversionError(
                f"Invalid value for legacy {product_type!r}.\n"
                f"Please specify correct semantic with semantic='XXXXX' Or fix db (wrong value: {new_ptypes!r})",
            )


T = TypeVar("T", ResourceDb, ProductMetadataResource)


def _custom_db_factory(custom_db_identifier: str, custom_db_class: Type[T], **kwargs: Any) -> T:
    kwargs = kwargs.copy()
    user_db = kwargs.get(f"{custom_db_identifier}_db")
    user_values = kwargs.get(custom_db_identifier, {})
    if user_values:
        kwargs["cache"] = False
        kwargs["force"] = True

    cache_id = custom_db_identifier
    if user_db is None:
        config = get_config(**kwargs)
        db: T = config.get_cached_data("resource_db", cache_id, **kwargs)
        if db is None:
            kwargs["extend"] = user_values
            return config.cache_data("resource_db", cache_id, custom_db_class(**kwargs), **kwargs)
    else:
        db = user_db
    return db


def custom_db_properties(**kwargs: Any) -> ResourceDb:
    """
    :param kwargs:
      - properties_db: existing db. If set, simply return it
      - properties: list of values to extend default db
    :return: db
    """
    kwargs = kwargs.copy()
    kwargs["relpath"] = "metadata/properties.json"
    return _custom_db_factory("properties", ResourceDb, **kwargs)


def custom_db_legacy_to_dpr(**kwargs: Any) -> ResourceDb:
    """
    :param kwargs:
      - legacy_to_dpr_db: existing db. If set, simply return it
      - legacy_to_dpr: list of values to extend default db
    :return: db
    """
    kwargs = kwargs.copy()
    kwargs["relpath"] = "metadata/mapping_legacy_dpr.json"
    return _custom_db_factory("legacy_to_dpr", ResourceDb, **kwargs)


def custom_db_datafiles(**kwargs: Any) -> ProductMetadataResource:
    """
    TODO: factorize with other custom_db_xxxx and avoid multiple loading.
    Should use get_config().resources to manage cache.

    :param kwargs:
      - datafiles_db: existing db. If set, simply return it
      - datafiles: list of values to extend default db
      - legacy_to_dpr_db: See custom_db_legacy_to_dpr
      - legacy_to_dpr: See custom_db_legacy_to_dpr
    :return: db
    """
    kwargs = kwargs.copy()
    kwargs["relpath"] = "metadata/datafiles.json"
    return _custom_db_factory("datafiles", ProductMetadataResource, **kwargs)


DATAFILE_METADATA = custom_db_datafiles()


FIELDS_DESCRIPTION = load_resource_file("metadata/fields_description.json")

PRODUCT_PATTERNS = load_resource_file("product_patterns.json")

# Note: The `load_resource_file` function can load user-defined data from the local user directory.
# Therefore, if patterns are extended by the user, prioritize user-defined patterns over the default generic ones.
PRODUCT_PATTERNS["S03OLCLFR"] = PRODUCT_PATTERNS.get("S03OLCLFR", PRODUCT_PATTERNS["S3OLCI"])
PRODUCT_PATTERNS["S03OLCLRR"] = PRODUCT_PATTERNS.get("S03OLCLRR", PRODUCT_PATTERNS["S3OLCI"])
PRODUCT_PATTERNS["S03OLCEFR"] = PRODUCT_PATTERNS.get("S03OLCEFR", PRODUCT_PATTERNS["S3OLCI"])
PRODUCT_PATTERNS["S03OLCERR"] = PRODUCT_PATTERNS.get("S03OLCERR", PRODUCT_PATTERNS["S3OLCI"])

PRODUCT_PATTERNS["S03SLSRBT"] = PRODUCT_PATTERNS.get("S03SLSRBT", PRODUCT_PATTERNS["SLSTR_RBT"])


PROPERTIES_METADATA = custom_db_properties()
TERMS_METADATA = ResourceDb(relpath="metadata/terms.json")

NAMESPACES = load_resource_file("namespaces.json")
XML_NAMESPACES = NAMESPACES.get("xml_namespaces", {})
XML_NAMESPACES_WITH_DUPLICATES = copy.copy(XML_NAMESPACES)
for alias, real_name in NAMESPACES.get("xml_aliases", {}).items():
    if real_name in XML_NAMESPACES:
        XML_NAMESPACES_WITH_DUPLICATES[alias] = XML_NAMESPACES[real_name]


class ProductTree(dict):  # type: ignore
    def __init__(self, metadata: ProductMetadataResource, tree_type: str = "product") -> None:
        super().__init__()
        self.s2: list[str] = []
        self.s3: list[str] = []
        self.all: list[str] = []
        self.s3_l0: list[str] = []

        self.metadata = metadata
        self.tree_type = tree_type
        self.reload(reload_metadata=False)

    def reload(self, **kwargs: Any) -> Self:
        if kwargs.get("recursive", True):
            self.metadata.reload()
        self.s2 = []
        self.s3 = []
        self.all = []
        self.s3_l0 = []
        for dpr_name, data in self.metadata.items():
            if data.get("adf_or_product") != self.tree_type:
                continue
            level = data.get("processing:level", "unknown")
            instrument = data.get("instrument", "X")
            mission = data.get("mission", "sentinel")
            self.all.append(dpr_name)
            if mission == "sentinel-2":
                self.s2.append(dpr_name)
            if mission == "sentinel-3":
                self.s3.append(dpr_name)
                if level == "L0":
                    self.s3_l0.append(dpr_name)
            if level == "L0" and mission == "sentinel":
                self.s3_l0.append(dpr_name)

            self.setdefault(mission, {}).setdefault(instrument, {}).setdefault(level, []).append(dpr_name)
            self.setdefault(mission, {}).setdefault(instrument, {}).setdefault("ALL", []).append(dpr_name)

        self.s2.sort()
        self.s3.sort()
        self.all.sort()
        self.s3_l0.sort()
        return self


AUXILIARY_TREE = ProductTree(DATAFILE_METADATA, tree_type="ADF")
PRODUCT_TREE = ProductTree(DATAFILE_METADATA)


def fields_headers(fields: Iterable[str]) -> list[Any]:
    return [FIELDS_DESCRIPTION.get(item, item) for item in fields]


def product_summaries(
    dpr_names: Iterable[str],
    fields: Iterable[str] = ("name", "description"),
) -> list[list[str]]:
    """
    >>> product_summaries(["OLCEFR", "OLCERR"]) # doctest: +ELLIPSIS
    [['OLCEFR', 'Full Resolution ...'], ['OLCERR', 'Reduced Resolution ...']]
    """
    return DATAFILE_METADATA.summary(dpr_names, fields)


def term_summaries(
    names: Iterable[str],
    fields: Iterable[str] = ("name", "description"),
) -> list[list[str]]:
    return TERMS_METADATA.summary(names, fields)
