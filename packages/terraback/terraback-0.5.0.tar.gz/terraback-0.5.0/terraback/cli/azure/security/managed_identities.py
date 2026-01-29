from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.msi import ManagedServiceIdentityClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.cli.azure.common.utils import normalize_resource_id

logger = get_logger(__name__)


class ManagedIdentitiesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = ManagedServiceIdentityClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_user_assigned_identities(self) -> List[Dict[str, Any]]:
        """List all user assigned identities in the subscription."""
        identities = []
        
        try:
            # List all user assigned identities
            for identity in self.client.user_assigned_identities.list_by_subscription():
                try:
                    identities.append(self._process_user_assigned_identity(identity))
                except Exception as e:
                    logger.error(f"Error processing user assigned identity {identity.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing user assigned identities: {str(e)}")
            
        return identities

    def _process_user_assigned_identity(self, identity) -> Dict[str, Any]:
        """Process a single user assigned identity resource."""
        # Normalize the resource ID
        normalized_id = normalize_resource_id(identity.id)
        
        identity_data = {
            "id": normalized_id,
            "name": identity.name,
            "type": "azure_user_assigned_identity",
            "resource_type": "azure_user_assigned_identity",
            "resource_group_name": normalized_id.split('/')[4],
            "location": identity.location,
            "properties": {
                "name": identity.name,
                "location": identity.location,
                "resource_group_name": normalized_id.split('/')[4],
            }
        }
        
        # Add metadata
        if hasattr(identity, 'principal_id') and identity.principal_id:
            identity_data["properties"]["principal_id"] = str(identity.principal_id)
            
        if hasattr(identity, 'client_id') and identity.client_id:
            identity_data["properties"]["client_id"] = str(identity.client_id)
            
        if hasattr(identity, 'tenant_id') and identity.tenant_id:
            identity_data["properties"]["tenant_id"] = str(identity.tenant_id)
        
        # Add tags
        if identity.tags:
            identity_data["properties"]["tags"] = identity.tags
            
        return identity_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all user assigned identities."""
        logger.info(f"Scanning user assigned identities in subscription {self.subscription_id}")
        return self.list_user_assigned_identities()


def scan_user_assigned_identities(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan user assigned identities in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = ManagedIdentitiesScanner(credentials, subscription_id)
    user_assigned_identities = scanner.scan()
    
    if user_assigned_identities:
        # Generate Terraform files
        generate_tf_auto(user_assigned_identities, "azure_user_assigned_identity", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(user_assigned_identities)} Azure Managed Identities")
        
        # Generate import file
        generate_imports_file(
            "azure_user_assigned_identity",
            user_assigned_identities,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return user_assigned_identities
