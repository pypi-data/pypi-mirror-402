from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.storage import StorageManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class FileSharesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = StorageManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_file_shares(self) -> List[Dict[str, Any]]:
        """List all file shares in the subscription."""
        file_shares = []
        
        try:
            # First get all storage accounts
            for storage_account in self.client.storage_accounts.list():
                resource_group_name = storage_account.id.split('/')[4]
                
                # Skip if file services are not enabled
                if hasattr(storage_account, 'enable_azure_files_aad_integration') and not storage_account.enable_azure_files_aad_integration:
                    continue
                
                # Then get all file shares for each storage account
                try:
                    for file_share in self.client.file_shares.list(
                        resource_group_name=resource_group_name,
                        account_name=storage_account.name
                    ):
                        try:
                            file_shares.append(self._process_file_share(
                                file_share, 
                                storage_account.name, 
                                resource_group_name
                            ))
                        except Exception as e:
                            logger.error(f"Error processing file share {file_share.name}: {str(e)}")
                            continue
                except HttpResponseError as e:
                    logger.debug(f"Error listing file shares for account {storage_account.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing storage accounts: {str(e)}")
            
        return file_shares

    def _process_file_share(self, file_share, storage_account_name: str, resource_group_name: str) -> Dict[str, Any]:
        """Process a single file share resource."""
        # Construct the storage account ID
        storage_account_id = f"/subscriptions/{self.subscription_id}/resourceGroups/{resource_group_name}/providers/Microsoft.Storage/storageAccounts/{storage_account_name}"
        
        file_share_data = {
            "id": file_share.id,
            "name": file_share.name,
            "type": "azure_storage_share",
            "resource_type": "azure_storage_share",
            "resource_group_name": resource_group_name,
            "properties": {
                "name": file_share.name,
                "storage_account_name": storage_account_name,
                "storage_account_id": storage_account_id,
                "resource_group_name": resource_group_name,
                "quota": file_share.share_quota or 5120,  # Default 5TB
            }
        }
        
        # Add optional properties
        if hasattr(file_share, 'enabled_protocols') and file_share.enabled_protocols:
            file_share_data["properties"]["enabled_protocol"] = file_share.enabled_protocols
            
        if hasattr(file_share, 'access_tier') and file_share.access_tier:
            file_share_data["properties"]["access_tier"] = file_share.access_tier
            
        if hasattr(file_share, 'metadata') and file_share.metadata:
            file_share_data["properties"]["metadata"] = file_share.metadata
        
        # Add share usage if available
        if hasattr(file_share, 'share_usage_bytes') and file_share.share_usage_bytes:
            file_share_data["properties"]["share_usage_bytes"] = file_share.share_usage_bytes
        
        # Get access policies if available
        try:
            access_policies = self.client.file_shares.get(
                resource_group_name=resource_group_name,
                account_name=storage_account_name,
                share_name=file_share.name,
                expand="stats"
            )
            
            if hasattr(access_policies, 'signed_identifiers') and access_policies.signed_identifiers:
                acl_list = []
                for identifier in access_policies.signed_identifiers:
                    acl_item = {"id": identifier.id}
                    if identifier.access_policy:
                        policy = identifier.access_policy
                        acl_item["access_policy"] = [{
                            "permissions": policy.permission,
                            "start": policy.start.isoformat() if policy.start else None,
                            "expiry": policy.expiry.isoformat() if policy.expiry else None
                        }]
                    acl_list.append(acl_item)
                if acl_list:
                    file_share_data["properties"]["acl"] = acl_list
        except Exception as e:
            logger.debug(f"Could not retrieve access policies for file share {file_share.name}: {str(e)}")
            
        return file_share_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all file shares."""
        logger.info(f"Scanning file shares in subscription {self.subscription_id}")
        return self.list_file_shares()


@require_professional
def scan_file_shares(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan Azure File Shares in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = FileSharesScanner(credentials, subscription_id)
    file_shares = scanner.scan()
    
    if file_shares:    # Process resources before generation
        file_shares = process_resources(file_shares, "azure_storage_share")
    

        # Generate Terraform files
        generate_tf_auto(file_shares, "azure_storage_share", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(file_shares)} Azure File Shares")
        
        # Generate import file
        generate_imports_file(
            "azure_storage_share",
            file_shares,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return file_shares
