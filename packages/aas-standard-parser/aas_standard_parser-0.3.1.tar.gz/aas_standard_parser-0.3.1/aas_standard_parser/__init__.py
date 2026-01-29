"""AAS Standard parser Package."""

import importlib.metadata
from datetime import datetime, timezone

from aas_standard_parser import (
    aas_parser,
    aid_parser,
    aimc_parser,
    collection_helpers,
    reference_helpers,
    submodel_json_parser,
    submodel_parser,
    utils,
)
from aas_standard_parser.aid_parser import AIDParser
from aas_standard_parser.version_check import check_for_update

__copyright__ = f"Copyright (C) {datetime.now(tz=timezone.utc).year} Fluid 4.0. All rights reserved."
__author__ = "Daniel Klein, Celina Adelhardt, Tom Gneuß"

try:
    __license__ = "MIT"
    __version__ = importlib.metadata.version(__name__)
except importlib.metadata.PackageNotFoundError:
    __version__ = "0.0.0-dev"

__project__ = "aas-standard-parser"
__package__ = "aas-standard-parser"


check_for_update()

__all__ = [
    "AIDParser",
    "aas_parser",
    "aid_parser",
    "aimc_parser",
    "collection_helpers",
    "reference_helpers",
    "submodel_json_parser",
    "submodel_parser",
    "utils",
]
