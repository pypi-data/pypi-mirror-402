"""Azure SQL Database scanning functions."""

from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.cli.azure.common.utils import format_resource_dict, filter_system_resources
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)

# System databases to skip
SYSTEM_DATABASES = ['master', 'msdb', 'model', 'tempdb']


def scan_sql_databases_continued(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Continue SQL database scanning implementation."""
    sql_client = get_azure_client('SqlManagementClient', subscription_id)
    databases: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure SQL Databases...")
    print("Scanning for SQL Databases...")
    
    # Get all servers first
    servers = _get_sql_servers(sql_client, resource_group_name)
    
    # Process databases for each server
    for server in servers:
        server_databases = _get_databases_for_server(
            sql_client,
            server['resource_group_name'],
            server['name'],
            server['id']
        )
        databases.extend(server_databases)
    
    # Filter out system databases
    databases = [db for db in databases if db['name'] not in SYSTEM_DATABASES]
    
    # Process resources before generation
    databases = process_resources(databases, "azure_sql_database")
    
    # Generate Terraform files
    if databases:
        generate_tf_auto(databases, "azure_sql_database", output_dir)
        
        generate_imports_file(
            "azure_sql_database",
            databases,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No SQL Databases found.")
        logger.info("No SQL Databases found.")
    
    return databases


def _get_sql_servers(sql_client: Any, resource_group_name: Optional[str]) -> List[Dict[str, Any]]:
    """Get list of SQL servers."""
    @safe_azure_operation("list SQL servers", default_return=[])
    def list_servers():
        if resource_group_name:
            return list(sql_client.servers.list_by_resource_group(resource_group_name))
        else:
            return list(sql_client.servers.list())
    
    servers = []
    for server in list_servers():
        servers.append({
            'id': server.id,
            'name': server.name,
            'resource_group_name': server.id.split('/')[4] if server.id else None
        })
    return servers


def _get_databases_for_server(
    sql_client: Any,
    resource_group: str,
    server_name: str,
    server_id: str
) -> List[Dict[str, Any]]:
    """Get all databases for a specific server."""
    @safe_azure_operation(f"list databases for {server_name}", default_return=[])
    def list_databases():
        return list(sql_client.databases.list_by_server(
            resource_group_name=resource_group,
            server_name=server_name
        ))
    
    databases = []
    for db in list_databases():
        # Skip system databases
        if db.name in SYSTEM_DATABASES:
            continue
        
        db_dict = format_resource_dict(db, 'sql_database')
        
        # Override sanitized name to include server name
        db_dict['name_sanitized'] = f"{server_name}_{db.name}".replace('-', '_').replace('.', '_').lower()
        
        # Add server info
        db_dict['server_id'] = server_id
        db_dict['server_name'] = server_name
        db_dict['resource_group_name'] = resource_group
        
        # Format database properties
        _format_database_sku(db_dict, db)
        _format_database_properties(db_dict, db)
        
        # Get additional configurations
        _get_transparent_data_encryption(sql_client, db_dict, resource_group, server_name, db.name)
        _get_retention_policies(sql_client, db_dict, resource_group, server_name, db.name)
        _get_threat_detection_policy(sql_client, db_dict, resource_group, server_name, db.name)
        
        databases.append(db_dict)
    
    return databases


def _format_database_sku(db_dict: Dict[str, Any], db: Any) -> None:
    """Format database SKU information."""
    if hasattr(db, 'sku') and db.sku:
        db_dict['sku_name'] = db.sku.name
        db_dict['sku_tier'] = db.sku.tier
        db_dict['sku_family'] = db.sku.family
        db_dict['sku_capacity'] = db.sku.capacity


def _format_database_properties(db_dict: Dict[str, Any], db: Any) -> None:
    """Format database properties."""
    # Format max size
    if hasattr(db, 'max_size_bytes') and db.max_size_bytes:
        db_dict['max_size_gb'] = int(db.max_size_bytes / (1024 * 1024 * 1024))
    
    # Format backup redundancy
    if hasattr(db, 'requested_backup_storage_redundancy') and db.requested_backup_storage_redundancy:
        db_dict['storage_account_type'] = db.requested_backup_storage_redundancy


def _get_transparent_data_encryption(
    sql_client: Any,
    db_dict: Dict[str, Any],
    resource_group: str,
    server_name: str,
    database_name: str
) -> None:
    """Get transparent data encryption status."""
    @safe_azure_operation(f"get TDE for {database_name}", default_return=None)
    def get_tde():
        tde = sql_client.transparent_data_encryptions.get(
            resource_group_name=resource_group,
            server_name=server_name,
            database_name=database_name,
            transparent_data_encryption_name='current'  # Required parameter for TDE
        )
        if tde:
            # Check for the correct attribute name (might be 'status' instead of 'state')
            if hasattr(tde, 'status'):
                db_dict['transparent_data_encryption_enabled'] = tde.status == 'Enabled'
            elif hasattr(tde, 'state'):
                db_dict['transparent_data_encryption_enabled'] = tde.state == 'Enabled'
            else:
                # Default to enabled if we can't determine the status
                db_dict['transparent_data_encryption_enabled'] = True
        else:
            db_dict['transparent_data_encryption_enabled'] = True  # Default
    
    get_tde()


def _get_retention_policies(
    sql_client: Any,
    db_dict: Dict[str, Any],
    resource_group: str,
    server_name: str,
    database_name: str
) -> None:
    """Get retention policies for the database."""
    # Long term retention policy
    @safe_azure_operation(f"get LTR policy for {database_name}", default_return=None)
    def get_ltr():
        ltr_policy = sql_client.long_term_retention_policies.get(
            resource_group_name=resource_group,
            server_name=server_name,
            database_name=database_name,
            policy_name='default'  # Required parameter for LTR policy
        )
        if ltr_policy:
            db_dict['long_term_retention_policy'] = {
                'weekly_retention': ltr_policy.weekly_retention,
                'monthly_retention': ltr_policy.monthly_retention,
                'yearly_retention': ltr_policy.yearly_retention,
                'week_of_year': ltr_policy.week_of_year
            }
    
    get_ltr()
    
    # Short term retention policy
    @safe_azure_operation(f"get STR policy for {database_name}", default_return=None)
    def get_str():
        str_policy = sql_client.backup_short_term_retention_policies.get(
            resource_group_name=resource_group,
            server_name=server_name,
            database_name=database_name,
            policy_name='default'  # Required parameter for STR policy
        )
        if str_policy:
            db_dict['short_term_retention_policy'] = {
                'retention_days': str_policy.retention_days,
                'backup_interval_in_hours': str_policy.diff_backup_interval_in_hours
            }
    
    get_str()


def _get_threat_detection_policy(
    sql_client: Any,
    db_dict: Dict[str, Any],
    resource_group: str,
    server_name: str,
    database_name: str
) -> None:
    """Get threat detection policy for the database."""
    @safe_azure_operation(f"get threat detection for {database_name}", default_return=None)
    def get_threat_policy():
        # Threat detection policies have been replaced by Advanced Threat Protection
        # in newer Azure SDK versions. We'll try to use the security alert policies instead.
        if hasattr(sql_client, 'database_security_alert_policies'):
            threat_policy = sql_client.database_security_alert_policies.get(
                resource_group_name=resource_group,
                server_name=server_name,
                database_name=database_name,
                security_alert_policy_name='default'
            )
            if threat_policy and threat_policy.state == 'Enabled':
                db_dict['threat_detection_policy'] = {
                    'state': 'Enabled',
                    'disabled_alerts': threat_policy.disabled_alerts or [],
                    'email_account_admins': threat_policy.email_account_admins,
                    'email_addresses': threat_policy.email_addresses or [],
                    'retention_days': threat_policy.retention_days if hasattr(threat_policy, 'retention_days') else None,
                    'storage_endpoint': threat_policy.storage_endpoint if hasattr(threat_policy, 'storage_endpoint') else None,
                    'storage_account_access_key': f'var.sql_db_{server_name}_{database_name}_storage_key' if hasattr(threat_policy, 'storage_endpoint') and threat_policy.storage_endpoint else None
                }
    
    get_threat_policy()