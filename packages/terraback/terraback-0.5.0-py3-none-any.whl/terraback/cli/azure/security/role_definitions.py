from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result

logger = get_logger(__name__)


class RoleDefinitionsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = AuthorizationManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_role_definitions(self, custom_only: bool = True) -> List[Dict[str, Any]]:
        """List role definitions in the subscription."""
        role_definitions = []
        scope = f"/subscriptions/{self.subscription_id}"
        
        try:
            # List all role definitions at subscription scope
            for role_def in self.client.role_definitions.list(scope):
                # Filter to custom roles only by default
                if custom_only and role_def.role_type != "CustomRole":
                    continue
                    
                try:
                    role_definitions.append(self._process_role_definition(role_def))
                except Exception as e:
                    logger.error(f"Error processing role definition {role_def.role_name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing role definitions: {str(e)}")
            
        return role_definitions

    def _process_role_definition(self, role_def) -> Dict[str, Any]:
        """Process a single role definition resource."""
        # Use the role definition ID as the basis for the name
        role_def_name = role_def.id.split('/')[-1]
        
        role_definition_data = {
            "id": role_def.id,
            "name": role_def.role_name.replace(' ', '_').replace('-', '_').lower(),
            "type": "azure_role_definition",
            "resource_type": "azure_role_definition",
            "properties": {
                "name": role_def_name,  # Use the GUID from the ID
                "scope": f"/subscriptions/{self.subscription_id}",
                "description": role_def.description or "",
            }
        }
        
        # Process permissions
        if role_def.permissions:
            permissions = []
            for perm in role_def.permissions:
                permission_data = {
                    "actions": list(perm.actions) if perm.actions else []
                }
                if perm.not_actions:
                    permission_data["not_actions"] = list(perm.not_actions)
                if hasattr(perm, 'data_actions') and perm.data_actions:
                    permission_data["data_actions"] = list(perm.data_actions)
                if hasattr(perm, 'not_data_actions') and perm.not_data_actions:
                    permission_data["not_data_actions"] = list(perm.not_data_actions)
                permissions.append(permission_data)
            role_definition_data["properties"]["permissions"] = permissions
        
        # Add assignable scopes
        if role_def.assignable_scopes:
            role_definition_data["properties"]["assignable_scopes"] = list(role_def.assignable_scopes)
        
        # Add metadata
        role_definition_data["properties"]["role_name"] = role_def.role_name
        role_definition_data["properties"]["role_type"] = role_def.role_type
            
        return role_definition_data

    def scan(self, custom_only: bool = True) -> List[Dict[str, Any]]:
        """Main scan method to retrieve role definitions."""
        logger.info(f"Scanning role definitions in subscription {self.subscription_id}")
        return self.list_role_definitions(custom_only)


def scan_role_definitions(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None,
    custom_only: bool = True
) -> List[Dict[str, Any]]:
    """Scan role definitions in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = RoleDefinitionsScanner(credentials, subscription_id)
    role_definitions = scanner.scan(custom_only)
    
    if role_definitions:    # Process resources before generation
        role_definitions = process_resources(role_definitions, "azure_role_definition")
    

        # Generate Terraform files
        generate_tf_auto(role_definitions, "azure_role_definition", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(role_definitions)} Azure Role Definitions")
        
        # Generate import file
        generate_imports_file(
            "azure_role_definition",
            role_definitions,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return role_definitions
