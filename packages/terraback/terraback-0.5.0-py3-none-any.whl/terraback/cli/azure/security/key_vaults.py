from typing import Optional, Dict, List, Any
from pathlib import Path
from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from .variable_stub import ensure_keyvault_secret_variable_stub
from terraback.core.license import require_professional

@require_professional
def scan_key_vaults(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Scans for Azure Key Vaults and generates Terraform code.
    """
    kv_client = get_azure_client('KeyVaultManagementClient', subscription_id)
    
    print("Scanning for Key Vaults...")
    key_vaults = []
    
    try:
        for vault in kv_client.vaults.list():
            vault_dict = vault.as_dict()
            
            # Add sanitized name
            vault_dict['name_sanitized'] = vault.name.replace('-', '_').replace('.', '_').lower()
            
            # Extract resource group
            if vault.id:
                parts = vault.id.split('/')
                if len(parts) >= 5:
                    vault_dict['resource_group_name'] = parts[4]
            
            # Get full vault properties
            try:
                full_vault = kv_client.vaults.get(
                    resource_group_name=vault_dict['resource_group_name'],
                    vault_name=vault.name
                )
                vault_dict.update(full_vault.as_dict())
            except Exception as e:
                print(f"  - Warning: Could not get full properties for {vault.name}: {e}")
            
            # Format SKU
            if hasattr(vault, 'properties') and hasattr(vault.properties, 'sku') and vault.properties.sku:
                vault_dict['sku_name'] = vault.properties.sku.name
            elif 'properties' in vault_dict and 'sku' in vault_dict['properties']:
                vault_dict['sku_name'] = vault_dict['properties']['sku']['name']
            else:
                vault_dict['sku_name'] = 'standard'  # Default value
            
            # Format tenant ID
            if hasattr(vault, 'properties') and hasattr(vault.properties, 'tenant_id') and vault.properties.tenant_id:
                vault_dict['tenant_id'] = str(vault.properties.tenant_id)
            elif 'properties' in vault_dict and 'tenant_id' in vault_dict['properties']:
                vault_dict['tenant_id'] = str(vault_dict['properties']['tenant_id'])
            else:
                # Try to get from subscription
                try:
                    from azure.mgmt.resource import SubscriptionClient
                    from azure.identity import DefaultAzureCredential
                    sub_client = SubscriptionClient(DefaultAzureCredential())
                    subscription = sub_client.subscriptions.get(subscription_id or vault_dict.get('id', '').split('/')[2])
                    vault_dict['tenant_id'] = str(subscription.tenant_id)
                except:
                    vault_dict['tenant_id'] = ''  # Will need to be filled manually
            
            # Format access policies
            if hasattr(vault, 'properties') and vault.properties.access_policies:
                vault_dict['access_policies'] = []
                for policy in vault.properties.access_policies:
                    policy_dict = {
                        'tenant_id': str(policy.tenant_id),
                        'object_id': str(policy.object_id),
                        'application_id': str(policy.application_id) if policy.application_id else None,
                        'certificate_permissions': policy.permissions.certificates if policy.permissions else [],
                        'key_permissions': policy.permissions.keys if policy.permissions else [],
                        'secret_permissions': policy.permissions.secrets if policy.permissions else [],
                        'storage_permissions': policy.permissions.storage if policy.permissions else []
                    }
                    vault_dict['access_policies'].append(policy_dict)
            
            # Format network ACLs
            if hasattr(vault, 'properties') and vault.properties.network_acls:
                network_acls = vault.properties.network_acls
                vault_dict['network_acls'] = {
                    'bypass': network_acls.bypass,
                    'default_action': network_acls.default_action,
                    'ip_rules': network_acls.ip_rules or [],
                    'virtual_network_subnet_ids': [rule.id for rule in network_acls.virtual_network_rules] if network_acls.virtual_network_rules else []
                }
            
            # Format other properties with robust error handling
            try:
                print(f"DEBUG: Processing vault {vault.name}, has properties: {hasattr(vault, 'properties')}")
                if hasattr(vault, 'properties'):
                    props = vault.properties
                    print(f"DEBUG: {vault.name} properties object: {type(props)}")
                    print(f"DEBUG: {vault.name} enable_rbac_authorization in props: {hasattr(props, 'enable_rbac_authorization')}")
                    
                    # Extract properties with fallbacks
                    vault_dict['enabled_for_deployment'] = getattr(props, 'enabled_for_deployment', False)
                    vault_dict['enabled_for_disk_encryption'] = getattr(props, 'enabled_for_disk_encryption', False)
                    vault_dict['enabled_for_template_deployment'] = getattr(props, 'enabled_for_template_deployment', False)
                    vault_dict['enable_rbac_authorization'] = getattr(props, 'enable_rbac_authorization', False)
                    vault_dict['soft_delete_retention_days'] = getattr(props, 'soft_delete_retention_in_days', 90)
                    vault_dict['purge_protection_enabled'] = getattr(props, 'enable_purge_protection', False)
                    vault_dict['public_network_access_enabled'] = props.public_network_access != 'Disabled' if hasattr(props, 'public_network_access') else True
                    
                    print(f"DEBUG: {vault.name} extracted enable_rbac_authorization = {vault_dict.get('enable_rbac_authorization', 'STILL_MISSING')}")
                elif 'properties' in vault_dict:
                    # Try to extract from vault_dict if direct attribute access fails
                    print(f"DEBUG: {vault.name} trying vault_dict properties extraction")
                    props_dict = vault_dict.get('properties', {})
                    vault_dict['enabled_for_deployment'] = props_dict.get('enabled_for_deployment', False)
                    vault_dict['enabled_for_disk_encryption'] = props_dict.get('enabled_for_disk_encryption', False)
                    vault_dict['enabled_for_template_deployment'] = props_dict.get('enabled_for_template_deployment', False)
                    vault_dict['enable_rbac_authorization'] = props_dict.get('enable_rbac_authorization', False)
                    vault_dict['soft_delete_retention_days'] = props_dict.get('soft_delete_retention_in_days', 90)
                    vault_dict['purge_protection_enabled'] = props_dict.get('enable_purge_protection', False)
                    vault_dict['public_network_access_enabled'] = props_dict.get('public_network_access', 'Enabled') != 'Disabled'
                    print(f"DEBUG: {vault.name} dict-based enable_rbac_authorization = {vault_dict.get('enable_rbac_authorization', 'STILL_MISSING')}")
                    
                    # Special handling: Try alternative property names that Azure API might use
                    if vault_dict.get('enable_rbac_authorization') is False:
                        # Check alternative property names
                        rbac_alternatives = ['enableRbacAuthorization', 'enable_rbac_authorization', 'enableRBACAuthorization']
                        for alt_name in rbac_alternatives:
                            if alt_name in props_dict:
                                vault_dict['enable_rbac_authorization'] = props_dict[alt_name]
                                print(f"DEBUG: {vault.name} found RBAC via alternative name '{alt_name}': {props_dict[alt_name]}")
                                break
                else:
                    print(f"DEBUG: {vault.name} has no properties at all!")
                    # Set safe defaults
                    vault_dict['enabled_for_deployment'] = False
                    vault_dict['enabled_for_disk_encryption'] = False
                    vault_dict['enabled_for_template_deployment'] = False
                    vault_dict['enable_rbac_authorization'] = False
                    vault_dict['soft_delete_retention_days'] = 90
                    vault_dict['purge_protection_enabled'] = False
                    vault_dict['public_network_access_enabled'] = True
                    
            except Exception as e:
                print(f"DEBUG: Exception processing {vault.name} properties: {e}")
                # Set safe defaults if property extraction fails
                vault_dict['enabled_for_deployment'] = False
                vault_dict['enabled_for_disk_encryption'] = False
                vault_dict['enabled_for_template_deployment'] = False
                vault_dict['enable_rbac_authorization'] = False
                vault_dict['soft_delete_retention_days'] = 90
                vault_dict['purge_protection_enabled'] = False
                vault_dict['public_network_access_enabled'] = True
            
            # Get diagnostic settings
            try:
                monitor_client = get_azure_client('MonitorManagementClient', subscription_id)
                diagnostic_settings = monitor_client.diagnostic_settings.list(
                    resource_uri=vault.id
                )
                vault_dict['diagnostic_settings'] = []
                for setting in diagnostic_settings:
                    vault_dict['diagnostic_settings'].append({
                        'name': setting.name,
                        'workspace_id': setting.workspace_id,
                        'storage_account_id': setting.storage_account_id,
                        'event_hub_auth_rule_id': setting.event_hub_authorization_rule_id,
                        'logs': [
                            {
                                'category': log.category,
                                'enabled': log.enabled,
                                'retention_policy': {
                                    'enabled': log.retention_policy.enabled if log.retention_policy else False,
                                    'days': log.retention_policy.days if log.retention_policy else 0
                                }
                            }
                            for log in setting.logs
                        ] if setting.logs else [],
                        'metrics': [
                            {
                                'category': metric.category,
                                'enabled': metric.enabled,
                                'retention_policy': {
                                    'enabled': metric.retention_policy.enabled if metric.retention_policy else False,
                                    'days': metric.retention_policy.days if metric.retention_policy else 0
                                }
                            }
                            for metric in setting.metrics
                        ] if setting.metrics else []
                    })
            except Exception as e:
                print(f"  - Warning: Could not get diagnostic settings for {vault.name}: {e}")
            
            # Ensure all boolean fields are present with proper values
            # If scanning failed to extract properties, use data from vault_dict['properties'] as backup
            boolean_fields = ['enabled_for_deployment', 'enabled_for_disk_encryption', 'enabled_for_template_deployment', 'enable_rbac_authorization', 'purge_protection_enabled', 'public_network_access_enabled']
            
            # Check if any boolean fields are missing and try to recover from vault_dict properties
            missing_fields = [field for field in boolean_fields if field not in vault_dict or vault_dict[field] is None]
            
            if missing_fields and 'properties' in vault_dict:
                print(f"DEBUG: Recovering missing fields {missing_fields} from vault_dict properties")
                props = vault_dict.get('properties', {})
                for field in missing_fields:
                    if field == 'enable_rbac_authorization':
                        vault_dict[field] = props.get('enable_rbac_authorization', False)
                    elif field == 'enabled_for_deployment':
                        vault_dict[field] = props.get('enabled_for_deployment', False)
                    elif field == 'enabled_for_disk_encryption':
                        vault_dict[field] = props.get('enabled_for_disk_encryption', False)
                    elif field == 'enabled_for_template_deployment':
                        vault_dict[field] = props.get('enabled_for_template_deployment', False)
                    elif field == 'purge_protection_enabled':
                        vault_dict[field] = props.get('enable_purge_protection', False)
                    elif field == 'public_network_access_enabled':
                        vault_dict[field] = props.get('public_network_access', 'Enabled') != 'Disabled'
                        
                print(f"DEBUG: After recovery, enable_rbac_authorization = {vault_dict.get('enable_rbac_authorization', 'STILL_MISSING')}")
            
            # Final safety net: ensure all boolean fields have values
            for field in boolean_fields:
                if field not in vault_dict or vault_dict[field] is None:
                    vault_dict[field] = False
                    
            # Debug: Check final vault_dict before adding to list
            print(f"DEBUG: Final vault_dict for {vault_dict.get('name', 'unknown')}: enable_rbac_authorization = {vault_dict.get('enable_rbac_authorization', 'NOT_FOUND')}")
            key_vaults.append(vault_dict)
            
    except Exception as e:
        print(f"Error scanning Key Vaults: {e}")
    
    if key_vaults:
        generate_tf_auto(key_vaults, "azure_key_vault", output_dir)
        generate_imports_file("azure_key_vault", key_vaults,
                            remote_resource_id_key="id", output_dir=output_dir, provider="azure")

def scan_key_vault_secrets(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Scans for Key Vault Secrets and generates Terraform code.
    Note: This only creates stubs as secret values cannot be retrieved.
    """
    kv_client = get_azure_client('KeyVaultManagementClient', subscription_id)
    secrets_client = get_azure_client('KeyVaultSecretsClient', subscription_id)
    
    print("Scanning for Key Vault Secrets...")
    secrets = []
    
    try:
        for vault in kv_client.vaults.list():
            resource_group = vault.id.split('/')[4] if vault.id else None
            
            # Get vault URI
            vault_uri = f"https://{vault.name}.vault.azure.net/"
            
            try:
                # List secrets in the vault
                for secret_props in secrets_client.list_properties_of_secrets(vault_uri):
                    secret_dict = {
                        'name': secret_props.name,
                        'name_sanitized': f"{vault.name}_{secret_props.name}".replace('-', '_').replace('.', '_').lower(),
                        'key_vault_id': vault.id,
                        'vault_name': vault.name,
                        'resource_group_name': resource_group,
                        'enabled': secret_props.enabled,
                        'content_type': secret_props.content_type,
                        'not_before_date': secret_props.not_before.isoformat() if secret_props.not_before else None,
                        'expiration_date': secret_props.expires_on.isoformat() if secret_props.expires_on else None,
                        'tags': secret_props.tags or {},
                        # Secret value will use generic variable
                        'value': "var.keyvault_secret_value"
                    }
                    
                    secrets.append(secret_dict)
                    
            except Exception as e:
                print(f"  - Warning: Could not list secrets for vault {vault.name}: {e}")
                # Fall back to creating stub entries
                continue
                
    except Exception as e:
        print(f"Error scanning Key Vault Secrets: {e}")
    
    if secrets:
        generate_tf_auto(secrets, "azure_key_vault_secret", output_dir)
        generate_imports_file("azure_key_vault_secret", secrets,
                            remote_resource_id_key="id", output_dir=output_dir, provider="azure")
        ensure_keyvault_secret_variable_stub(output_dir)

def scan_key_vault_keys(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Scans for Key Vault Keys and generates Terraform code.
    """
    kv_client = get_azure_client('KeyVaultManagementClient', subscription_id)
    keys_client = get_azure_client('KeyVaultKeysClient', subscription_id)
    
    print("Scanning for Key Vault Keys...")
    keys = []
    
    try:
        for vault in kv_client.vaults.list():
            resource_group = vault.id.split('/')[4] if vault.id else None
            
            # Get vault URI
            vault_uri = f"https://{vault.name}.vault.azure.net/"
            
            try:
                # List keys in the vault
                for key_props in keys_client.list_properties_of_keys(vault_uri):
                    key_dict = {
                        'name': key_props.name,
                        'name_sanitized': f"{vault.name}_{key_props.name}".replace('-', '_').replace('.', '_').lower(),
                        'key_vault_id': vault.id,
                        'vault_name': vault.name,
                        'resource_group_name': resource_group,
                        'key_type': key_props.key_type,
                        'key_size': key_props.key_size,
                        'enabled': key_props.enabled,
                        'not_before_date': key_props.not_before.isoformat() if key_props.not_before else None,
                        'expiration_date': key_props.expires_on.isoformat() if key_props.expires_on else None,
                        'tags': key_props.tags or {},
                        'key_opts': key_props.key_operations if hasattr(key_props, 'key_operations') else []
                    }
                    
                    # Try to get more details
                    try:
                        key = keys_client.get_key(vault_uri, key_props.name)
                        if key:
                            key_dict['curve'] = key.key.crv if hasattr(key.key, 'crv') else None
                    except Exception:
                        pass
                    
                    keys.append(key_dict)
                    
            except Exception as e:
                print(f"  - Warning: Could not list keys for vault {vault.name}: {e}")
                continue
                
    except Exception as e:
        print(f"Error scanning Key Vault Keys: {e}")
    
    if keys:
        generate_tf_auto(keys, "azure_key_vault_key", output_dir)
        generate_imports_file("azure_key_vault_key", keys,
                            remote_resource_id_key="id", output_dir=output_dir, provider="azure")

def scan_key_vault_certificates(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """
    Scans for Key Vault Certificates and generates Terraform code.
    """
    kv_client = get_azure_client('KeyVaultManagementClient', subscription_id)
    certs_client = get_azure_client('KeyVaultCertificatesClient', subscription_id)
    
    print("Scanning for Key Vault Certificates...")
    certificates = []
    
    try:
        for vault in kv_client.vaults.list():
            resource_group = vault.id.split('/')[4] if vault.id else None
            
            # Get vault URI
            vault_uri = f"https://{vault.name}.vault.azure.net/"
            
            try:
                # List certificates in the vault
                for cert_props in certs_client.list_properties_of_certificates(vault_uri):
                    cert_dict = {
                        'name': cert_props.name,
                        'name_sanitized': f"{vault.name}_{cert_props.name}".replace('-', '_').replace('.', '_').lower(),
                        'key_vault_id': vault.id,
                        'vault_name': vault.name,
                        'resource_group_name': resource_group,
                        'enabled': cert_props.enabled,
                        'not_before_date': cert_props.not_before.isoformat() if cert_props.not_before else None,
                        'expiration_date': cert_props.expires_on.isoformat() if cert_props.expires_on else None,
                        'tags': cert_props.tags or {}
                    }
                    
                    # Try to get certificate policy
                    try:
                        policy = certs_client.get_certificate_policy(vault_uri, cert_props.name)
                        if policy:
                            cert_dict['certificate_policy'] = {
                                'issuer_parameters': {
                                    'name': policy.issuer_parameters.name if policy.issuer_parameters else 'Self'
                                },
                                'key_properties': {
                                    'exportable': policy.key_properties.exportable if policy.key_properties else True,
                                    'key_size': policy.key_properties.key_size if policy.key_properties else 2048,
                                    'key_type': policy.key_properties.kty if policy.key_properties else 'RSA',
                                    'reuse_key': policy.key_properties.reuse_key if policy.key_properties else False
                                },
                                'lifetime_action': [],
                                'secret_properties': {
                                    'content_type': policy.secret_properties.content_type if policy.secret_properties else 'application/x-pkcs12'
                                },
                                'x509_certificate_properties': {
                                    'extended_key_usage': policy.x509_certificate_properties.ekus if policy.x509_certificate_properties and policy.x509_certificate_properties.ekus else [],
                                    'key_usage': policy.x509_certificate_properties.key_usage if policy.x509_certificate_properties and policy.x509_certificate_properties.key_usage else [],
                                    'subject': policy.x509_certificate_properties.subject if policy.x509_certificate_properties else '',
                                    'validity_in_months': policy.x509_certificate_properties.validity_in_months if policy.x509_certificate_properties else 12
                                }
                            }
                            
                            # Add lifetime actions
                            if policy.lifetime_actions:
                                for action in policy.lifetime_actions:
                                    lifetime_action = {
                                        'action': {
                                            'action_type': action.action.action_type if action.action else 'AutoRenew'
                                        },
                                        'trigger': {}
                                    }
                                    if action.trigger:
                                        if action.trigger.days_before_expiry:
                                            lifetime_action['trigger']['days_before_expiry'] = action.trigger.days_before_expiry
                                        if action.trigger.lifetime_percentage:
                                            lifetime_action['trigger']['lifetime_percentage'] = action.trigger.lifetime_percentage
                                    cert_dict['certificate_policy']['lifetime_action'].append(lifetime_action)
                    except Exception:
                        # If we can't get the policy, create a default one
                        cert_dict['certificate_policy'] = {
                            'issuer_parameters': {'name': 'Self'},
                            'key_properties': {
                                'exportable': True,
                                'key_size': 2048,
                                'key_type': 'RSA',
                                'reuse_key': False
                            },
                            'lifetime_action': [{
                                'action': {'action_type': 'AutoRenew'},
                                'trigger': {'days_before_expiry': 30}
                            }],
                            'secret_properties': {'content_type': 'application/x-pkcs12'},
                            'x509_certificate_properties': {
                                'extended_key_usage': [],
                                'key_usage': ['digitalSignature', 'keyEncipherment'],
                                'subject': f'CN={cert_props.name}',
                                'validity_in_months': 12
                            }
                        }
                    
                    certificates.append(cert_dict)
                    
            except Exception as e:
                print(f"  - Warning: Could not list certificates for vault {vault.name}: {e}")
                continue
                
    except Exception as e:
        print(f"Error scanning Key Vault Certificates: {e}")
    
    if certificates:
        generate_tf_auto(certificates, "azure_key_vault_certificate", output_dir)
        generate_imports_file("azure_key_vault_certificate", certificates,
                            remote_resource_id_key="id", output_dir=output_dir, provider="azure")

def list_key_vaults(output_dir: Path):
    """Lists all Key Vault resources previously generated."""
    ImportManager(output_dir, "azure_key_vault").list_all()

def import_key_vault(resource_id: str, output_dir: Path):
    """Runs terraform import for a specific Key Vault."""
    ImportManager(output_dir, "azure_key_vault").find_and_import(resource_id)


def _format_sku(vault_dict: Dict[str, Any], vault: Any) -> None:
    """Format SKU information for the key vault."""
    if hasattr(vault, 'properties') and hasattr(vault.properties, 'sku') and vault.properties.sku:
        vault_dict['sku_name'] = vault.properties.sku.name
    else:
        vault_dict['sku_name'] = 'standard'  # Default value


def _format_tenant_id(vault_dict: Dict[str, Any], vault: Any, subscription_id: str = None) -> None:
    """Format tenant ID for the key vault."""
    if hasattr(vault, 'properties') and hasattr(vault.properties, 'tenant_id') and vault.properties.tenant_id:
        vault_dict['tenant_id'] = str(vault.properties.tenant_id)
    else:
        # Try to get from subscription
        try:
            from azure.mgmt.resource import SubscriptionClient
            from azure.identity import DefaultAzureCredential
            sub_client = SubscriptionClient(DefaultAzureCredential())
            subscription = sub_client.subscriptions.get(subscription_id or vault_dict.get('id', '').split('/')[2])
            vault_dict['tenant_id'] = str(subscription.tenant_id)
        except:
            vault_dict['tenant_id'] = ''  # Will need to be filled manually


def _format_access_policies(vault_dict: Dict[str, Any], vault: Any) -> None:
    """Format access policies for the key vault."""
    vault_dict['access_policies'] = []
    
    if hasattr(vault, 'properties') and vault.properties.access_policies:
        for policy in vault.properties.access_policies:
            policy_dict = {
                'tenant_id': str(policy.tenant_id),
                'object_id': str(policy.object_id),
                'application_id': str(policy.application_id) if policy.application_id else None,
                'certificate_permissions': policy.permissions.certificates if policy.permissions else [],
                'key_permissions': policy.permissions.keys if policy.permissions else [],
                'secret_permissions': policy.permissions.secrets if policy.permissions else [],
                'storage_permissions': policy.permissions.storage if policy.permissions else []
            }
            vault_dict['access_policies'].append(policy_dict)


def _format_network_acls(vault_dict: Dict[str, Any], vault: Any) -> None:
    """Format network ACLs for the key vault."""
    if hasattr(vault, 'properties') and vault.properties.network_acls:
        network_acls = vault.properties.network_acls
        vault_dict['network_acls'] = {
            'bypass': network_acls.bypass or 'AzureServices',
            'default_action': network_acls.default_action or 'Allow',
            'ip_rules': network_acls.ip_rules or [],
            'virtual_network_subnet_ids': [rule.id for rule in network_acls.virtual_network_rules] if network_acls.virtual_network_rules else []
        }


def _format_other_properties(vault_dict: Dict[str, Any], vault: Any) -> None:
    """Format other properties for the key vault."""
    if hasattr(vault, 'properties'):
        props = vault.properties
        vault_dict['enabled_for_deployment'] = getattr(props, 'enabled_for_deployment', False)
        vault_dict['enabled_for_disk_encryption'] = getattr(props, 'enabled_for_disk_encryption', False)
        vault_dict['enabled_for_template_deployment'] = getattr(props, 'enabled_for_template_deployment', False)
        vault_dict['enable_rbac_authorization'] = getattr(props, 'enable_rbac_authorization', False)
        vault_dict['soft_delete_retention_days'] = getattr(props, 'soft_delete_retention_in_days', 90)
        vault_dict['purge_protection_enabled'] = getattr(props, 'enable_purge_protection', False)
        
        # Handle public network access
        if hasattr(props, 'public_network_access'):
            vault_dict['public_network_access_enabled'] = props.public_network_access != 'Disabled'
        else:
            vault_dict['public_network_access_enabled'] = True


def _format_diagnostic_settings(vault_dict: Dict[str, Any], vault_id: str, subscription_id: str = None) -> None:
    """Format diagnostic settings for the key vault."""
    vault_dict['diagnostic_settings'] = []
    
    @safe_azure_operation(f"get diagnostic settings for key vault", default_return=[])
    def get_diagnostic_settings():
        monitor_client = get_azure_client('MonitorManagementClient', subscription_id)
        return list(monitor_client.diagnostic_settings.list(resource_uri=vault_id))
    
    diagnostic_settings = get_diagnostic_settings()
    
    for setting in diagnostic_settings:
        vault_dict['diagnostic_settings'].append({
            'name': setting.name,
            'workspace_id': setting.workspace_id,
            'storage_account_id': setting.storage_account_id,
            'event_hub_auth_rule_id': setting.event_hub_authorization_rule_id,
            'logs': [
                {
                    'category': log.category,
                    'enabled': log.enabled,
                    'retention_policy': {
                        'enabled': log.retention_policy.enabled if log.retention_policy else False,
                        'days': log.retention_policy.days if log.retention_policy else 0
                    }
                }
                for log in setting.logs
            ] if setting.logs else [],
            'metrics': [
                {
                    'category': metric.category,
                    'enabled': metric.enabled,
                    'retention_policy': {
                        'enabled': metric.retention_policy.enabled if metric.retention_policy else False,
                        'days': metric.retention_policy.days if metric.retention_policy else 0
                    }
                }
                for metric in setting.metrics
            ] if setting.metrics else []
        })


def _format_template_attributes(vault_dict: Dict[str, Any], vault: Any) -> None:
    """Format all key vault attributes to match Jinja2 template expectations."""
    
    # Handle tags - ensure empty tags are handled properly
    if not hasattr(vault, 'tags') or not vault.tags:
        vault_dict['tags'] = {}
    else:
        vault_dict['tags'] = dict(vault.tags) if vault.tags else {}
    
    # Set sanitized name for resource naming
    vault_dict['name_sanitized'] = vault.name.replace('-', '_').replace('.', '_').lower()
    
    # Ensure all required boolean fields have defaults
    boolean_fields = [
        'enabled_for_deployment',
        'enabled_for_disk_encryption', 
        'enabled_for_template_deployment',
        'enable_rbac_authorization',
        'purge_protection_enabled',
        'public_network_access_enabled'
    ]
    
    for field in boolean_fields:
        if field not in vault_dict or vault_dict[field] is None:
            vault_dict[field] = False
    
    # Ensure soft_delete_retention_days has a default
    if 'soft_delete_retention_days' not in vault_dict or vault_dict['soft_delete_retention_days'] is None:
        vault_dict['soft_delete_retention_days'] = 90
