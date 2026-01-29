"""Azure SQL Database scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging
from terraback.core.license import require_professional

from terraback.cli.azure.session import get_azure_client
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict, filter_system_resources
from terraback.cli.azure.common.exceptions import safe_azure_operation
from terraback.cli.azure.resource_processor import process_resources

logger = logging.getLogger(__name__)
app = typer.Typer(name="sql", help="Scan and import Azure SQL resources.")

def scan_sql_servers(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure SQL Servers and generate Terraform configurations.
    
    This function retrieves all SQL Servers from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of SQL Server resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    sql_client = get_azure_client('SqlManagementClient', subscription_id)
    servers: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure SQL Servers...")
    print("Scanning for SQL Servers...")
    
    # List all SQL servers with error handling
    @safe_azure_operation("list SQL servers", default_return=[])
    def list_servers():
        if resource_group_name:
            return list(sql_client.servers.list_by_resource_group(resource_group_name))
        else:
            return list(sql_client.servers.list())
    
    server_list = list_servers()
    
    # Process each server
    for server in server_list:
        server_dict = format_resource_dict(server, 'sql_server')
        
        # Format server properties
        _format_administrator_login(server_dict, server)
        _format_identity(server_dict, server)
        
        # Get additional configurations
        _get_azure_ad_admin(sql_client, server_dict, server.name)
        _get_security_policies(sql_client, server_dict, server.name)
        _get_firewall_rules(sql_client, server_dict, server.name)
        _get_virtual_network_rules(sql_client, server_dict, server.name)
        _get_auditing_settings(sql_client, server_dict, server.name)
        
        # Format all template attributes
        _format_template_attributes(server_dict, server)
        
        servers.append(server_dict)
        logger.debug(f"Processed SQL server: {server.name}")
    
    # Process resources before generation
    servers = process_resources(servers, "azure_sql_server")
    
    # Generate Terraform files
    if servers:
        generate_tf_auto(servers, "azure_sql_server", output_dir)
        
        generate_imports_file(
            "azure_sql_server",
            servers,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
        
        # Generate variables for SQL server passwords
        _ensure_sql_server_password_variables(output_dir, servers)
    else:
        print("No SQL Servers found.")
        logger.info("No SQL Servers found.")
    
    return servers

def _format_administrator_login(server_dict: Dict[str, Any], server: Any) -> None:
    """Format administrator login information."""
    if hasattr(server, 'administrator_login') and server.administrator_login:
        server_dict['administrator_login'] = server.administrator_login
        # Password will need to be provided via variable
        server_dict['administrator_login_password'] = f"var.sql_server_{server.name}_password"


def _format_identity(server_dict: Dict[str, Any], server: Any) -> None:
    """Format server identity information."""
    if hasattr(server, 'identity') and server.identity:
        server_dict['identity_formatted'] = {
            'type': server.identity.type,
            'principal_id': server.identity.principal_id,
            'tenant_id': server.identity.tenant_id,
            'identity_ids': list(server.identity.user_assigned_identities.keys()) if server.identity.user_assigned_identities else []
        }


def _get_azure_ad_admin(
    sql_client: Any,
    server_dict: Dict[str, Any],
    server_name: str
) -> None:
    """Get Azure AD administrator configuration."""
    @safe_azure_operation(f"get Azure AD admin for {server_name}", default_return=None)
    def get_ad_admin():
        ad_admin = sql_client.server_azure_ad_administrators.get(
            resource_group_name=server_dict['resource_group_name'],
            server_name=server_name,
            administrator_name='ActiveDirectory'
        )
        if ad_admin:
            server_dict['azuread_administrator'] = {
                'login_username': ad_admin.login,
                'object_id': ad_admin.sid,
                'tenant_id': ad_admin.tenant_id,
                'azuread_authentication_only': ad_admin.azure_ad_only_authentication
            }
    
    get_ad_admin()


def _get_security_policies(
    sql_client: Any,
    server_dict: Dict[str, Any],
    server_name: str
) -> None:
    """Get server security alert policies."""
    @safe_azure_operation(f"get security policies for {server_name}", default_return=[])
    def get_policies():
        return list(sql_client.server_security_alert_policies.list_by_server(
            resource_group_name=server_dict['resource_group_name'],
            server_name=server_name
        ))
    
    security_alerts = get_policies()
    for alert_policy in security_alerts:
        if alert_policy.state == 'Enabled':
            server_dict['threat_detection_policy'] = {
                'state': 'Enabled',
                'disabled_alerts': alert_policy.disabled_alerts or [],
                'email_account_admins': alert_policy.email_account_admins,
                'email_addresses': alert_policy.email_addresses or [],
                'retention_days': alert_policy.retention_days,
                'storage_endpoint': alert_policy.storage_endpoint,
                'storage_account_access_key': f'var.sql_server_{server_name}_storage_key' if alert_policy.storage_endpoint else None
            }
            break


def _get_firewall_rules(
    sql_client: Any,
    server_dict: Dict[str, Any],
    server_name: str
) -> None:
    """Get firewall rules for the server."""
    @safe_azure_operation(f"get firewall rules for {server_name}", default_return=[])
    def get_rules():
        return list(sql_client.firewall_rules.list_by_server(
            resource_group_name=server_dict['resource_group_name'],
            server_name=server_name
        ))
    
    firewall_rules = get_rules()
    server_dict['firewall_rules'] = [
        {
            'name': rule.name,
            'start_ip_address': rule.start_ip_address,
            'end_ip_address': rule.end_ip_address
        }
        for rule in firewall_rules
    ]


def _get_virtual_network_rules(
    sql_client: Any,
    server_dict: Dict[str, Any],
    server_name: str
) -> None:
    """Get virtual network rules for the server."""
    @safe_azure_operation(f"get vnet rules for {server_name}", default_return=[])
    def get_rules():
        return list(sql_client.virtual_network_rules.list_by_server(
            resource_group_name=server_dict['resource_group_name'],
            server_name=server_name
        ))
    
    vnet_rules = get_rules()
    server_dict['virtual_network_rules'] = [
        {
            'name': rule.name,
            'subnet_id': rule.virtual_network_subnet_id,
            'ignore_missing_vnet_service_endpoint': rule.ignore_missing_vnet_service_endpoint
        }
        for rule in vnet_rules
    ]


def _get_auditing_settings(
    sql_client: Any,
    server_dict: Dict[str, Any],
    server_name: str
) -> None:
    """Get auditing settings for the server."""
    @safe_azure_operation(f"get auditing settings for {server_name}", default_return=None)
    def get_auditing():
        auditing = sql_client.server_blob_auditing_policies.get(
            resource_group_name=server_dict['resource_group_name'],
            server_name=server_name
        )
        if auditing and auditing.state == 'Enabled':
            server_dict['extended_auditing_policy'] = {
                'storage_endpoint': auditing.storage_endpoint,
                'storage_account_access_key': f'var.sql_server_{server_name}_audit_storage_key' if auditing.storage_endpoint else None,
                'storage_account_access_key_is_secondary': auditing.is_storage_secondary_key_in_use,
                'retention_in_days': auditing.retention_days,
                'log_monitoring_enabled': auditing.is_azure_monitor_target_enabled
            }
    
    get_auditing()


@require_professional
def scan_sql_databases(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure SQL Databases and generate Terraform configurations.
    
    This function retrieves all SQL Databases from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of SQL Database resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    # Import the continuation function to avoid duplication
    from .sql_databases_scan import scan_sql_databases_continued
    return scan_sql_databases_continued(output_dir, subscription_id, resource_group_name, location)


def scan_sql_elastic_pools(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure SQL Elastic Pools and generate Terraform configurations.
    
    This function retrieves all SQL Elastic Pools from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group filter
        
    Returns:
        List of SQL Elastic Pool resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    sql_client = get_azure_client('SqlManagementClient', subscription_id)
    elastic_pools: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Azure SQL Elastic Pools...")
    print("Scanning for SQL Elastic Pools...")
    
    # Get all servers
    from .sql_databases_scan import _get_sql_servers
    servers = _get_sql_servers(sql_client, resource_group_name)
    
    # Process elastic pools for each server
    for server in servers:
        pools = _get_elastic_pools_for_server(
            sql_client,
            server['resource_group_name'],
            server['name'],
            server['id']
        )
        elastic_pools.extend(pools)
    
    # Process resources before generation
    elastic_pools = process_resources(elastic_pools, "azure_sql_elastic_pool")
    
    # Generate Terraform files
    if elastic_pools:
        generate_tf_auto(elastic_pools, "azure_sql_elastic_pool", output_dir)
        
        generate_imports_file(
            "azure_sql_elastic_pool",
            elastic_pools,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
    else:
        print("No SQL Elastic Pools found.")
        logger.info("No SQL Elastic Pools found.")
    
    return elastic_pools

def _get_elastic_pools_for_server(
    sql_client: Any,
    resource_group: str,
    server_name: str,
    server_id: str
) -> List[Dict[str, Any]]:
    """Get all elastic pools for a specific server."""
    @safe_azure_operation(f"list elastic pools for {server_name}", default_return=[])
    def list_pools():
        return list(sql_client.elastic_pools.list_by_server(
            resource_group_name=resource_group,
            server_name=server_name
        ))
    
    elastic_pools = []
    for pool in list_pools():
        pool_dict = format_resource_dict(pool, 'sql_elastic_pool')
        
        # Override sanitized name to include server name
        pool_dict['name_sanitized'] = f"{server_name}_{pool.name}".replace('-', '_').replace('.', '_').lower()
        
        # Add server info
        pool_dict['server_id'] = server_id
        pool_dict['server_name'] = server_name
        pool_dict['resource_group_name'] = resource_group
        
        # Format pool properties
        _format_elastic_pool_sku(pool_dict, pool)
        _format_elastic_pool_settings(pool_dict, pool)
        
        # Get databases in pool
        _get_databases_in_pool(sql_client, pool_dict, resource_group, server_name, pool.name)
        
        elastic_pools.append(pool_dict)
    
    return elastic_pools


def _format_elastic_pool_sku(pool_dict: Dict[str, Any], pool: Any) -> None:
    """Format elastic pool SKU information."""
    if hasattr(pool, 'sku') and pool.sku:
        pool_dict['sku'] = {
            'name': pool.sku.name,
            'tier': pool.sku.tier,
            'family': pool.sku.family if hasattr(pool.sku, 'family') else None,
            'capacity': pool.sku.capacity
        }
        # Also keep formatted version for backwards compatibility
        pool_dict['sku_formatted'] = pool_dict['sku']


def _format_elastic_pool_settings(pool_dict: Dict[str, Any], pool: Any) -> None:
    """Format elastic pool settings."""
    # Format per database settings
    if hasattr(pool, 'per_database_settings') and pool.per_database_settings:
        pool_dict['per_database_settings_formatted'] = {
            'min_capacity': pool.per_database_settings.min_capacity,
            'max_capacity': pool.per_database_settings.max_capacity
        }
    
    # Format max size - keep as bytes for template to handle special cases
    if hasattr(pool, 'max_size_bytes') and pool.max_size_bytes:
        pool_dict['max_size_bytes'] = pool.max_size_bytes
        # Also provide GB value for general use (float, not int)
        pool_dict['max_size_gb'] = pool.max_size_bytes / (1024 * 1024 * 1024)


def _get_databases_in_pool(
    sql_client: Any,
    pool_dict: Dict[str, Any],
    resource_group: str,
    server_name: str,
    pool_name: str
) -> None:
    """Get databases in the elastic pool."""
    @safe_azure_operation(f"list databases in pool {pool_name}", default_return=[])
    def list_databases():
        return list(sql_client.databases.list_by_elastic_pool(
            resource_group_name=resource_group,
            server_name=server_name,
            elastic_pool_name=pool_name
        ))
    
    databases_in_pool = list_databases()
    pool_dict['database_ids'] = [db.id for db in databases_in_pool]


# CLI Commands
@app.command("scan-servers")
def scan_sql_servers_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure SQL Servers and generates Terraform code."""
    typer.echo(f"Scanning for Azure SQL Servers in subscription '{subscription_id}'...")
    
    try:
        scan_sql_servers(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning SQL Servers: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("scan-databases")
def scan_sql_databases_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure SQL Databases and generates Terraform code."""
    typer.echo(f"Scanning for Azure SQL Databases in subscription '{subscription_id}'...")
    
    try:
        scan_sql_databases(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning SQL Databases: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("scan-elastic-pools")
def scan_sql_elastic_pools_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure SQL Elastic Pools and generates Terraform code."""
    typer.echo(f"Scanning for Azure SQL Elastic Pools in subscription '{subscription_id}'...")
    
    try:
        scan_sql_elastic_pools(
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name
        )
    except Exception as e:
        typer.echo(f"Error scanning SQL Elastic Pools: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list-servers")
def list_sql_servers(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all SQL Server resources previously generated."""
    ImportManager(output_dir, "azure_sql_server").list_all()


@app.command("import-server")
def import_sql_server(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the SQL Server to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific SQL Server."""
    ImportManager(output_dir, "azure_sql_server").find_and_import(resource_id)


@app.command("list-databases")
def list_sql_databases(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all SQL Database resources previously generated."""
    ImportManager(output_dir, "azure_sql_database").list_all()


@app.command("import-database")
def import_sql_database(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the SQL Database to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific SQL Database."""
    ImportManager(output_dir, "azure_sql_database").find_and_import(resource_id)


@app.command("list-elastic-pools")
def list_sql_elastic_pools(output_dir: Path = typer.Option("generated", "-o")):
    """Lists all SQL Elastic Pool resources previously generated."""
    ImportManager(output_dir, "azure_sql_elastic_pool").list_all()


@app.command("import-elastic-pool")
def import_sql_elastic_pool(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the SQL Elastic Pool to import."),
    output_dir: Path = typer.Option("generated", "-o")
):
    """Runs terraform import for a specific SQL Elastic Pool."""
    ImportManager(output_dir, "azure_sql_elastic_pool").find_and_import(resource_id)


def _ensure_sql_server_password_variables(output_dir: Path, servers: List[Dict[str, Any]]) -> None:
    """Ensure variables.tf includes password variables for SQL servers."""
    variables_file = output_dir / "variables.tf"
    
    try:
        # Read existing content or start with empty
        if variables_file.exists():
            content = variables_file.read_text()
        else:
            content = ""
        
        # Track if we added any new variables
        added_any = False
        
        # Check and add variable for each SQL server
        for server in servers:
            if server.get('administrator_login'):
                var_name = f"sql_server_{server['name_sanitized']}_password"
                search_string = f'variable "{var_name}"'
                
                if search_string not in content:
                    if content and not content.endswith("\n"):
                        content += "\n"
                    
                    variable_block = (
                        f'\nvariable "{var_name}" {{\n'
                        f'  type        = string\n'
                        f'  description = "Administrator password for SQL Server {server["name"]}"\n'
                        f'  default     = "ChangeMe123!"\n'
                        f'  sensitive   = true\n'
                        f'}}\n'
                    )
                    content += variable_block
                    added_any = True
                    print(f"Added password variable '{var_name}' to variables.tf")
        
        # Write back if any changes were made
        if added_any:
            variables_file.write_text(content)
            print("Update these password values before applying Terraform.")
            
    except Exception as e:
        print(f"Warning: could not update {variables_file}: {e}")


def _format_template_attributes(server_dict: Dict[str, Any], server: Any) -> None:
    """Format all SQL server attributes to match Jinja2 template expectations."""
    
    # Set basic server attributes with proper defaults
    if hasattr(server, 'version'):
        server_dict['version'] = server.version or '12.0'
    else:
        server_dict['version'] = '12.0'
    
    # Format connection policy
    if hasattr(server, 'connection_policy'):
        server_dict['connection_policy'] = server.connection_policy
    
    # Format minimum TLS version
    if hasattr(server, 'minimal_tls_version'):
        server_dict['minimum_tls_version'] = server.minimal_tls_version
    elif hasattr(server, 'minimum_tls_version'):
        server_dict['minimum_tls_version'] = server.minimum_tls_version
    
    # Format public network access
    if hasattr(server, 'public_network_access') and server.public_network_access:
        server_dict['public_network_access_enabled'] = server.public_network_access != 'Disabled'
    elif 'public_network_access_enabled' not in server_dict:
        server_dict['public_network_access_enabled'] = True
    
    # Format outbound network restriction
    if hasattr(server, 'restrict_outbound_network_access'):
        server_dict['outbound_network_restriction_enabled'] = server.restrict_outbound_network_access == 'Enabled'
    elif 'outbound_network_restriction_enabled' not in server_dict:
        server_dict['outbound_network_restriction_enabled'] = False
    
    # Handle tags - ensure empty tags are handled properly
    if not hasattr(server, 'tags') or not server.tags:
        server_dict['tags'] = {}
    else:
        server_dict['tags'] = dict(server.tags) if server.tags else {}
    
    # Set sanitized name for resource naming
    server_dict['name_sanitized'] = server.name.replace('-', '_').replace('.', '_').lower()
    
    # Map identity_formatted to identity if present
    if 'identity_formatted' in server_dict:
        server_dict['identity'] = server_dict['identity_formatted']
    
    # Set default boolean values if not present
    boolean_fields = [
        'public_network_access_enabled',
        'outbound_network_restriction_enabled'
    ]
    
    for field in boolean_fields:
        if field not in server_dict or server_dict[field] is None:
            server_dict[field] = field == 'public_network_access_enabled'  # Default True for public access, False for others
