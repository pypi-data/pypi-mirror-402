from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.authorization import AuthorizationManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
import uuid

logger = get_logger(__name__)


class RoleAssignmentsScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = AuthorizationManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_role_assignments(self) -> List[Dict[str, Any]]:
        """List all role assignments in the subscription."""
        role_assignments = []
        
        try:
            # List all role assignments at subscription scope
            for assignment in self.client.role_assignments.list_for_subscription():
                try:
                    role_assignments.append(self._process_role_assignment(assignment))
                except Exception as e:
                    logger.error(f"Error processing role assignment {assignment.id}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing role assignments: {str(e)}")
            
        return role_assignments

    def _process_role_assignment(self, assignment) -> Dict[str, Any]:
        """Process a single role assignment resource."""
        # Generate a deterministic name from the assignment ID
        assignment_name = assignment.id.split('/')[-1]
        
        role_assignment_data = {
            "id": assignment.id,
            "name": assignment_name,
            "type": "azure_role_assignment",
            "resource_type": "azure_role_assignment",
            "properties": {
                "scope": assignment.scope,
                "role_definition_id": assignment.role_definition_id,
                "principal_id": assignment.principal_id,
            }
        }
        
        # Add optional properties
        if hasattr(assignment, 'principal_type') and assignment.principal_type:
            role_assignment_data["properties"]["principal_type"] = assignment.principal_type
            
        if hasattr(assignment, 'condition') and assignment.condition:
            role_assignment_data["properties"]["condition"] = assignment.condition
            
        if hasattr(assignment, 'condition_version') and assignment.condition_version:
            role_assignment_data["properties"]["condition_version"] = assignment.condition_version
            
        if hasattr(assignment, 'delegated_managed_identity_resource_id') and assignment.delegated_managed_identity_resource_id:
            role_assignment_data["properties"]["delegated_managed_identity_resource_id"] = assignment.delegated_managed_identity_resource_id
            
        if hasattr(assignment, 'description') and assignment.description:
            role_assignment_data["properties"]["description"] = assignment.description
        
        # Extract role name if possible
        try:
            role_def_parts = assignment.role_definition_id.split('/')
            if len(role_def_parts) >= 2:
                role_id = role_def_parts[-1]
                # Try to get the role definition to get its display name
                try:
                    role_def = self.client.role_definitions.get_by_id(assignment.role_definition_id)
                    if role_def and role_def.role_name:
                        role_assignment_data["properties"]["role_name"] = role_def.role_name
                except Exception as e:
                    logger.debug(
                        f"Failed to fetch role definition {assignment.role_definition_id}: {e}"
                    )
        except Exception as e:
            logger.debug(
                f"Error processing role definition ID {assignment.role_definition_id}: {e}"
            )
            
        return role_assignment_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all role assignments."""
        logger.info(f"Scanning role assignments in subscription {self.subscription_id}")
        return self.list_role_assignments()


def scan_role_assignments(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Azure Role Assignments in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = RoleAssignmentsScanner(credentials, subscription_id)
    role_assignments = scanner.scan()
    
    if role_assignments:    # Process resources before generation
        role_assignments = process_resources(role_assignments, "azure_role_assignment")
    

        # Generate Terraform files
        generate_tf_auto(role_assignments, "azure_role_assignment", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(role_assignments)} Azure Role Assignments")
        
        # Generate import file
        generate_imports_file(
            "azure_role_assignment",
            role_assignments,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return role_assignments
