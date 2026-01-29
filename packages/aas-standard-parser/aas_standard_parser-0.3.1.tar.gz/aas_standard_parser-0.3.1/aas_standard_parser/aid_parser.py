"""This module provides functions to parse AID Submodels and extract MQTT interface descriptions."""

import base64
from typing import Dict, List

from basyx.aas.model import (
    Property,
    SubmodelElement,
    SubmodelElementCollection,
    SubmodelElementList,
)

from aas_standard_parser.collection_helpers import find_all_by_semantic_id, find_by_id_short, find_by_semantic_id


class IProtocolBinding:
    def __init__(self):
        pass


class HttpProtocolBinding(IProtocolBinding):
    def __init__(self, method_name: str, headers: Dict[str, str]):
        super().__init__()
        self.method_name = method_name
        self.headers = headers


class PropertyDetails:
    def __init__(self, href: str, keys: List[str], protocol_binding: IProtocolBinding = None):
        self.href = href
        self.keys = keys
        self.protocol_binding = protocol_binding


class IAuthenticationDetails:
    def __init__(self):
        # TODO: different implementations for different AID versions
        pass


class BasicAuthenticationDetails(IAuthenticationDetails):
    def __init__(self, user: str, password: str):
        self.user = user
        self.password = password
        super().__init__()


class NoAuthenticationDetails(IAuthenticationDetails):
    def __init__(self):
        super().__init__()


class AIDParser:
    def __init__(self):
        pass

    def parse_base(self, aid_interface: SubmodelElementCollection) -> str:
        """Get the base address (EndpointMetadata.base) from a SMC describing an interface in the AID."""

        endpoint_metadata: SubmodelElementCollection | None = find_by_semantic_id(
            aid_interface.value, "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"
        )
        if endpoint_metadata is None:
            raise ValueError(f"'EndpointMetadata' SMC not found in the provided '{aid_interface.id_short}' SMC.")

        base: Property | None = find_by_semantic_id(endpoint_metadata.value, "https://www.w3.org/2019/wot/td#baseURI")
        if base is None:
            raise ValueError("'base' Property not found in 'EndpointMetadata' SMC.")

        return base.value

    def parse_properties(self, aid_interface: SubmodelElementCollection) -> Dict[str, PropertyDetails]:
        """Find all first-level and nested properties in a provided SMC describing one interface in the AID.
        Map each property (either top-level or nested) to the according 'href' attribute.
        Nested properties are further mapped to the hierarchical list of keys
        that are necessary to extract their value from the payload of the interface.

        :param aid_interface: An SMC describing an interface in the AID.
        :return: A dictionary mapping each property (represented by its idShort-path) to PropertyDetails.
        """
        mapping: Dict[str, PropertyDetails] = {}

        interaction_metadata: SubmodelElementCollection | None = find_by_semantic_id(
            aid_interface.value, "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/InteractionMetadata"
        )
        if interaction_metadata is None:
            raise ValueError(f"'InteractionMetadata' SMC not found in the provided '{aid_interface.id_short}' SMC.")

        properties: SubmodelElementCollection | None = find_by_semantic_id(
            interaction_metadata.value, "https://www.w3.org/2019/wot/td#PropertyAffordance"
        )
        if properties is None:
            raise ValueError("'properties' SMC not found in 'InteractionMetadata' SMC.")

        fl_properties: List[SubmodelElement] = find_all_by_semantic_id(
            properties.value, "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/PropertyDefinition"
        )
        if fl_properties is None:
            print(f"WARN: No first-level 'property' SMC not found in 'properties' SMC.")
            return {}

        def traverse_property(
            smc: SubmodelElementCollection,
            parent_path: str,
            href: str,
            key_path: List[str | int],
            is_items=False,
            idx=None,
            is_top_level=False,
            protocol_binding: IProtocolBinding = None,
        ):
            # determine local key only if not top-level
            if not is_top_level:
                if is_items and idx is not None:
                    # is a nested "items" property -> add index to the list of keys
                    local_key = idx
                else:
                    # is a nested "properties" property -> add value of "key" attribute or idShort to list of keys
                    key_prop = find_by_semantic_id(smc.value, "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/key")
                    local_key = key_prop.value if key_prop else smc.id_short
                new_key_path = key_path + [local_key]
            else:
                # TODO: use the key of the first-level property (or its idShort otherwise)
                # is a top-level property
                # key_prop: Property | None = find_by_semantic_id(
                #    smc.value, "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/key"
                # )
                # local_key = key_prop.value if key_prop else smc.id_short
                # new_key_path = [local_key]

                new_key_path = key_path
                # NOTE (Tom Gneuß, 2025-10-20)
                # See GitHub Issue: https://github.com/admin-shell-io/submodel-templates/issues/197
                # First-level properties are allowed to have a "key" attribute - otherwise the idShort path is used.
                # However, complex first-level properties would represent, e.g., the JSON payload (object) itself.
                # This JSON payload does only have keys for nested elements.
                # So, using the key (or idShort) of the first-level property to get the JSON object from the payload
                # is not possible.
                # On the other hand: the first-level property could intentionally be something within the JSON object.
                # In that case, having a "key" (or using the idSort) is entirely valid.
                # How to distinguish both cases?

            # create the idShort path of this property
            full_path = f"{parent_path}.{smc.id_short}"
            # add this property with all its details to the mapping -> href (from top-level parent if this is nested),
            # protocol bindings (from top-level parent if this is nested), list of keys
            mapping[full_path] = PropertyDetails(href, new_key_path, protocol_binding)

            # traverse nested "properties" or "items"
            for nested_sem_id in [
                "https://www.w3.org/2019/wot/json-schema#properties",
                "https://www.w3.org/2019/wot/json-schema#items",
            ]:
                nested_group: SubmodelElementCollection | None = find_by_semantic_id(smc.value, nested_sem_id)
                if nested_group:
                    # attach the name of that SMC ("items" or "properties" or similar) to the key_path
                    full_path += "." + nested_group.id_short

                    # find all nested properties/items by semantic-ID
                    nested_properties: List[SubmodelElement] = find_all_by_semantic_id(
                        nested_group.value, "https://www.w3.org/2019/wot/json-schema#propertyName"
                    )

                    # traverse all nested properties/items recursively
                    for idx, nested in enumerate(nested_properties):
                        if nested_sem_id.endswith("#items"):
                            # for arrays: append index instead of "key" attribute
                            traverse_property(nested, full_path, href, new_key_path, is_items=True, idx=idx)
                        else:
                            traverse_property(nested, full_path, href, new_key_path)

        # process all first-level properties
        for fl_property in fl_properties:  # type: SubmodelElementCollection
            forms: SubmodelElementCollection | None = find_by_semantic_id(fl_property.value, "https://www.w3.org/2019/wot/td#hasForm")
            if forms is None:
                raise ValueError(f"'forms' SMC not found in '{fl_property.id_short}' SMC.")

            href: Property | None = find_by_semantic_id(forms.value, "https://www.w3.org/2019/wot/hypermedia#hasTarget")
            if href is None:
                raise ValueError("'href' Property not found in 'forms' SMC.")

            # get the href value of the first-level property
            href_value = href.value

            # construct the idShort path up to "Interface_.InteractionMetadata.properties"
            # will be used as prefix for the idShort paths of the first-level and nested properties
            idshort_path_prefix = f"{aid_interface.id_short}.{interaction_metadata.id_short}.{properties.id_short}"

            # check which protocol-specific subtype of forms is used
            # there is no clean solution for determining the subtype (e.g., a supplSemId)
            # -> can only be figured out if the specific fields are present
            protocol_binding: IProtocolBinding = None

            # ... try HTTP ("htv_methodName" must be present)
            htv_method_name: Property | None = find_by_semantic_id(forms.value, "https://www.w3.org/2011/http#methodName")
            if htv_method_name is not None:
                protocol_binding: HttpProtocolBinding = HttpProtocolBinding(htv_method_name.value, {})
                htv_headers: SubmodelElementCollection | None = find_by_semantic_id(forms.value, "https://www.w3.org/2011/http#headers")
                if htv_headers is not None:
                    for header in htv_headers.value:  # type: SubmodelElementCollection
                        htv_field_name: Property | None = find_by_semantic_id(header.value, "https://www.w3.org/2011/http#fieldName")
                        htv_field_value: Property | None = find_by_semantic_id(header.value, "https://www.w3.org/2011/http#fieldValue")
                        protocol_binding.headers[htv_field_name.value] = htv_field_value.value

            # TODO: the other protocols
            # ... try Modbus
            # ... try MQTT

            # recursively parse the first-level property and its nested properties (if any)
            traverse_property(
                smc=fl_property,
                parent_path=idshort_path_prefix,
                href=href_value,
                key_path=[],
                is_items=False,
                idx=None,
                is_top_level=True,
                protocol_binding=protocol_binding,
            )

        return mapping

    def parse_security(self, aid_interface: SubmodelElementCollection) -> IAuthenticationDetails:
        """Extract the authentication details (EndpointMetadata.security) from the provided interface in the AID.

        :param aid_interface: An SMC describing an interface in the AID.
        :return: A subtype of IAuthenticationDetails with details depending on the specified authentication method for the interface.
        """
        endpoint_metadata: SubmodelElementCollection | None = find_by_semantic_id(
            aid_interface.value, "https://admin-shell.io/idta/AssetInterfacesDescription/1/0/EndpointMetadata"
        )
        if endpoint_metadata is None:
            raise ValueError(f"'EndpointMetadata' SMC not found in the provided '{aid_interface.id_short}' SMC.")

        security: SubmodelElementList | None = find_by_semantic_id(endpoint_metadata.value, "https://www.w3.org/2019/wot/td#hasSecurityConfiguration")
        if security is None:
            raise ValueError("'security' SML not found in 'EndpointMetadata' SMC.")

        # TODO: resolve the full reference(s)
        # for now, assume there is only one reference to the security in use
        # -> access SML[0]
        # assume that this ReferenceElement points to a security scheme in this very AID SM
        # -> can just use the last key to determine the type of security
        sc_idshort = security.value[0].value.key[-1].value

        # get the securityDefinitions SMC
        security_definitions: SubmodelElementCollection | None = find_by_semantic_id(
            endpoint_metadata.value, "https://www.w3.org/2019/wot/td#definesSecurityScheme"
        )
        if security_definitions is None:
            raise ValueError("'securityDefinitions' SMC not found in 'EndpointMetadata' SMC.")

        # find the security scheme SMC with the same idShort as mentioned in the reference "sc"
        referenced_security: SubmodelElementCollection | None = find_by_id_short(security_definitions.value, sc_idshort)
        if referenced_security is None:
            raise ValueError(f"Referenced security scheme '{sc_idshort}' SMC not found in 'securityDefinitions' SMC")

        # get the name of the security scheme
        scheme: Property | None = find_by_semantic_id(referenced_security.value, "https://www.w3.org/2019/wot/security#SecurityScheme")
        if scheme is None:
            raise ValueError(f"'scheme' Property not found in referenced security scheme '{sc_idshort}' SMC.")

        auth_details: IAuthenticationDetails = None

        match scheme.value:
            case "nosec":
                auth_details = NoAuthenticationDetails()

            case "basic":
                basic_sc_name: Property | None = find_by_semantic_id(referenced_security.value, "https://www.w3.org/2019/wot/security#name")
                if basic_sc_name is None:
                    raise ValueError("'name' Property not found in 'basic_sc' SMC")

                auth_base64 = basic_sc_name.value
                auth_plain = base64.b64decode(auth_base64).decode("utf-8")
                auth_details = BasicAuthenticationDetails(auth_plain.split(":")[0], auth_plain.split(":")[1])

            # TODO: remaining cases
            case "digest":
                pass
            case "bearer":
                pass
            case "psk":
                pass
            case "oauth2":
                pass
            case "apikey":
                pass
            case "auto":
                pass

        return auth_details
