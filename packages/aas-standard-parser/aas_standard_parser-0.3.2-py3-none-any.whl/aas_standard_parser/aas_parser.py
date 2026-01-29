"""Module for parsing AAS."""

import logging

from basyx.aas import model

logger = logging.getLogger(__name__)


def get_submodel_ids(shell: model.AssetAdministrationShell) -> list[str]:
    """Get all IDs from the submodels referenced in the given AAS.

    :param shell: The Asset Administration Shell to extract submodel IDs from.
    :return: A list of submodel IDs referenced in the AAS.
    """
    submodel_ids = []
    for submodel in shell.submodel:
        if len(submodel.key) < 1 or submodel.key[0].type != model.KeyTypes.SUBMODEL:
            logger.warning(f"Submodel reference {submodel} does not start with SUBMODEL key type.")
            continue

        submodel_ids.append(submodel.key[0].value)

    return submodel_ids
