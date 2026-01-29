"""Utility functions for AAS standard parser."""

import json
import logging
from pathlib import Path
from typing import Any

import basyx.aas.adapter.json
from basyx.aas import model

logger = logging.getLogger(__name__)


def create_submodel_from_file(file_path: str) -> model.Submodel:
    """Loads a Submodel structure from a given JSON file and converts it into a model.Submodel object from the python SDK framework.

    :param file_path: Path to the JSON file containing the Submodel structure.
    :return: A model.Submodel object representing the loaded Submodel structure.
    """
    file = Path(file_path)
    if not file.exists():
        raise FileNotFoundError(f"Submodel structure file not found: {file}")

    template_data = {}

    # Load the template JSON file
    with file.open("r", encoding="utf-8") as f:
        template_data = json.load(f)

    # Load the template JSON into a Submodel object
    return _convert_to_object(template_data)


def _convert_to_object(content: dict) -> Any | None:
    """Convert a dictionary to a BaSyx SDK framework object.

    :param content: dictionary to convert
    :return: BaSyx SDK framework object or None
    """
    if not content or len(content) == 0:
        logger.debug("Empty content provided for conversion to object.")
        return None

    try:
        dict_string = json.dumps(content)
        return json.loads(dict_string, cls=basyx.aas.adapter.json.json_deserialization.AASFromJsonDecoder)
    except Exception as e:
        logger.error(f"Decoding error: {e}")
        logger.error(f"In JSON: {content}")
        return None
