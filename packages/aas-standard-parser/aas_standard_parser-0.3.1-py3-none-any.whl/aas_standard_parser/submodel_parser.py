"""Module for parsing submodels."""

import logging

from basyx.aas import model

logger = logging.getLogger(__name__)


def get_submodel_element_by_id_short_path(submodel: model.Submodel, id_short_path: str) -> model.SubmodelElement:
    """Retrieve a specific submodel element from the submodel at a specific idShort path.

    :param submodel: The submodel to search within.
    :param id_short_path: IdShort path to the submodel element (dot-separated), e.g., "Element1.Element2[0].Element3".
    :return: The found submodel element or None if not found.
    """
    # Split the path by '.' and traverse the structure
    parts = id_short_path.split(".")
    current_elements = submodel.submodel_element
    part_index = 0
    for part in parts:
        part_index += 1
        # Handle indexed access like "Element[0]" for SubmodelElementLists
        if "[" in part and "]" in part:
            # Split SubmodelElementList name and index
            base, idx = part[:-1].split("[")
            idx = int(idx)
            # Find the SubmodelElementList in the current elements
            submodel_element = next((el for el in current_elements if el.id_short == base), None)

            if not submodel_element or not (isinstance(submodel_element, (model.SubmodelElementList, model.SubmodelElementCollection))):
                logger.debug(f"Submodel element '{base}' not found or is not a collection/list in current {current_elements}.")
                return None

            # Check if index is within range
            if idx >= len(submodel_element.value):
                logger.debug(f"Index '{idx}' out of range for element '{base}' with length {len(submodel_element.value)}.")
                return None

            # get the element by its index from SubmodelElementList
            submodel_element = submodel_element.value[idx]

        else:
            # Find the SubmodelElement in the current SubmodelElementCollection
            submodel_element = next((el for el in current_elements if el.id_short == part), None)

        if not submodel_element:
            logger.debug(f"Submodel element '{part}' not found in current {current_elements}.")
            return None

        # If we've reached the last part, return the found element
        if part_index == len(parts):
            return submodel_element

        # If the found element is a collection or list, continue traversing
        if isinstance(submodel_element, (model.SubmodelElementCollection, model.SubmodelElementList)):
            current_elements = submodel_element.value
        else:
            return submodel_element

    return submodel_element
