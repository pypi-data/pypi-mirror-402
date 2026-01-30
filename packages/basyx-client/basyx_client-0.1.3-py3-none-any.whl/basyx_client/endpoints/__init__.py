"""Endpoint implementations for AAS Part 2 API v3.x."""

from basyx_client.endpoints.aas_registry import AASRegistryEndpoint
from basyx_client.endpoints.aas_repository import AASRepositoryEndpoint
from basyx_client.endpoints.aasx_server import AASXServerEndpoint
from basyx_client.endpoints.base import BaseEndpoint
from basyx_client.endpoints.concept_descriptions import ConceptDescriptionEndpoint
from basyx_client.endpoints.discovery import DiscoveryEndpoint
from basyx_client.endpoints.submodel_registry import SubmodelRegistryEndpoint
from basyx_client.endpoints.submodel_repository import SubmodelRepositoryEndpoint

__all__ = [
    "AASRegistryEndpoint",
    "AASRepositoryEndpoint",
    "AASXServerEndpoint",
    "BaseEndpoint",
    "ConceptDescriptionEndpoint",
    "DiscoveryEndpoint",
    "SubmodelRegistryEndpoint",
    "SubmodelRepositoryEndpoint",
]
