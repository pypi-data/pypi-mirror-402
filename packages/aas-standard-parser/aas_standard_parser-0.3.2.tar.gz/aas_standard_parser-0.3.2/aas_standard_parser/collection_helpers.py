from typing import List

from basyx.aas.model import ExternalReference, Key, KeyTypes, NamespaceSet, Reference, SubmodelElement


def find_all_by_semantic_id(parent: NamespaceSet[SubmodelElement], semantic_id_value: str) -> List[SubmodelElement]:
    """Find all SubmodelElements having a specific Semantic ID.

    :param parent: The NamespaceSet to search within.
    :param semantic_id_value: The semantic ID value to search for.
    :return: The found SubmodelElement(s) or an empty list if not found.
    """
    reference: Reference = ExternalReference((Key(type_=KeyTypes.GLOBAL_REFERENCE, value=semantic_id_value),))
    found_elements: list[SubmodelElement] = [element for element in parent if element.semantic_id.__eq__(reference)]
    return found_elements


def find_by_semantic_id(parent: NamespaceSet[SubmodelElement], semantic_id_value: str) -> SubmodelElement | None:
    """Find a SubmodelElement by its semantic ID.

    :param parent: The NamespaceSet to search within.
    :param semantic_id_value: The semantic ID value to search for.
    :return: The first found SubmodelElement, or None if not found.
    @rtype: object
    """
    # create a Reference that acts like the to-be-matched semanticId
    reference: Reference = ExternalReference((Key(type_=KeyTypes.GLOBAL_REFERENCE, value=semantic_id_value),))

    # check if the constructed Reference appears as semanticId of the child elements
    for element in parent:
        if element.semantic_id.__eq__(reference):
            return element
    return None


def find_by_in_semantic_id(parent: NamespaceSet[SubmodelElement], semantic_id_part: str) -> SubmodelElement | None:
    """Find a SubmodelElement by checking if its semantic ID contains the given value.

    :param parent: The NamespaceSet to search within.
    :param semantic_id_value: The semantic ID value to search for.
    :return: The first found SubmodelElement, or None if not found.
    """
    return next((el for el in parent if any(semantic_id_part in key.value for key in el.semantic_id.key)), None)


def find_all_by_in_semantic_id(parent: NamespaceSet[SubmodelElement], semantic_id_part: str) -> SubmodelElement | None:
    """Find a SubmodelElement by checking if its semantic ID contains the given value.

    :param parent: The NamespaceSet to search within.
    :param semantic_id_value: The semantic ID value to search for.
    :return: The first found SubmodelElement, or None if not found.
    """
    return [el for el in parent if any(semantic_id_part in key.value for key in el.semantic_id.key)]


def find_by_id_short(parent: NamespaceSet[SubmodelElement], id_short_value: str) -> SubmodelElement | None:
    """Find a SubmodelElement by its idShort.

    :param parent: The NamespaceSet to search within.
    :param id_short_value: The idShort value to search for.
    :return: The first found SubmodelElement, or None if not found.
    """
    for element in parent:
        if element.id_short == id_short_value:
            return element

    return None


def find_by_supplemental_semantic_id(parent: NamespaceSet[SubmodelElement], semantic_id_value: str) -> SubmodelElement | None:
    """Find a SubmodelElement by its supplemental semantic ID.

    :param parent: The NamespaceSet to search within.
    :param semantic_id_value: The supplemental semantic ID value to search for.
    :return: The first found SubmodelElement, or None if not found.
    """
    for element in parent:
        if contains_supplemental_semantic_id(element, semantic_id_value):
            return element
    return None


def contains_supplemental_semantic_id(element: SubmodelElement, semantic_id_value: str) -> bool:
    """Check if the element contains a specific supplemental semantic ID.

    :param element: The SubmodelElement to check.
    :param semantic_id_value: The supplemental semantic ID value to search for.
    :return: True if the element contains the supplemental semantic ID, False otherwise.
    """
    reference: Reference = ExternalReference((Key(type_=KeyTypes.GLOBAL_REFERENCE, value=semantic_id_value),))
    return element.supplemental_semantic_id.__contains__(reference)
