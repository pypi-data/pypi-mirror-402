"""All pre-commit hooks."""

from checks.model_checks.models_have_contracts import (
    ModelsHaveContracts as ModelsHaveContracts,
)
from checks.model_checks.models_have_descriptions import (
    ModelsHaveDescriptions as ModelsHaveDescriptions,
)
from checks.model_checks.models_have_constraints import (
    ModelsHaveConstraints as ModelsHaveConstraints,
)
from checks.macro_checks.macros_have_descriptions import (
    MacrosHaveDescriptions as MacrosHaveDescriptions,
)
from checks.model_checks.models_have_properties_file import (
    ModelsHavePropertiesFile as ModelsHavePropertiesFile,
)
from checks.macro_checks.macro_arguments_have_descriptions import (
    MacroArgumentsHaveDescriptions as MacroArgumentsHaveDescriptions,
)
from checks.macro_checks.macro_arguments_match_manifest_vs_sql import (
    MacroArgumentsMatchManifestVsSql as MacroArgumentsMatchManifestVsSql,
)
from checks.model_checks.model_columns_have_descriptions import (
    ModelColumnsHaveDescriptions as ModelColumnsHaveDescriptions,
)
from checks.model_checks.models_have_tags import (
    ModelsHaveTags as ModelsHaveTags,
)
from checks.model_checks.model_columns_have_types import (
    ModelColumnsHaveTypes as ModelColumnsHaveTypes,
)
from checks.model_checks.model_column_names_match_manifest_vs_catalog import (
    ModelColumnNamesMatchManifestVsCatalog as ModelColumnNamesMatchManifestVsCatalog,
)
from checks.model_checks.model_column_types_match_manifest_vs_catalog import (
    ModelColumnTypesMatchManifestVsCatalog as ModelColumnTypesMatchManifestVsCatalog,
)
from checks.model_checks.model_column_descriptions_are_consistent import (
    ModelColumnsDescriptionsAreConsistent as ModelColumnsDescriptionsAreConsistent,
)
from checks.model_checks.models_have_data_tests import (
    ModelsHaveDataTests as ModelsHaveDataTests,
)
from checks.model_checks.models_have_unit_tests import (
    ModelsHaveUnitTests as ModelsHaveUnitTests,
)
from checks.source_checks.sources_have_descriptions import (
    SourcesHaveDescriptions as SourcesHaveDescriptions,
)
from checks.source_checks.source_columns_have_descriptions import (
    SourceColumnsHaveDescriptions as SourceColumnsHaveDescriptions,
)
from checks.source_checks.source_column_names_match_manifest_vs_catalog import (
    SourceColumnNamesMatchManifestVsCatalog as SourceColumnNamesMatchManifestVsCatalog,
)
from checks.source_checks.source_columns_have_types import (
    SourceColumnsHaveTypes as SourceColumnsHaveTypes,
)
from checks.source_checks.source_column_types_match_manifest_vs_catalog import (
    SourceColumnTypesMatchManifestVsCatalog as SourceColumnTypesMatchManifestVsCatalog,
)
from checks.source_checks.sources_have_data_tests import (
    SourcesHaveDataTests as SourcesHaveDataTests,
)

ALL_CHECKS = (
    ModelsHaveContracts,
    ModelsHaveDescriptions,
    ModelsHaveConstraints,
    MacrosHaveDescriptions,
    ModelsHavePropertiesFile,
    ModelsHaveDataTests,
    ModelsHaveUnitTests,
    MacroArgumentsHaveDescriptions,
    MacroArgumentsMatchManifestVsSql,
    ModelColumnsHaveDescriptions,
    ModelColumnNamesMatchManifestVsCatalog,
    SourcesHaveDescriptions,
    SourceColumnsHaveDescriptions,
    SourceColumnNamesMatchManifestVsCatalog,
    SourceColumnsHaveTypes,
    SourceColumnTypesMatchManifestVsCatalog,
    SourcesHaveDataTests,
    ModelColumnTypesMatchManifestVsCatalog,
    ModelColumnsHaveTypes,
    ModelColumnsDescriptionsAreConsistent,
    ModelsHaveTags,
)
ALL_CHECKS_MAP = {check.check_name: check for check in ALL_CHECKS}
