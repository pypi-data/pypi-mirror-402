"""Resource processor for Azure resources.

Applies ID field mappings, filters Azure-managed resources, and populates
`name_sanitized` for Terraform generation.
"""
from typing import List, Dict, Any
import logging
import re

from terraback.scanners.azure_id_field_mappings import (
    get_id_field,
    should_filter_resource,
)
from terraback.terraform_generator.filters import to_terraform_resource_name

def _filter_managed(resources: List[Dict[str, Any]], resource_type: str) -> List[Dict[str, Any]]:
    """Remove Azure-managed resources based on known patterns."""
    filtered: List[Dict[str, Any]] = []
    for r in resources:
        if should_filter_resource(resource_type, r):
            logging.debug(
                "Skipping Azure-managed %s resource: %s",
                resource_type,
                r.get("id") or r.get("name"),
            )
        else:
            filtered.append(r)
    return filtered

def _enhance_names(resources: List[Dict[str, Any]], resource_type: str) -> List[Dict[str, Any]]:
    """Populate name_sanitized field for each resource."""
    id_field = get_id_field(resource_type)
    for resource in resources:
        identifier = resource.get(id_field) or resource.get('id') or resource.get('name')
        if isinstance(identifier, str) and '/' in identifier:
            identifier = identifier.strip('/').split('/')[-1]
        if identifier:
            sanitized = to_terraform_resource_name(str(identifier))
            resource['name_sanitized'] = sanitized
        else:
            resource['name_sanitized'] = f'{resource_type}_resource'
    return resources

def process_resources(resources: List[Dict[str, Any]], resource_type: str, include_all: bool = False) -> List[Dict[str, Any]]:
    """Process Azure resources before template generation."""
    if not include_all:
        try:
            resources = _filter_managed(resources, resource_type)
        except Exception as exc:  # pragma: no cover - defensive
            logging.error(
                "Error filtering managed resources for %s: %s", resource_type, exc
            )
    try:
        resources = _enhance_names(resources, resource_type)
    except Exception as exc:  # pragma: no cover - defensive
        logging.error(
            "Error enhancing names for %s: %s", resource_type, exc
        )
    return resources
