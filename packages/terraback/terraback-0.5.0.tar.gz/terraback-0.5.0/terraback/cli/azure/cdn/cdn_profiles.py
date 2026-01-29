from typing import Dict, List, Any, Optional
from pathlib import Path
from azure.mgmt.cdn import CdnManagementClient
from azure.core.exceptions import HttpResponseError
from terraback.utils.logging import get_logger
from terraback.cli.cache import cache_result
from terraback.core.license import require_professional

logger = get_logger(__name__)


class CdnProfilesScanner:
    def __init__(self, credentials, subscription_id: str):
        self.credentials = credentials
        self.subscription_id = subscription_id
        self.client = CdnManagementClient(credentials, subscription_id)

    @cache_result(ttl=300)
    def list_cdn_profiles(self) -> List[Dict[str, Any]]:
        """List all CDN profiles in the subscription."""
        cdn_profiles = []
        
        try:
            # List all CDN profiles
            for profile in self.client.profiles.list():
                try:
                    cdn_profiles.append(self._process_cdn_profile(profile))
                except Exception as e:
                    logger.error(f"Error processing CDN profile {profile.name}: {str(e)}")
                    continue
                    
        except HttpResponseError as e:
            logger.error(f"Error listing CDN profiles: {str(e)}")
            
        return cdn_profiles

    def _process_cdn_profile(self, profile) -> Dict[str, Any]:
        """Process a single CDN profile resource."""
        cdn_profile_data = {
            "id": profile.id,
            "name": profile.name,
            "type": "azure_cdn_profile",
            "resource_type": "azure_cdn_profile",
            "resource_group_name": profile.id.split('/')[4],
            "location": profile.location,
            "properties": {
                "name": profile.name,
                "location": profile.location,
                "resource_group_name": profile.id.split('/')[4],
                "sku": profile.sku.name,
            }
        }
        
        # Add tags
        if profile.tags:
            cdn_profile_data["properties"]["tags"] = profile.tags
            
        return cdn_profile_data

    def scan(self) -> List[Dict[str, Any]]:
        """Main scan method to retrieve all CDN profiles."""
        logger.info(f"Scanning CDN profiles in subscription {self.subscription_id}")
        return self.list_cdn_profiles()


@require_professional
def scan_cdn_profiles(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Scan CDN Profiles in the subscription."""
    from terraback.cli.azure.session import get_azure_credential, get_default_subscription_id
    from terraback.cli.azure.resource_processor import process_resources
    from terraback.terraform_generator.writer import generate_tf_auto
    from terraback.terraform_generator.imports import generate_imports_file
    
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    credentials = get_azure_credential()
    scanner = CdnProfilesScanner(credentials, subscription_id)
    cdn_profiles = scanner.scan()
    
    if cdn_profiles:
        # Generate Terraform files
        generate_tf_auto(cdn_profiles, "azure_cdn_profile", output_dir)
        print(f"[Cross-scan] Generated Terraform for {len(cdn_profiles)} Azure CDN Profiles")
        
        # Generate import file
        generate_imports_file(
            "azure_cdn_profile",
            cdn_profiles,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    
    return cdn_profiles
