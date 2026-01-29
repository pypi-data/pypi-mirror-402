import logging
import re
from typing import Any

LOGGER = logging.getLogger("sentineltoolbox")

STAC_PRODUCT_TYPE = "product:type"
STAC_VERSION = "1.1.0"


RE_ADF = "(S[0-9]+|[0-9]+)?_?(?:[A-Z_]_)?(?:ADF_)?([A-Z][A-Z_0-9]{4})"
RE_GENERIC = "(S[0-9]+|[0-9]+)?([A-Z][A-Z_0-9]{4,5})"  # keep {5,6} for case like "SAMPL" -> ADF, "SAMPLE" -> product


def create_dpr_type_from_semantic(
    ptype: str,
    is_adf: bool | None = None,
    num: str | int | None = None,
) -> str | list[str]:
    if is_adf is None:
        is_adf = "ADF_" in ptype or len(ptype) == 5
    if "ADF" in ptype:
        m = re.match(RE_ADF, ptype)
    else:
        m = re.match(RE_GENERIC, ptype)
    if m:
        extracted_num = m.group(1)
        if num is None:
            num = extracted_num if extracted_num else "00"
        else:
            num = str(num)
        semantic = m.group(2)
        num_str = num.lstrip("S").zfill(2)
    elif len(ptype) in (5, 6):
        semantic = ptype
        num_str = "00"
    else:
        return []
    if is_adf:
        canonical_ptype = f"S{num_str}_ADF_{semantic}"
    else:
        canonical_ptype = f"S{num_str}{semantic}"
    return canonical_ptype


def to_canonical_type(ptype: str, is_adf: bool | None = None, num: int | None = None, **kwargs: Any) -> str | list[str]:
    """
    Converts a given ptype into a canonical ptype based on certain rules.

    This function uses the `to_dpr_ptype` function from the `DATAFILE_METADATA`
    to first attempt to map the given `ptype` to a canonical version. If no
    canonical version is found and the `is_adf` flag is True, it prepends
    "SXX_ADF_" to the semantic component of the `ptype`. Otherwise, it only
    extracts the semantic component of the `ptype`.

    Example where product:type is recognized and so constellation is known (S02, S03, ...)

    >>> to_canonical_type("OLCEFR")
    'S03OLCEFR'
    >>> to_canonical_type("OLINS")
    'S03_ADF_OLINS'

    Example where product:type is not recognized. Constellation cannot be determined and is replaced by "SXX"
    >>> to_canonical_type("ABCDEF")
    'S00ABCDEF'
    >>> to_canonical_type("ABCDE")
    'S00_ADF_ABCDE'
    >>> to_canonical_type("ABCDE", num=3)
    'S03_ADF_ABCDE'

    Not that you can force to generate and adf or a product with is_adf arguments

    :param ptype: The ptype string that needs to be converted into its canonical form.
    :type ptype: str
    :param is_adf: force the `ptype` to be an ADF (is_adf=True) or a product (is_adf=False) Defaults to None: autodetect
    :type is_adf: bool | None
    :return: The canonical ptype derived from the input `ptype`.
    :rtype: str
    """
    from sentineltoolbox.resources.data import custom_db_datafiles

    db_metadata = custom_db_datafiles(**kwargs)

    # search in db. Required for obsolete names
    canonical_ptype = db_metadata.to_dpr_ptype(ptype, is_adf=is_adf, num=num)
    if canonical_ptype:
        # found in db, check if db item and is_adf flag correspond if is_adf is forced
        if is_adf is not None and isinstance(canonical_ptype, str):
            db_is_adf = db_metadata.get_metadata(canonical_ptype).get("adf_or_product") == "ADF"
            if db_is_adf != is_adf:
                # is_adf is forced and do not match DB
                LOGGER.info(
                    f"to_canonical_type forced ({is_adf=}) but {ptype} corresponds to is_adf={db_is_adf} in db."
                    f"Please check everything is correct",
                )
                canonical_ptype = None  # set to None to force new generation of canonical_type based on user parameters

    if not canonical_ptype:
        # not found in db, create dpr_name from scratch
        if isinstance(ptype, list):
            canonical_ptype = [create_dpr_type_from_semantic(p, is_adf, num) for p in ptype]
        else:
            canonical_ptype = create_dpr_type_from_semantic(ptype, is_adf, num)

    return canonical_ptype
