"""Methods for compiling formatted failure console messages."""

from typing import Collection, Any

from prettytable import PrettyTable, HRuleStyle

PRETTY_TABLE_KWARGS: dict[str, Any] = {
    "max_table_width": 80,
    "hrules": HRuleStyle.ALL,
    "min_width": 28,
    "border": True,
}


def macro_argument_mismatch_manifest_vs_sql(
    sql_args: Collection[str], manifest_args: Collection[str]
) -> str:
    """Summarise check failures when macro arguments mismatch between manifest and SQL code.

    Args:
        sql_args: Collection of macro argument names from the SQL code
        manifest_args: Collection of macro argument names from the manifest file

    Returns:
        A string summarising the check failures
    """
    sql_args_set: set[str] = set(sql_args)
    manifest_args_set: set[str] = set(manifest_args)
    table = PrettyTable(**PRETTY_TABLE_KWARGS)
    table.field_names = ["SQL code macro arguments", "Manifest macro arguments"]
    for arg in sorted(sql_args_set - manifest_args_set):
        table.add_row([arg, "MISSING"])
    for arg in sorted(manifest_args_set - sql_args_set):
        table.add_row(["MISSING", arg])
    return (
        "There are mismatches between the macro arguments found in the manifest.json"
        f" and those defined in macro SQL code:\n{table}"
    )


def manifest_vs_catalog_column_name_mismatch_message(
    manifest_columns: Collection[str], catalog_columns: Collection[str]
):
    """Summarise check failures when manifest column names mismatch between manifest and catalog.

    Args::
        manifest_columns: Collection of column names from the manifest file
        catalog_columns:  Collection of column names from the catalog file

    Returns:
        A string summarising the check failures
    """
    manifest_columns_set: set[str] = set(manifest_columns)
    catalog_columns_set: set[str] = set(catalog_columns)
    table = PrettyTable(**PRETTY_TABLE_KWARGS)
    table.field_names = ["Catalog columns", "Manifest columns"]
    for arg in sorted(catalog_columns_set - manifest_columns_set):
        table.add_row([arg, "MISSING"])
    for arg in sorted(manifest_columns_set - catalog_columns_set):
        table.add_row(["MISSING", arg])
    return (
        f"There are mismatches between the column names found in"
        f" manifest.json vs. catalog.json:\n{table}"
    )


def manifest_vs_catalog_column_type_mismatch_message(
    manifest_columns: dict[str, str], catalog_columns: dict[str, str]
):
    """Summarise check failures when manifest column types mismatch between manifest and catalog.

    Args::
        manifest_columns: Mapping of column names to column types from the manifest file
        catalog_columns:  Mapping of column names to column types from the catalog file

    Returns:
        A string summarising the check failures
    """
    table = PrettyTable(**PRETTY_TABLE_KWARGS)
    table.field_names = ["Catalog columns", "Manifest columns"]
    all_keys = set(manifest_columns.keys()).union(set(catalog_columns.keys()))
    for key in sorted(all_keys):
        if (
            catalog_columns.get(key)
            and manifest_columns.get(key)
            and (catalog_columns.get(key) != manifest_columns.get(key))
        ):
            table.add_row(
                [
                    f"{key}: {catalog_columns.get(key)}",
                    f"{key}: {manifest_columns.get(key)}",
                ]
            )
        elif catalog_columns.get(key) and not manifest_columns.get(key):
            table.add_row([f"{key}: {catalog_columns.get(key)}", "MISSING"])
        elif manifest_columns.get(key) and not catalog_columns.get(key):
            table.add_row(
                [
                    "MISSING",
                    f"{key}: {manifest_columns.get(key)}",
                ]
            )
    return (
        f"There are mismatches between the column types found in"
        f" manifest.json vs. catalog.json:\n{table}"
    )


def object_missing_attribute_message(
    missing_attributes: Collection[str],
    object_type: str,
    attribute_type: str,
    expected_values: set[str] | None = None,
) -> str:
    """Summarise check failures when object attributes are missing in the manifest.

    Args:
        missing_attributes: Collection of missing attributes
        object_type: Type of object being checked
        attribute_type: Type of attribute being checked for
        expected_values: Optional, set of expected values for the attribute

    Returns:
        string summarising the check failures
    """
    join_string = "\n - "
    return (
        f"The following {object_type}s do not have{' the required ' if expected_values else ''}"
        f" {attribute_type}s{' (' + ', '.join(sorted(expected_values)) + ')' if expected_values else ''}:"
        f"\n - {join_string.join(sorted(missing_attributes))}"
    )


def inconsistent_column_descriptions_message(
    descriptions: dict[str, list[dict[str, str]]],
) -> str:
    """Summarise check failures when column descriptions are inconsistent across different models.

    Args:
        descriptions: dict mapping column names to a list of occurrence instance dicts,
        including the name of the model and the description in that model

    Returns:
        string summarising the check failures
    """
    table = PrettyTable(**PRETTY_TABLE_KWARGS)
    table.field_names = ["Column", "Model", "Descriptions"]
    for column_name, column_instances in sorted(
        descriptions.items(), key=lambda x: x[0]
    ):
        for column_instance in column_instances:
            table.add_row(
                [
                    column_name,
                    column_instance["model"],
                    column_instance["description"],
                ]
            )
    return f"There are inconsistent descriptions for the following model column descriptions:\n{table}"


def object_missing_values_from_set_message(
    objects: dict[str, set[str]],
    object_type: str,
    attribute_type: str,
    must_have_all_from: set[str] | None = None,
    must_have_any_from: set[str] | None = None,
) -> str:
    """Summarise check failures when an object is missing attribute values from a set.

    Args:
        objects: objects which have failed the check, with the set of actual values
        object_type: Type of object being checked
        attribute_type: Type of attribute being checked for
        must_have_all_from: the set of values which the object must have all values from
        must_have_any_from: the set of values which the object must at least one value from

    Returns:
        string summarising the check failures
    """
    table = PrettyTable(**PRETTY_TABLE_KWARGS)
    field_names = [
        object_type.capitalize(),
    ]
    if must_have_all_from or must_have_any_from:
        field_names.append(f"Actual {attribute_type}s")
    if must_have_all_from:
        field_names.append("Require all from")
    if must_have_any_from:
        field_names.append("Require any from")
    table.field_names = field_names
    for object_name, actual_values in objects.items():
        row = [object_name]
        if must_have_all_from or must_have_any_from:
            row.append(str(sorted(actual_values)) if actual_values else "")
        if must_have_all_from:
            row.append(str(sorted(must_have_all_from)) if must_have_all_from else "")
        if must_have_any_from:
            row.append(str(sorted(must_have_any_from)) if must_have_any_from else "")
        table.add_row(row)
    return (
        f"The following {object_type}s do not have{' the required' if must_have_all_from or must_have_any_from else ''}"
        f" {attribute_type}s:\n{table}"
    )
