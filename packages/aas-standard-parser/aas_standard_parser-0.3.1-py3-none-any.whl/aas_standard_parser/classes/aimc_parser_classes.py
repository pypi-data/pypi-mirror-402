import json
from dataclasses import field

import basyx.aas.adapter.json
from basyx.aas import model


class ReferenceProperties:
    """Class representing properties of a reference in the mapping configuration."""

    reference: model.ExternalReference = field(metadata={"description": "Reference to the property in the submodel."})
    submodel_id: str = field(metadata={"description": "Identifier of the submodel used by the reference."})
    property_name: str = field(metadata={"description": "Name of the mapped property."})
    parent_path: list[str] = field(metadata={"description": "List of idShorts representing the parent path of the reference."})


class SourceSinkRelation:
    """Class representing a source-sink relation in the mapping configuration."""

    source_properties: ReferenceProperties = field(metadata={"description": "Properties of the source reference."})
    sink_properties: ReferenceProperties = field(metadata={"description": "Properties of the sink reference."})

    def source_reference_as_dict(self) -> dict:
        """Convert the source reference to a dictionary.

        :return: The source reference as a dictionary.
        """
        dict_string = json.dumps(self.source_properties.reference, cls=basyx.aas.adapter.json.AASToJsonEncoder)
        dict_string = dict_string.replace("GlobalReference", "Submodel").replace("FragmentReference", "SubmodelElementCollection")
        return json.loads(dict_string)

    def sink_reference_as_dict(self) -> dict:
        """Convert the sink reference to a dictionary.

        :return: The sink reference as a dictionary.
        """
        return json.loads(json.dumps(self.sink_properties.reference, cls=basyx.aas.adapter.json.AASToJsonEncoder))


class MappingConfiguration:
    """Class representing a mapping configuration."""

    interface_reference: model.ReferenceElement = field(metadata={"description": "Reference to the interface in the AID submodel."})
    aid_submodel_id: str = field(metadata={"description": "Identifier of the AID submodel used by the interface reference."})
    source_sink_relations: list[SourceSinkRelation] = field(metadata={"description": "List of source-sink relations in the mapping configuration."})


class MappingConfigurations:
    """Class representing mapping configurations from AIMC submodel."""

    configurations: list[MappingConfiguration] = field(metadata={"description": "List of mapping configurations."})
    aid_submodel_ids: list[str] = field(metadata={"description": "List of AID submodel IDs used in the mapping configurations."})
