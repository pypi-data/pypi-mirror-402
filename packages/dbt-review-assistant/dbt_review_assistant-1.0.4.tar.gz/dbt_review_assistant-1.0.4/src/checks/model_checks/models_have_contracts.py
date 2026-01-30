"""Check if models have contracts enforced."""

from utils.check_failure_messages import object_missing_attribute_message
from utils.check_abc import ManifestCheck
from utils.artifact_data import get_models_from_manifest


def model_has_contract_enforced(model: dict) -> bool:
    """Check if a model has a contract enforced.

    Args:
        model: model dictionary from the dbt manifest.json

    Returns:
        True if the model has an enforced contract
    """
    return bool(model.get("config", {}).get("contract", {}).get("enforced"))


class ModelsHaveContracts(ManifestCheck):
    """Check if models have contracts enforced.

    Attributes:
        check_name: name of the check
        additional_arguments: arguments required in addition to the global arguments
    """

    check_name: str = "models-have-contracts"
    additional_arguments = [
        "include_materializations",
        "include_tags",
        "include_packages",
        "include_node_paths",
        "exclude_materializations",
        "exclude_tags",
        "exclude_packages",
        "exclude_node_paths",
    ]

    def perform_check(self) -> None:
        """Execute the check logic."""
        self.failures = {
            node["unique_id"]
            for node in get_models_from_manifest(
                manifest_dir=self.args.manifest_dir,
                filter_conditions=self.filter_conditions,
            )
            if not model_has_contract_enforced(node)
            # Ephemeral models cannot have contracts
            and node.get("config", {}).get("materialized") != "ephemeral"
        }

    @property
    def failure_message(self) -> str:
        """Compile a failure log message."""
        return object_missing_attribute_message(
            missing_attributes=self.failures,
            object_type="model",
            attribute_type="contract",
        )


if __name__ == "__main__":
    ModelsHaveContracts()
