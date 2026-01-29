# Copyright 2024 ACRI-ST
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import logging
import sys
from typing import Any, Callable, Hashable

import click
import deepdiff
import numpy as np
import xarray
import xarray as xr
from deepdiff.helper import SetOrdered
from xarray import DataTree

from sentineltoolbox.logging_utils import setup_compare_loggers
from sentineltoolbox.product_type_utils import guess_product_type
from sentineltoolbox.readers.coding import encode_cf_datetime
from sentineltoolbox.readers.datatree_subset import (
    drop_empty_vars,
    filter_datatree,
    filter_flags,
)
from sentineltoolbox.readers.open_datatree import open_datatree
from sentineltoolbox.typedefs import XarrayData
from sentineltoolbox.verification.compare import (
    _drop_mismatched_variables,
    _get_failed_formatted_string_flags,
    _get_failed_formatted_string_vars,
    _get_passed_formatted_string_flags,
    bitwise_statistics,
    compute_confusion_matrix_for_dataarray,
    parse_cmp_vars,
    product_exists,
    sort_datatree,
    variables_statistics,
)

categories = (
    "dictionary_item_added",
    "dictionary_item_removed",
    "values_changed",
    "type_changes",
    "iterable_item_added",
    "iterable_item_removed",
    "set_item_added",
    "set_item_removed",
)

category_aliases = {
    "dictionary_item_added": "Items Added",
    "dictionary_item_removed": "Items Removed",
    "values_changed": "Values Changed",
    "type_changes": "Type Changes",
    "iterable_item_added": "Iterable Items Added",
    "iterable_item_removed": "Iterable Items Removed",
    "set_item_added": "Set Items Added",
    "set_item_removed": "Set Items Removed",
}


def _format_deep_diff_result(category: str, item: Any) -> str:
    path = ""
    for name in item.path(output_format="list"):
        if isinstance(name, int):
            path += f"[{name}]"
        elif name is None:
            pass
        else:
            path += f"/{name}"
    if category == "iterable_item_added":
        msg = f"{path} == {item.t2!r}"
    elif category == "iterable_item_removed":
        msg = f"{path} == {item.t1!r}"
    elif category == "dictionary_item_added":
        msg = f"{path} == {item.t2!r}"
    elif category == "dictionary_item_removed":
        msg = f"{path} == {item.t1!r}"
    elif category == "type_changes":
        msg = f"{path} == {item.t1!r} ({type(item.t1).__name__}) -> {item.t2!r} ({type(item.t2).__name__})"
    elif category == "values_changed":
        msg = f"{path} == {item.t1!r} -> {item.t2!r}"
    elif category == "set_item_added":
        msg = f"{path}.add({item.t2!r})"
    elif category == "set_item_removed":
        msg = f"{path}.remove({item.t1!r})"
    else:
        msg = f"{path} == {item.t1!r} -> {item.t2!r}"
    return msg


def compare_products(
    reference: str,
    actual: str,
    cmp_vars: str | None = None,
    cmp_grps: str | None = None,
    verbose: bool = False,
    info: bool = False,
    relative: bool = False,
    absolute: bool = False,
    threshold: float = 0.01,
    threshold_packed: float = 1.5,
    threshold_nb_outliers: float = 0.01,
    threshold_coverage: float = 0.01,
    structure: bool = True,
    data: bool = True,
    flags: bool = True,
    coords: bool = True,
    encoding: bool = True,
    encoding_compressor: bool = True,
    encoding_preferred_chunks: bool = True,
    encoding_chunks: bool = True,
    chunks: bool = True,
    secret: str | None = None,
    loggers: list[logging.Logger] | None = None,
    output_format: str = "std",
    **kwargs: Any,
) -> tuple[DataTree | None, DataTree | None, float | None, list[float] | None] | RuntimeError:
    """Compare two products Zarr or SAFE.

    Parameters
    ----------
    reference: Path
        Reference product path
    actual: Path
        New product path
    verbose: bool
        2-level of verbosity (INFO or DEBUG)
    info: bool
        Display statistics even if PASSED
    relative: bool
        Compute relative error (default for non-packed variables)
    absolute: bool
        Compute absolute error (default for packed variables)
    threshold: float
        Maximum allowed threshold defining the PASSED/FAILED result.
        In relative mode, this is a float between 0 and 1 (e.g. 0.01 for 1%).
        In absolute mode, packed variables use a configurable threshold of scale_factor * threshold_packed.
    threshold_packed: float
        Packed variables threshold for absolute mode (threshold = scale_factor * threshold_packed)
    threshold_nb_outliers: float
        Maximum allowed relative number of outliers as a float between 0 and 1 (e.g. 0.01 for 1% outliers).
    threshold_coverage: float
        Maximum allowed valid coverage relative difference as a float between 0 and 1 (e.g. 0.01 for 1%)
    structure: bool
        Compare product structure and metadata like Zarr metadata/attributes
    data: bool
        Compare variables data
    flags: bool
        Compare flags/masks variables
    output_format: str, optional
        Output format
        default="std"
    logger: logging.Logger, optional
        Logger for general comparison messages. If None, uses "sentineltoolbox.compare"
    passed_logger: logging.Logger, optional
        Logger for success messages. If None, uses "sentineltoolbox.compare.success"
    failed_logger: logging.Logger, optional
        Logger for failure messages. If None, uses "sentineltoolbox.compare.fail"

    Examples
    --------
    Simple usage with default loggers (output to stderr):

    >>> compare_products("ref.zarr", "actual.zarr") # doctest: +SKIP

    For output redirection to a file:

    >>> from sentineltoolbox.logging_utils import setup_compare_loggers
    >>> with open("report.log", "w") as f:
    ...     main, passed, failed, bare = setup_compare_loggers(stream=f)
    ...     compare_products("ref.zarr", "actual.zarr", # doctest: +SKIP
    ...                     logger=main, passed_logger=passed, failed_logger=failed) # doctest: +SKIP

    For custom logger configuration:

    >>> from sentineltoolbox.logging_utils import setup_compare_loggers
    >>> main, passed, failed, bare = setup_compare_loggers(verbose=True)
    >>> compare_products("ref.zarr", "actual.zarr", # doctest: +SKIP
    ...                 logger=main, passed_logger=passed, failed_logger=failed) # doctest: +SKIP
    """
    # Initialize loggers - use provided loggers or create default ones
    if loggers is None:
        logger, passed_logger, failed_logger, bare_logger = setup_compare_loggers(verbose=verbose)
    else:
        logger, passed_logger, failed_logger, bare_logger = loggers

    # Check input products
    if not product_exists(reference, secret=secret):
        logger.error(f"{reference} cannot be found.")
        raise FileNotFoundError(reference)
    if not product_exists(actual, secret=secret):
        logger.error(f"{actual} cannot be found.")
        raise FileNotFoundError(actual)
    logger.info(
        f"Compare the new product {actual} to the reference product {reference}",
    )

    # Check if specific variables
    if cmp_vars:
        list_ref_new_vars = parse_cmp_vars(reference, actual, cmp_vars)
    else:
        list_ref_new_vars = []
    if cmp_grps:
        list_ref_new_grps = parse_cmp_vars(reference, actual, cmp_grps)
    else:
        list_ref_new_grps = []

    kwargs["decode_times"] = False
    if secret:
        kwargs["secret_alias"] = secret
    if coords:
        kwargs["decode_coords"] = False
    # Open reference product
    dt_ref = open_datatree(reference, **kwargs)
    dt_ref.name = "ref"
    logger.debug(dt_ref)

    # Open new product
    dt_new = open_datatree(actual, **kwargs)
    dt_new.name = "new"
    logger.debug(dt_new)

    err, err_flags, score, score_flag = compare_product_datatrees(
        dt_ref,
        dt_new,
        list_ref_new_vars,
        list_ref_new_grps,
        info,
        relative,
        absolute,
        threshold,
        threshold_packed,
        threshold_nb_outliers,
        threshold_coverage,
        structure,
        data,
        flags,
        encoding,
        encoding_compressor,
        encoding_preferred_chunks,
        encoding_chunks,
        chunks,
        output_format,
        logger=logger,
        passed_logger=passed_logger,
        failed_logger=failed_logger,
        bare_logger=bare_logger,
    )

    return err, err_flags, score, score_flag


def _generate_rst_table(
    results: dict[str, list[Any]],
    threshold_nb_outliers: float,
    threshold_coverage: float,
    relative: bool,
    logger: logging.Logger,
) -> None:
    """
    Generate an RST list table with variable comparison statistics.

    Parameters
    ----------
    results : dict
        Dictionary containing variable statistics from variables_statistics
    threshold_nb_outliers : float
        Maximum allowed relative number of outliers
    threshold_coverage : float
        Maximum allowed valid coverage relative difference
    relative : bool
        Whether relative or absolute error was computed
    """
    logger.info("Variable Comparison Results")
    logger.info("=" * 27 + "\n")

    # Add CSS styling for colors - more Sphinx-compatible approach
    logger.info(".. raw:: html\n")
    logger.info("   <style>")
    logger.info("   .status-passed { color: #28a745; font-weight: bold; }")
    logger.info("   .status-failed { color: #dc3545; font-weight: bold; }")
    logger.info("   </style>\n")
    logger.info(".. role:: status-passed\n")
    logger.info(".. role:: status-failed\n")

    # List table header
    logger.info(".. list-table:: Variable Comparison Statistics")
    logger.info("   :widths: 20 8 12 12 12 12 12")
    logger.info("   :header-rows: 1\n")
    logger.info("   * - Variable Name")
    logger.info("     - Status")
    logger.info("     - Outliers %")
    logger.info("     - Min Error")
    logger.info("     - Max Error")
    logger.info("     - Mean Error")
    logger.info("     - Median Error")

    # Table rows
    for name, val in results.items():
        if name.endswith("spatial_ref") or name.endswith("band"):
            continue

        # Check if the number of outliers is within the allowed threshold
        outliers_ratio = val[7] / val[8] if val[8] != 0 else 0  # outliers / valid pixels
        # Check if the valid coverage difference is within the allowed threshold
        coverage_diff_ratio = val[10] / val[9]  # valid pixels / total pixels

        # Determine PASSED/FAILED status with color formatting
        if (outliers_ratio <= threshold_nb_outliers) and (np.abs(coverage_diff_ratio) <= threshold_coverage):
            status = ":status-passed:`PASSED`"
        else:
            status = ":status-failed:`FAILED`"

        # Calculate percentage of outliers
        outliers_percent = outliers_ratio * 100

        # Format error values based on relative/absolute mode
        if relative:
            min_error = f"{val[0]*100:8.4f}%"
            max_error = f"{val[1]*100:8.4f}%"
            mean_error = f"{val[2]*100:8.4f}%"
            median_error = f"{val[4]*100:8.4f}%"
        else:
            min_error = f"{val[0]:9.6f}"
            max_error = f"{val[1]:9.6f}"
            mean_error = f"{val[2]:9.6f}"
            median_error = f"{val[4]:9.6f}"

        # Write table row
        logger.info(f"   * - {name}")
        logger.info(f"     - {status}")
        logger.info(f"     - {outliers_percent:10.3f}%")
        logger.info(f"     - {min_error}")
        logger.info(f"     - {max_error}")
        logger.info(f"     - {mean_error}")
        logger.info(f"     - {median_error}")

        logger.info("")


def _generate_rst_table_flags(
    res: dict[str, xr.Dataset],
    threshold_nb_outliers: float,
    logger: logging.Logger,
) -> None:
    """
    Generate an RST list table with flag comparison statistics and append to existing file.

    Parameters
    ----------
    res : dict
        Dictionary containing flag statistics from bitwise_statistics
    threshold_nb_outliers : float
        Maximum allowed relative number of outliers
    """
    logger.info("\n\nFlag Comparison Results")
    logger.info("=" * 23 + "\n")

    # List table header for flags
    logger.info(".. list-table:: Flag Comparison Statistics")
    logger.info("   :widths: 25 8 12 12 12")
    logger.info("   :header-rows: 1\n")
    logger.info("   * - Flag Name")
    logger.info("     - Status")
    logger.info("     - Different %")
    logger.info("     - Equal Count")
    logger.info("     - Different Count")

    # Table rows for flags
    eps = 100.0 * threshold_nb_outliers
    for name, ds in res.items():
        for bit in ds.index.data:
            # Determine PASSED/FAILED status
            if ds.different_percentage[bit] > eps:
                status = ":status-failed:`FAILED`"
            else:
                status = ":status-passed:`PASSED`"

            # Write table row
            logger.info(f"   * - {name} (bit {bit})")
            logger.info(f"     - {status}")
            logger.info(f"     - {ds.different_percentage[bit]:10.3f}%")
            logger.info(f"     - {ds.equal_count[bit]:10d}")
            logger.info(f"     - {ds.different_count[bit]:10d}")

    logger.info("")


# Global state to track XML structure
_xml_state = {"testsuites_open": False, "xml_declaration_logged": False}


def _log_xml_declaration(logger: logging.Logger) -> None:
    """Log XML declaration if not already logged."""
    if not _xml_state["xml_declaration_logged"]:
        logger.info('<?xml version="1.0" encoding="UTF-8"?>')
        _xml_state["xml_declaration_logged"] = True


def _log_testsuites_start(logger: logging.Logger) -> None:
    """Log testsuites opening tag if not already open."""
    if not _xml_state["testsuites_open"]:
        _log_xml_declaration(logger)
        logger.info("<testsuites>")
        _xml_state["testsuites_open"] = True


def _log_testsuites_end(logger: logging.Logger) -> None:
    """Log testsuites closing tag."""
    if _xml_state["testsuites_open"]:
        logger.info("</testsuites>")
        _xml_state["testsuites_open"] = False


def _close_junit_xml(logger: logging.Logger) -> None:
    """Close the JUnit XML structure by logging the closing testsuites tag."""
    _log_testsuites_end(logger)


def _generate_junit_xml(
    results: dict[str, list[Any]],
    threshold_nb_outliers: float,
    threshold_coverage: float,
    relative: bool,
    logger: logging.Logger,
    test_suite_name: str = "Product Comparison",
) -> None:
    """
    Generate JUnit XML output with variable comparison statistics using logger.

    Parameters
    ----------
    results : dict
        Dictionary containing variable statistics from variables_statistics
    threshold_nb_outliers : float
        Maximum allowed relative number of outliers
    threshold_coverage : float
        Maximum allowed valid coverage relative difference
    relative : bool
        Whether relative or absolute error was computed
    logger : logging.Logger
        Logger for XML output
    test_suite_name : str
        Name of the test suite
    """
    from datetime import datetime

    # Start testsuites if not already open
    _log_testsuites_start(logger)

    # Count tests
    test_count = len([name for name in results.keys() if not (name.endswith("spatial_ref") or name.endswith("band"))])

    # Log testsuite opening
    logger.info(f'  <testsuite name="{test_suite_name}" tests="{test_count}" timestamp="{datetime.now().isoformat()}">')

    # Count passed and failed tests
    passed_count = 0
    failed_count = 0

    # Create test cases for each variable
    for name, val in results.items():
        if name.endswith("spatial_ref") or name.endswith("band"):
            continue

        # Check if the number of outliers is within the allowed threshold
        outliers_ratio = val[7] / val[8] if val[8] != 0 else 0  # outliers / valid pixels
        # Check if the valid coverage difference is within the allowed threshold
        coverage_diff_ratio = val[10] / val[9]  # valid pixels / total pixels

        # Determine PASSED/FAILED status
        if (outliers_ratio <= threshold_nb_outliers) and (np.abs(coverage_diff_ratio) <= threshold_coverage):
            test_passed = True
            passed_count += 1
        else:
            test_passed = False
            failed_count += 1

        # Calculate statistics for the message
        outliers_percent = outliers_ratio * 100

        # Format error values based on relative/absolute mode
        if relative:
            min_error = f"{val[0]*100:8.4f}%"
            max_error = f"{val[1]*100:8.4f}%"
            mean_error = f"{val[2]*100:8.4f}%"
            median_error = f"{val[4]*100:8.4f}%"
        else:
            min_error = f"{val[0]:9.6f}"
            max_error = f"{val[1]:9.6f}"
            mean_error = f"{val[2]:9.6f}"
            median_error = f"{val[4]:9.6f}"

        # Create detailed message
        message = (
            f"Variable: {name}\n"
            f"Status: {'PASSED' if test_passed else 'FAILED'}\n"
            f"Outliers: {outliers_percent:.3f}% (threshold: {threshold_nb_outliers*100:.1f}%)\n"
            f"Coverage diff: {coverage_diff_ratio*100:+.3f}% (threshold: {threshold_coverage*100:.1f}%)\n"
            f"Min Error: {min_error}\n"
            f"Max Error: {max_error}\n"
            f"Mean Error: {mean_error}\n"
            f"Median Error: {median_error}"
        )

        # Log testcase
        testcase_name = f"variable_comparison_{name.replace('/', '_').replace(' ', '_')}"
        logger.info(f'    <testcase name="{testcase_name}" classname="ProductComparison">')

        if not test_passed:
            # Log failure element
            logger.info(f'      <failure message="Variable {name} failed comparison">')
            logger.info(f"        {message}")
            logger.info("      </failure>")
        else:
            # Log system-out element for passed tests
            logger.info("      <system-out>")
            logger.info(f"        {message}")
            logger.info("      </system-out>")

        logger.info("    </testcase>")

    # Log testsuite closing with attributes
    logger.info("  </testsuite>")


def _generate_junit_xml_flags(
    res: dict[str, xr.Dataset],
    threshold_nb_outliers: float,
    logger: logging.Logger,
    test_suite_name: str = "Flag Comparison",
) -> None:
    """
    Generate JUnit XML output with flag comparison statistics using logger.

    Parameters
    ----------
    res : dict
        Dictionary containing flag statistics from bitwise_statistics
    threshold_nb_outliers : float
        Maximum allowed relative number of outliers
    logger : logging.Logger
        Logger for XML output
    test_suite_name : str
        Name of the test suite
    """
    from datetime import datetime

    # Start testsuites if not already open
    _log_testsuites_start(logger)

    # Count total flag tests
    total_tests = sum(len(ds.index.data) for ds in res.values())

    # Log testsuite opening
    logger.info(
        f'  <testsuite name="{test_suite_name}" tests="{total_tests}" timestamp="{datetime.now().isoformat()}">',
    )

    # Count passed and failed tests
    passed_count = 0
    failed_count = 0

    # Create test cases for each flag
    eps = 100.0 * threshold_nb_outliers
    for name, ds in res.items():
        for bit in ds.index.data:
            # Determine PASSED/FAILED status
            if ds.different_percentage[bit] > eps:
                test_passed = False
                failed_count += 1
            else:
                test_passed = True
                passed_count += 1

            # Create detailed message
            message = (
                f"Flag: {name} (bit {bit})\n"
                f"Status: {'PASSED' if test_passed else 'FAILED'}\n"
                f"Different percentage: {ds.different_percentage[bit]:.3f}% (threshold: {eps:.1f}%)\n"
                f"Equal count: {ds.equal_count[bit].item()}\n"
                f"Different count: {ds.different_count[bit].item()}\n"
                f"Equal percentage: {ds.equal_percentage[bit]:.3f}%"
            )

            # Log testcase
            testcase_name = f"flag_comparison_{name.replace('/', '_').replace(' ', '_')}_bit_{bit}"
            logger.info(f'    <testcase name="{testcase_name}" classname="FlagComparison">')

            if not test_passed:
                # Log failure element
                logger.info(f'      <failure message="Flag {name} (bit {bit}) failed comparison">')
                logger.info(f"        {message}")
                logger.info("      </failure>")
            else:
                # Log system-out element for passed tests
                logger.info("      <system-out>")
                logger.info(f"        {message}")
                logger.info("      </system-out>")

            logger.info("    </testcase>")

    # Log testsuite closing
    logger.info("  </testsuite>")


def compare_product_datatrees(
    dt_ref: xarray.DataTree,
    dt_new: xarray.DataTree,
    list_ref_new_vars: list[tuple[str, str]] | None = None,
    list_ref_new_grps: list[tuple[str, str]] | None = None,
    info: bool = False,
    relative: bool = False,
    absolute: bool = False,
    threshold: float = 0.01,
    threshold_packed: float = 1.5,
    threshold_nb_outliers: float = 0.01,
    threshold_coverage: float = 0.01,
    structure: bool = True,
    data: bool = True,
    flags: bool = True,
    encoding: bool = True,
    encoding_compressor: bool = True,
    encoding_preferred_chunks: bool = True,
    encoding_chunks: bool = True,
    chunks: bool = True,
    output_format: str = "std",
    **kwargs: Any,
) -> tuple[DataTree | None, DataTree | None, float | None, list[float] | None]:
    """
    Compares two datatrees or datasets and checks for structural, metadata, and data-level
    differences. It calculates statistics on variable and flag data if requested, ensuring
    comparison based on defined thresholds.

    :param dt_ref: Reference datatree or dataset used for comparison.
    :param dt_new: New datatree or dataset to compare with the reference.
    :param list_ref_new_vars: Optional mapping of variable names in the reference and new datatrees.
    :param list_ref_new_grps: Optional mapping of group names in the reference and new datatrees.
    :param info: If True, includes detailed information logs about the comparison process.
    :param relative: Enables relative difference computation for variable data.
    :param absolute: Enables absolute difference computation for variable data.
    :param threshold: Acceptable difference threshold for variable data comparison.
    :param threshold_nb_outliers: Maximum allowed ratio of outliers for a variable to pass verification.
    :param threshold_coverage: Maximum allowed coverage difference ratio to pass verification.
    :param threshold_packed: Packed variables threshold for absolute mode (threshold = scale_factor * threshold_packed)
    :param structure: If True, verifies structure and metadata consistency between datatrees.
    :param data: If True, performs variable data comparison.
    :param flags: If True, compares flags representation between datatrees.
    :param output_format: Output format default="std"
    :param kwargs: Additional keyword arguments such as custom loggers.
    :return: A tuple containing error information, flag difference statistics, variable comparison
             score, and flags comparison scores, or raises a RuntimeError if comparison fails.

    :raises RuntimeError: Occurs if structural checks or initial compatibility checks fail.
    """
    if list_ref_new_vars is None:
        list_ref_new_vars = []
    if list_ref_new_grps is None:
        list_ref_new_grps = []

    logger = kwargs.get("logger", logging.getLogger("sentineltoolbox.compare"))
    passed_logger = kwargs.get("passed_logger", logging.getLogger("sentineltoolbox.compare.success"))
    failed_logger = kwargs.get("failed_logger", logging.getLogger("sentineltoolbox.compare.fail"))
    bare_logger = kwargs.get("bare_logger", logging.getLogger("sentineltoolbox.compare.bare"))

    # Sort datatree
    dt_ref = sort_datatree(dt_ref)
    dt_new = sort_datatree(dt_new)

    # Get product type
    eopf_type = guess_product_type(dt_ref)

    # Filter datatree
    if list_ref_new_vars:
        dt_ref = filter_datatree(
            dt_ref,
            [var[0] for var in list_ref_new_vars],
            type="variables",
        )
        dt_new = filter_datatree(
            dt_new,
            [var[1] for var in list_ref_new_vars],
            type="variables",
        )
    if list_ref_new_grps:
        dt_ref = filter_datatree(
            dt_ref,
            [var[0] for var in list_ref_new_grps],
            type="groups",
        )
        dt_new = filter_datatree(
            dt_new,
            [var[1] for var in list_ref_new_grps],
            type="groups",
        )

    # Ensure time is encoded as integer.
    dt_ref = encode_cf_datetime(dt_ref)
    dt_new = encode_cf_datetime(dt_new)

    # Filter out zero-size variables (occurs in FRP products for instance)
    dt_ref = drop_empty_vars(dt_ref)
    dt_new = drop_empty_vars(dt_new)

    # Check if datatrees are isomorphic
    if not dt_new.isomorphic(dt_ref):
        logger.error("Reference and new products are not isomorphic")
        logger.error("Comparison fails")
        raise RuntimeError

    # Unify chunks within each input datatrees
    unified = dt_ref.map_over_datasets(lambda ds: ds.unify_chunks())
    if isinstance(unified, DataTree):
        dt_ref = unified
    else:
        raise ValueError(
            "Error when unifying chunks over datasets",
            "within the reference product resulting in tuple of DataTree",
        )
    unified = dt_new.map_over_datasets(lambda ds: ds.unify_chunks())
    if isinstance(unified, DataTree):
        dt_new = unified
    else:
        raise ValueError(
            "Error when unifying chunks over datasets",
            "within the new product resulting in tuple of DataTree",
        )

    # Compare structure and metadata if requested
    skip_comparison: bool = False
    if structure:
        logger.info("-- Verification of structure and metadata")
        skip_comparison = compare_datatrees_structure(
            dt_ref,
            dt_new,
            passed_logger,
            failed_logger,
            check_subset_only=kwargs.get("check_subset_only"),
            chunks=chunks,
            encoding=encoding,
            encoding_compressor=encoding_compressor,
            encoding_preferred_chunks=encoding_preferred_chunks,
            encoding_chunks=encoding_chunks,
        )
        if skip_comparison:
            message = "Reference and new products have fatal structure differences"
            logger.error(message)
            logger.error("Comparison fails")

    # Variable statistics
    score: float | None = 0
    err = None
    if data and not skip_comparison:
        results, err = variables_statistics(dt_new, dt_ref, relative, absolute, threshold, threshold_packed)

        logger.info("-- Verification of variables data")
        match output_format:
            case "std":
                for name, val in results.items():
                    if name.endswith("spatial_ref") or name.endswith("band"):
                        continue
                    # Check if the number of outliers is within the allowed threshold
                    outliers_ratio = val[7] / val[8] if val[8] != 0 else 0  # outliers / valid pixels
                    # Check if the valid coverage difference is within the allowed threshold
                    coverage_diff_ratio = val[10] / val[9]  # valid pixels / total pixels
                    if (outliers_ratio <= threshold_nb_outliers) and (
                        np.abs(coverage_diff_ratio) <= threshold_coverage
                    ):
                        if info:
                            passed_logger.info(
                                _get_failed_formatted_string_vars(
                                    name,
                                    val,
                                    threshold_nb_outliers,
                                    threshold_coverage,
                                ),
                            )
                        else:
                            passed_logger.info(f"{name}")
                    else:
                        failed_logger.info(
                            _get_failed_formatted_string_vars(
                                name,
                                val,
                                threshold_nb_outliers,
                                threshold_coverage,
                            ),
                        )

            case "rst":
                _generate_rst_table(results, threshold_nb_outliers, threshold_coverage, relative, bare_logger)
                logger.info("RST comparison table written to output.rst")

            case "junit":
                _generate_junit_xml(results, threshold_nb_outliers, threshold_coverage, relative, bare_logger)
                logger.info("JUnit XML test report generated")

        # Global scoring:
        if relative:
            score = 100.0 - np.abs(np.nanmedian([np.abs((res[2] + res[4]) * 0.5) for res in results.values()]) * 100)
            logger.debug(
                """Metrics is: 100% - |median_over_variables(0.5 * (
                                    (1 / npix) *sum_npix(err_rel[p]) + median_pix(err_rel[p])
                                    ) * 100|

                        with err_rel[p] = (val[p] - ref[p]) / ref[p]
                        """,
            )
            logger.info(f"   Global scoring for non-flag variables = {score:20.12f}%")
        else:
            score = None

    score_flag: list[float] = []
    err_flags = None
    if flags and not skip_comparison:
        # Flags statistics
        flags_ref = filter_flags(dt_ref)
        flags_new = filter_flags(dt_new)

        res: dict[str, xr.Dataset] = {}

        # Patch for S2 L2
        # Attributes for reference product are not correct so that filtering flags is ineffective
        # TODO: for exclusive flags (detected on attributes=flag_values), use the confusion matrix
        # instead of the bitwise statistics which is not correct
        try:
            if eopf_type in [
                "S02MSIL1C",
                "S02MSIL2A",
            ]:
                patch_s2l2 = True
            else:
                patch_s2l2 = False
        except KeyError:
            patch_s2l2 = False

        if patch_s2l2:
            score_flag_scl = compute_confusion_matrix_for_dataarray(
                dt_ref.conditions.mask.l2a_classification.r20m.scl,
                dt_new.conditions.mask.l2a_classification.r20m.scl,
                normalize="true",
            )
            score_flag.append(score_flag_scl)
            err_flags = None
            logger.info(f"   Score for scene classification is = {score_flag[0]}")

        else:
            with xr.set_options(keep_attrs=True):
                try:
                    err_flags = flags_ref ^ flags_new
                except xr.AlignmentError:
                    dropped_vars = _drop_mismatched_variables(flags_new, flags_ref)
                    if dropped_vars:
                        logger.warning("Dropped mismatched flag variables: %s", ",".join(dropped_vars))
                    err_flags = flags_ref ^ flags_new
                except TypeError:
                    logger.warning("Is there anyone here?")
                    pass
            if err_flags is not None:
                res = bitwise_statistics(err_flags)
                eps = 100.0 * threshold_nb_outliers
                logger.info("-- Verification of flags")
                match output_format:
                    case "std":
                        for name, ds in res.items():
                            for bit in ds.index.data:
                                if ds.different_percentage[bit] > eps:
                                    failed_logger.info(
                                        _get_failed_formatted_string_flags(name, ds, bit, threshold_nb_outliers),
                                    )
                                else:
                                    passed_logger.info(
                                        _get_passed_formatted_string_flags(name, ds, bit),
                                    )
                    case "rst":
                        _generate_rst_table_flags(res, threshold_nb_outliers, bare_logger)
                        logger.info("Flag comparison table appended to output.rst")

                    case "junit":
                        _generate_junit_xml_flags(res, threshold_nb_outliers, bare_logger)
                        logger.info("Flag comparison test cases generated")

            # Global scoring for flags
            # score_flag: list[float] = []
            for name, ds in res.items():
                score_var: float = 0
                sum_weight: float = 0
                for bit in ds.index.data:
                    weight = ds.equal_count.data[bit] + ds.different_count.data[bit]
                    sum_weight += weight
                    score_var = score_var + ds.equal_percentage.data[bit] * weight
                score_var /= sum_weight
                score_flag.append(score_var)

            logger.info(f"   Scores for flag variables are = {score_flag}")
            logger.info(f"   Global scores for flag variables is = {np.nanmedian(score_flag)   :20.12f}")

    logger.info("Exiting compare")

    # Close JUnit XML structure if it was opened
    if output_format == "junit":
        _close_junit_xml(bare_logger)

    return err, err_flags, score, score_flag


# def get_subsets(reference, current, **kwargs) -> reference, current
ApplySubsetFunction = Callable[[str, XarrayData, XarrayData, Any], tuple[XarrayData, XarrayData, bool]]


def compare_datatrees_structure(
    dt_ref: DataTree,
    dt_new: DataTree,
    passed_logger: logging.Logger,
    failed_logger: logging.Logger,
    check_subset_only: ApplySubsetFunction | None = None,
    **kwargs: Any,
) -> bool:
    """
    Compare the structure of two DataTree objects except variables data, log differences and
    return a flag to skip variables data comparison when fatal differences are found
    (e.g. dimensions or shape are different for at least one variable).

    Traverses through all nodes in the reference DataTree and compares them with corresponding
    nodes in the new DataTree. For each node, it compares dataset and variable objects fields,
    attributes, encoding, etc... and logs whether they are identical or different.

    Args:
        dt_ref: Reference DataTree to compare against
        dt_new: New DataTree being compared
        passed_logger: Logger for recording successful comparisons
        failed_logger: Logger for recording failed comparisons or differences

    Returns:
        True if variables data comparison should be skipped, False otherwise.
    """
    skip_data_comparison = False
    skip_data_comparison_message = ""

    for ref_node in dt_ref.subtree:
        ds_ref_path = ref_node.path

        # Check if the node exists in the new product
        try:
            new_node = dt_new[ds_ref_path]
        except KeyError:
            failed_logger.info(f"{ds_ref_path}: Node exists in reference but not in new product")
            continue

        ref_ds = ref_node.to_dataset()
        new_ds = new_node.to_dataset()

        # Compare dataset fields
        for field, ref_obj, new_obj in get_fields_for_comparisons(ref_ds, new_ds, **kwargs):
            ds_path_str = f"[{ds_ref_path}][{field}]"
            diff = deepdiff_compare_objects(ref_obj, new_obj, prefix=ds_path_str + ": ")
            if diff:
                failed_logger.info(f"{ds_path_str} fields are not identical")
                for msg in diff:
                    failed_logger.info(msg)

        # Compare variables fields
        for ref_var in ref_ds.values():
            try:
                new_var = new_ds[ref_var.name]
            except KeyError:
                msg = f"{ref_var.name} is not in reference DataTree"
                skip_data_comparison_message += msg + "\n"
                failed_logger.info(msg)
                skip_data_comparison = True
            else:
                var_ref_path = f"{ds_ref_path}/{ref_var.name}"

                for field, ref_obj, new_obj in get_fields_for_comparisons(ref_var, new_var, **kwargs):
                    var_path_str = f"[{var_ref_path}][{field}]"
                    diff = deepdiff_compare_objects(ref_obj, new_obj, prefix=var_path_str + ": ")
                    if diff:
                        # Skip data comparison if variable dimensions or shape are different because
                        # it is not possible to compare the data in this case.
                        skip_data_comparison_message = ""
                        if field in ("dims", "shape"):
                            skip_data_comparison = True
                            skip_data_comparison_message = (
                                " (WARNING: variable dimensions or shape are different, "
                                "all variables data comparison will be skipped)"
                            )
                        failed_logger.info(
                            f"{var_path_str} fields are not identical{skip_data_comparison_message}:",
                        )
                        for msg in diff:
                            failed_logger.info(msg)

    return skip_data_comparison


def get_fields_for_comparisons(
    ref_obj: xr.Dataset | xr.DataArray,
    new_obj: xr.Dataset | xr.DataArray,
    **kwargs: Any,
) -> tuple[Any, ...]:
    """
    Extract fields to compare from two xarray objects (Dataset or DataArray).

    Args:
        ref_obj: Reference object (Dataset or DataArray)
        new_obj: Object to compare against the reference (must be same type as ref_obj)

    Returns:
        A tuple of tuples containing field names to compare, with their values from both objects
    """
    if not isinstance(ref_obj, type(new_obj)):
        raise TypeError(f"Objects must be of the same type, got {type(ref_obj)} and {type(new_obj)}")

    ref_obj_attrs = ref_obj.attrs
    new_obj_attrs = new_obj.attrs

    # Common fields for both Dataset and DataArray
    chunks = kwargs.get("chunks", True)
    encoding = kwargs.get("encoding", True)
    encoding_compressor = kwargs.get("encoding_compressor", True)
    encoding_preferred_chunks = kwargs.get("encoding_preferred_chunks", True)
    encoding_chunks = kwargs.get("encoding_chunks", True)

    remove_from_encoding = ["source"]
    if not encoding:
        remove_from_encoding.extend(["compressor", "preferred_chunks", "chunks"])
    if not encoding_compressor:
        remove_from_encoding.append("compressor")
    if not encoding_preferred_chunks:
        remove_from_encoding.append("preferred_chunks")
    if not encoding_chunks:
        remove_from_encoding.append("chunks")

    common_fields: list[tuple[str, Any, Any]] = [
        ("attrs", ref_obj_attrs, new_obj_attrs),
        ("chunks", ref_obj.chunks if chunks else None, new_obj.chunks if chunks else None),
        (
            "chunksizes",
            ref_obj.chunksizes if chunks else None,
            new_obj.chunksizes if chunks else None,
        ),
        ("coords", list(ref_obj.coords), list(new_obj.coords)),
        (
            "encoding",
            dict_remove_keys(ref_obj.encoding, remove_from_encoding),
            dict_remove_keys(new_obj.encoding, remove_from_encoding),
        ),
        ("nbytes", ref_obj.nbytes, new_obj.nbytes),
        ("sizes", ref_obj.sizes, new_obj.sizes),
    ]

    ds_fields: list[tuple[str, Any, Any]]
    if isinstance(ref_obj, xr.Dataset):
        # Dataset specific fields
        ds_fields = [
            ("data_vars", list(ref_obj.data_vars), list(new_obj.data_vars)),
        ]
        fields = common_fields + ds_fields
    else:  # DataArray
        # DataArray specific fields
        da_fields = [
            ("dims", ref_obj.dims, new_obj.dims),
            ("dtype", ref_obj.dtype, new_obj.dtype),
            ("name", ref_obj.name, new_obj.name),
            ("shape", ref_obj.shape, new_obj.shape),
        ]
        fields = common_fields + da_fields

    return tuple(fields)


def dict_remove_keys(d: dict[Hashable, Any], keys: list[str]) -> dict[Hashable, Any]:
    """
    Remove specified keys from a dictionary.

    Args:
        d: Input dictionary
        keys: List of keys to remove from the dictionary

    Returns:
        A new dictionary with the specified keys removed
    """
    return {k: v for k, v in d.items() if k not in keys}


def deepdiff_compare_objects(ref_obj: Any, new_obj: Any, **kwargs: Any) -> list[str]:
    """
    Compare two objects using DeepDiff and return a formatted representation of the differences.

    Args:
        ref_obj: Reference object
        new_obj: Object to compare against the reference

    Returns:
        A formatted string describing the differences between objects if any differences exist,
        None otherwise
    """
    ddiff = deepdiff.DeepDiff(ref_obj, new_obj, threshold_to_diff_deeper=0, view="tree")
    diff_messages = []
    if ddiff:
        # return pprint.pformat(ddiff, width=120)
        # Below an alternative using DeepDiff pretty print, but it doesn't show (for example) new coords name.
        # return ddiff.pretty()
        for category in categories:
            items = ddiff.get(category)
            if isinstance(items, dict):
                for path, change in items.items():
                    diff_messages.append(f"[{category}] {path}: {change}")
            elif isinstance(items, SetOrdered):
                for item in items:
                    path = ""
                    for name in item.path(output_format="list"):
                        if isinstance(name, int):
                            path += f"[{name}]"
                        elif name is None:
                            pass
                        else:
                            path += f"/{name}"
                    msg = _format_deep_diff_result(
                        category,
                        item,
                    )
                    before_msg = kwargs.get("prefix", "")
                    diff_messages.append(f"[{category}]{before_msg}{msg}")
    return diff_messages


@click.command()
@click.argument("reference", type=str, nargs=1, required=True)
@click.argument("actual", type=str, nargs=1, required=True)
@click.option(
    "--cmp-vars",
    type=str,
    help="Compare only specific variables, defined as: path/to/var_ref:path/to/var_new,... ",
)
@click.option(
    "--cmp-grps",
    type=str,
    help="Compare only specific groups, defined as: path/to/grp_ref:path/to/grp_new,... ",
)
@click.option(
    "-v",
    "--verbose",
    is_flag=True,
    default=False,
    show_default=True,
    help="increased verbosity",
)
@click.option(
    "--info",
    is_flag=True,
    default=False,
    show_default=True,
    help="always display statistics even if PASSED",
)
# We do not use the https://click.palletsprojects.com/en/stable/options/#feature-switches
# because no error is automatically raised if both --relative and --absolute options are used.
@click.option(
    "--relative",
    is_flag=True,
    default=False,
    show_default=True,
    help="Compute relative error (default for non-packed variables)",
    cls=click.Option,
    is_eager=True,
)
@click.option(
    "--absolute",
    is_flag=True,
    default=False,
    show_default=True,
    help="Compute absolute error (default for packed variables)",
    cls=click.Option,
    is_eager=True,
)
@click.option(
    "--threshold",
    required=False,
    type=float,
    default=0.01,
    show_default=True,
    help="Maximum allowed threshold defining the PASSED/FAILED result. "
    "In relative mode, this is a float between 0 and 1 (e.g. 0.01 for 1%). "
    "In absolute mode, packed variables use a configurable threshold of scale_factor * threshold_packed.",
)
@click.option(
    "--threshold-packed",
    required=False,
    type=float,
    default=1.5,
    show_default=True,
    help="Packed variables threshold for absolute mode (threshold = scale_factor * threshold_packed)",
)
@click.option(
    "--threshold-nb-outliers",
    required=False,
    type=float,
    default=0.01,
    show_default=True,
    help="Maximum allowed relative number of outliers as a float between 0 and 1 (e.g. 0.01 for 1% outliers).",
)
@click.option(
    "--threshold-coverage",
    required=False,
    type=float,
    default=0.01,
    show_default=True,
    help="Maximum allowed valid coverage relative difference as a float between 0 and 1 (e.g. 0.01 for 1%)",
)
@click.option(
    "--structure/--no-structure",
    required=False,
    default=True,
    show_default=True,
    help="Compare products structure and metadata like Zarr metadata/attributes",
)
@click.option(
    "--data/--no-data",
    required=False,
    default=True,
    show_default=True,
    help="Compare variables data",
)
@click.option(
    "--flags/--no-flags",
    required=False,
    default=True,
    show_default=True,
    help="Compare flags/masks variables",
)
@click.option(
    "--coords/--no-coords",
    required=False,
    default=True,
    show_default=True,
    help="Account for coordinates differences",
)
@click.option(
    "--encoding/--no-encoding",
    required=False,
    default=None,
    show_default=True,
    help="Ignore encoding differences",
)
@click.option(
    "--encoding-compressor/--no-encoding-compressor",
    required=False,
    default=None,
    show_default=True,
    help="Ignore encoding compressor differences",
)
@click.option(
    "--encoding-preferred-chunks/--no-encoding-preferred-chunks",
    required=False,
    default=None,
    show_default=True,
    help="Ignore encoding preferred chunks differences",
)
@click.option(
    "--encoding-chunks/--no-encoding-chunks",
    required=False,
    default=None,
    show_default=True,
    help="Ignore encoding chunks differences",
)
@click.option(
    "--chunks/--no-chunks",
    required=False,
    default=None,
    show_default=True,
    help="Ignore chunks differences",
)
@click.option(
    "--strict/--no-strict",
    required=False,
    default=True,
    show_default=True,
    help="Strict mode: Comprehensive comparison of all variables/metadata. "
    "If no strict, some metadata are ignored (chunks sizes, encoding/compression parameters...)",
)
@click.option(
    "-s",
    "--secret",
    required=False,
    show_default=True,
    help="Secret alias if available extracted from env. variable S3_SECRETS_JSON_BASE64 or in /home/.eopf/secrets.json",
)
@click.option("-o", "--output", required=False, help="output file")
@click.option(
    "--output-format",
    required=False,
    show_default=True,
    help="Output format",
    type=click.Choice(["rst", "junit", "std"]),
    default="std",
)
def compare(
    reference: str,
    actual: str,
    cmp_vars: str,
    cmp_grps: str,
    verbose: bool,
    info: bool,
    relative: bool,
    absolute: bool,
    threshold: float,
    threshold_packed: float,
    threshold_nb_outliers: float,
    threshold_coverage: float,
    structure: bool,
    data: bool,
    flags: bool,
    coords: bool,
    encoding: bool,
    encoding_compressor: bool,
    encoding_preferred_chunks: bool,
    encoding_chunks: bool,
    chunks: bool,
    strict: bool,
    secret: str,
    output: str,
    output_format: str,
    **kwargs: Any,
) -> None:
    """CLI tool to compare two products Zarr or SAFE."""
    if relative and absolute:
        raise click.UsageError("Options --relative and --absolute are mutually exclusive.")

    if strict:
        if encoding is None:
            encoding = True
        if encoding_compressor is None:
            encoding_compressor = True
        if encoding_preferred_chunks is None:
            encoding_preferred_chunks = True
        if encoding_chunks is None:
            encoding_chunks = True
        if chunks is None:
            chunks = True
    else:
        if encoding is None:
            encoding = True
        if encoding_compressor is None:
            encoding_compressor = True
        if encoding_preferred_chunks is None:
            encoding_preferred_chunks = False
        if encoding_chunks is None:
            encoding_chunks = False
        if chunks is None:
            chunks = False

    if output_format is not None and output_format != "std":
        level = logging.NOTSET
        verbose = False
    else:
        level = logging.INFO

    # Determine output stream (None means use sys.stderr default)
    stream = None
    if output:
        stream = open(output, mode="w")

    try:
        # Configure loggers for CLI usage
        # Setup configured loggers
        main_logger, passed_logger, failed_logger, bare_logger = setup_compare_loggers(
            stream=stream,
            level=level,
            verbose=verbose,
        )

        # Call compare_products with configured loggers
        compare_products(
            reference,
            actual,
            cmp_vars=cmp_vars,
            cmp_grps=cmp_grps,
            verbose=verbose,
            info=info,
            relative=relative,
            absolute=absolute,
            threshold=threshold,
            threshold_packed=threshold_packed,
            threshold_nb_outliers=threshold_nb_outliers,
            threshold_coverage=threshold_coverage,
            structure=structure,
            data=data,
            flags=flags,
            coords=coords,
            encoding=encoding,
            encoding_compressor=encoding_compressor,
            encoding_preferred_chunks=encoding_preferred_chunks,
            encoding_chunks=encoding_chunks,
            chunks=chunks,
            secret=secret,
            loggers=[main_logger, passed_logger, failed_logger, bare_logger],
            output_format=output_format,
            **kwargs,
        )
    except FileNotFoundError:
        if output and stream:
            stream.close()
        sys.exit(1)
    finally:
        # Close output file if opened
        if output and stream:
            stream.close()
