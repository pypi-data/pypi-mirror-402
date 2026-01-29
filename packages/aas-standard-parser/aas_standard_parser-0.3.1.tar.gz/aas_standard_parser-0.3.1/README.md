# aas-standard-parser

<div align="center">
<!-- change this to your projects logo if you have on.
  If you don't have one it might be worth trying chatgpt dall-e to create one for you...
 -->
<img src="docs/assets/fluid_logo.svg" alt="aas_standard_parser" width=500 />
</div>

---

[![License: MIT](https://img.shields.io/badge/license-MIT-%23f8a602?label=License&labelColor=%23992b2e)](LICENSE)
[![CI](https://github.com/fluid40/aas-standard-parser/actions/workflows/CI.yml/badge.svg?branch=main&cache-bust=1)](https://github.com/fluid40/aas-standard-parser/actions)
[![PyPI version](https://img.shields.io/pypi/v/aas-standard-parser.svg)](https://pypi.org/project/aas-standard-parser/)


This project provides tools for parsing and handling Asset Administration Shell (AAS) standard submodels, with a focus on AID and AIMC submodels. It enables:

- Extraction, interpretation, and mapping of submodel elements and their properties
- Working with references, semantic IDs, and submodel element collections
- Representation and processing of mapping configurations and source-sink relations
- Structured and colored logging, including log file management

These components enable efficient parsing, transformation, and analysis of AAS submodels in Python-based workflows.
> **Note:** Most functions in this project utilize the [python aas sdk framework](https://github.com/aas-core-works/aas-core3.0-python) for parsing and handling AAS submodels, ensuring compatibility with the official AAS data models and structures.
---

## Provided Parsers

- **AID Parser**: Parses AID submodels to extract interface descriptions, properties, and security/authentication details.
- **AIMC Parser**: Parses AIMC submodels to extract and process mapping configurations and source-sink relations.
- **AAS Parser**: Utilities to extract submodel IDs from an Asset Administration Shell.
- **Submodel Parser**: Helpers to retrieve submodel elements by semantic ID or by path within a submodel.

## Helper Modules

- **Collection Helpers**: Functions to search and filter submodel elements by semantic ID, idShort, or supplemental semantic ID within collections.
- **Reference Helpers**: Utilities for working with references, such as constructing idShort paths and extracting values from reference keys.
- **Utilities**: General utility functions, including loading a submodel from a file.

---

## API References
- AID Parser
- AIMC Parser
- [AAS Parser](docs/api_references/api_aas_parser.md)
- [Submodel Parser](docs/api_references/api_submodel_parser.md)
- Collection Helpers
- [Reference Helpers](docs/api_references/api_reference_helpers.md)
- [Utilities](docs/api_references/api_utils.md)

## Resources

🤖 [Releases](http://github.com/fluid40/aas-standard-parser/releases)

📦 [Pypi Packages](https://pypi.org/project/aas-standard-parser/)

📜 [MIT License](LICENSE)
