import logging

import aas_standard_parser.aimc_parser as aimc_parser
from aas_standard_parser.utils import create_submodel_from_file

logger = logging.getLogger(__name__)


def start() -> None:
    logger.info("Demo process started.")

    aimc_submodel = create_submodel_from_file("tests/test_data/aimc_submodel.json")

    tmp = aimc_parser.parse_mapping_configurations(aimc_submodel)

    tmp2 = tmp.configurations[0].source_sink_relations[0].get_source_parent_property_group_name()

    logger.info("Demo process finished.")
