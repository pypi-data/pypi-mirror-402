"""Module for parsing submodels JSON data."""

import logging

logger = logging.getLogger(__name__)


def get_value_from_semantic_id_by_index(submodel_data: dict, index: int = 0) -> str | None:
    """Retrieve the value from the semantic ID from a submodel JSON dictionary by index.

    :param submodel_data: The submodel data as a dictionary.
    :param index: The index to access if the element is a list or collection, defaults to 0.
    :return: The value of the found submodel element or None if not found.
    """
    if "semanticId" not in submodel_data:
        logger.debug(f"Submodel '{submodel_data}' has no semantic ID")
        return None

    sm_semantic_id = submodel_data.get("semanticId", {})
    if "keys" not in sm_semantic_id or len(sm_semantic_id["keys"]) == 0:
        logger.debug(f"Submodel '{submodel_data}' has no semantic ID keys")
        return None

    keys = sm_semantic_id.get("keys", [])

    if len(keys) < index + 1:
        logger.debug(f"Submodel '{submodel_data}' has no semantic ID key at index {index}")
        return None

    key = keys[index]

    if "value" not in key:
        logger.debug(f"Submodel '{submodel_data}' has no semantic ID value")
        return None

    return key["value"]
