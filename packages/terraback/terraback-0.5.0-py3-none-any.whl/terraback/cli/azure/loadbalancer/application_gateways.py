"""Azure Application Gateways scanning and management module."""

import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

from terraback.cli.azure.session import get_azure_client
from terraback.cli.azure.resource_processor import process_resources
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.common.utils import format_resource_dict
from terraback.cli.azure.common.exceptions import safe_azure_operation

logger = logging.getLogger(__name__)
app = typer.Typer(name="app-gateway", help="Scan and import Azure Application Gateways.")


def scan_application_gateways(
    output_dir: Path,
    subscription_id: Optional[str] = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
) -> List[Dict[str, Any]]:
    """
    Scan for Azure Application Gateways and generate Terraform configurations.
    
    This function retrieves all Application Gateways from the specified subscription
    and generates corresponding Terraform resource definitions.
    
    Args:
        output_dir: Directory where Terraform files will be generated
        subscription_id: Azure subscription ID. If None, uses default subscription
        resource_group_name: Optional resource group to filter by (not used)
        location: Optional location to filter by (not used)
        
    Returns:
        List of Application Gateway resource dictionaries
        
    Raises:
        AzureError: If Azure API calls fail
        IOError: If file writing fails
    """
    network_client = get_azure_client('NetworkManagementClient', subscription_id)
    app_gateways: List[Dict[str, Any]] = []
    
    logger.info("Scanning for Application Gateways...")
    print("Scanning for Application Gateways...")
    
    # List all application gateways with error handling
    @safe_azure_operation("list application gateways", default_return=[])
    def list_gateways():
        return list(network_client.application_gateways.list_all())
    
    gateway_list = list_gateways()
    
    # Process each gateway
    for gateway in gateway_list:
        gateway_dict = format_resource_dict(gateway, 'application_gateway')
        
        # Format complex properties
        _format_gateway_sku(gateway_dict, gateway)
        _format_gateway_ip_configurations(gateway_dict, gateway)
        _format_frontend_configurations(gateway_dict, gateway)
        _format_backend_configurations(gateway_dict, gateway)
        _format_http_settings(gateway_dict, gateway)
        _format_listeners_and_rules(gateway_dict, gateway)
        _format_probes(gateway_dict, gateway)
        _format_ssl_certificates(gateway_dict, gateway)
        _format_waf_configuration(gateway_dict, gateway)
        
        # Get additional configurations
        _get_webhooks(gateway_dict, network_client, gateway.name)
        
        app_gateways.append(gateway_dict)
        logger.debug(f"Processed application gateway: {gateway.name}")
    
    # Process resources before generation
    app_gateways = process_resources(app_gateways, "azure_application_gateway")
    

    
    # Generate Terraform files
    if app_gateways:
        generate_tf_auto(app_gateways, "azure_application_gateway", output_dir)
        
        generate_imports_file(
            "azure_application_gateway",
            app_gateways,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
        
        # Check if SSL certificates are present
        if _has_ssl_certificates(app_gateways):
            _ensure_ssl_certificate_variable(output_dir)
    else:
        print("No Application Gateways found.")
        logger.info("No Application Gateways found.")
    
    return app_gateways


def _format_gateway_sku(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format gateway SKU information."""
    if hasattr(gateway, 'sku') and gateway.sku:
        gateway_dict['sku_formatted'] = {
            'name': gateway.sku.name,
            'tier': gateway.sku.tier,
            'capacity': gateway.sku.capacity
        }


def _format_gateway_ip_configurations(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format gateway IP configurations."""
    if not hasattr(gateway, 'gateway_ip_configurations') or not gateway.gateway_ip_configurations:
        return
        
    gateway_dict['gateway_ip_configurations_formatted'] = []
    for config in gateway.gateway_ip_configurations:
        gateway_dict['gateway_ip_configurations_formatted'].append({
            'name': config.name,
            'subnet_id': config.subnet.id if config.subnet else None
        })


def _format_frontend_configurations(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format frontend IP configurations and ports."""
    # Frontend IP configurations
    if hasattr(gateway, 'frontend_ip_configurations') and gateway.frontend_ip_configurations:
        gateway_dict['frontend_ip_configurations_formatted'] = []
        for config in gateway.frontend_ip_configurations:
            formatted_config = {
                'name': config.name,
                'private_ip_address': config.private_ip_address,
                'private_ip_allocation_method': config.private_ip_allocation_method
            }
            if config.public_ip_address:
                formatted_config['public_ip_address_id'] = config.public_ip_address.id
            if config.subnet:
                formatted_config['subnet_id'] = config.subnet.id
            gateway_dict['frontend_ip_configurations_formatted'].append(formatted_config)
    
    # Frontend ports
    if hasattr(gateway, 'frontend_ports') and gateway.frontend_ports:
        gateway_dict['frontend_ports_formatted'] = [
            {
                'name': port.name,
                'port': port.port
            }
            for port in gateway.frontend_ports
        ]


def _format_backend_configurations(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format backend address pools."""
    if not hasattr(gateway, 'backend_address_pools') or not gateway.backend_address_pools:
        return
        
    gateway_dict['backend_address_pools_formatted'] = []
    for pool in gateway.backend_address_pools:
        pool_dict = {
            'name': pool.name,
            'ip_addresses': [],
            'fqdns': []
        }
        
        if pool.backend_addresses:
            for addr in pool.backend_addresses:
                if hasattr(addr, 'ip_address') and addr.ip_address:
                    pool_dict['ip_addresses'].append(addr.ip_address)
                if hasattr(addr, 'fqdn') and addr.fqdn:
                    pool_dict['fqdns'].append(addr.fqdn)
        
        gateway_dict['backend_address_pools_formatted'].append(pool_dict)


def _format_http_settings(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format backend HTTP settings."""
    if not hasattr(gateway, 'backend_http_settings_collection') or not gateway.backend_http_settings_collection:
        return
        
    gateway_dict['backend_http_settings_formatted'] = []
    for settings in gateway.backend_http_settings_collection:
        settings_dict = {
            'name': settings.name,
            'port': settings.port,
            'protocol': settings.protocol,
            'cookie_based_affinity': settings.cookie_based_affinity,
            'request_timeout': settings.request_timeout,
            'pick_host_name_from_backend_address': settings.pick_host_name_from_backend_address
        }
        
        if settings.probe:
            settings_dict['probe_id'] = settings.probe.id
        if settings.authentication_certificates:
            settings_dict['authentication_certificate_ids'] = [
                cert.id for cert in settings.authentication_certificates
            ]
        
        gateway_dict['backend_http_settings_formatted'].append(settings_dict)


def _format_listeners_and_rules(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format HTTP listeners and request routing rules."""
    # HTTP listeners
    if hasattr(gateway, 'http_listeners') and gateway.http_listeners:
        gateway_dict['http_listeners_formatted'] = []
        for listener in gateway.http_listeners:
            listener_dict = {
                'name': listener.name,
                'protocol': listener.protocol,
                'host_name': listener.host_name,
                'require_sni': listener.require_server_name_indication
            }
            
            if listener.frontend_ip_configuration:
                listener_dict['frontend_ip_configuration_name'] = listener.frontend_ip_configuration.id.split('/')[-1]
            if listener.frontend_port:
                listener_dict['frontend_port_name'] = listener.frontend_port.id.split('/')[-1]
            if listener.ssl_certificate:
                listener_dict['ssl_certificate_id'] = listener.ssl_certificate.id
            
            gateway_dict['http_listeners_formatted'].append(listener_dict)
    
    # Request routing rules
    if hasattr(gateway, 'request_routing_rules') and gateway.request_routing_rules:
        gateway_dict['request_routing_rules_formatted'] = []
        for rule in gateway.request_routing_rules:
            rule_dict = {
                'name': rule.name,
                'rule_type': rule.rule_type,
                'priority': rule.priority
            }
            
            if rule.http_listener:
                rule_dict['http_listener_name'] = rule.http_listener.id.split('/')[-1]
            if rule.backend_address_pool:
                rule_dict['backend_address_pool_name'] = rule.backend_address_pool.id.split('/')[-1]
            if rule.backend_http_settings:
                rule_dict['backend_http_settings_name'] = rule.backend_http_settings.id.split('/')[-1]
            if rule.url_path_map:
                rule_dict['url_path_map_id'] = rule.url_path_map.id
            
            gateway_dict['request_routing_rules_formatted'].append(rule_dict)


def _format_probes(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format health probes."""
    if not hasattr(gateway, 'probes') or not gateway.probes:
        return
        
    gateway_dict['probes_formatted'] = []
    for probe in gateway.probes:
        probe_dict = {
            'name': probe.name,
            'protocol': probe.protocol,
            'host': probe.host,
            'path': probe.path,
            'interval': probe.interval,
            'timeout': probe.timeout,
            'unhealthy_threshold': probe.unhealthy_threshold,
            'pick_host_name_from_backend_http_settings': probe.pick_host_name_from_backend_http_settings
        }
        gateway_dict['probes_formatted'].append(probe_dict)


def _format_ssl_certificates(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format SSL certificates."""
    if not hasattr(gateway, 'ssl_certificates') or not gateway.ssl_certificates:
        return
        
    gateway_dict['ssl_certificates_formatted'] = []
    for cert in gateway.ssl_certificates:
        cert_dict = {
            'name': cert.name,
            'data': 'REDACTED',  # Certificate data should be handled via variables
            'password': 'var.ssl_certificate_password'
        }
        gateway_dict['ssl_certificates_formatted'].append(cert_dict)


def _format_waf_configuration(gateway_dict: Dict[str, Any], gateway: Any) -> None:
    """Format WAF configuration."""
    if not hasattr(gateway, 'web_application_firewall_configuration'):
        return
        
    waf = gateway.web_application_firewall_configuration
    if waf:
        gateway_dict['waf_configuration'] = {
            'enabled': waf.enabled,
            'firewall_mode': waf.firewall_mode,
            'rule_set_type': waf.rule_set_type,
            'rule_set_version': waf.rule_set_version,
            'file_upload_limit_mb': waf.file_upload_limit_in_mb,
            'request_body_check': waf.request_body_check,
            'max_request_body_size_kb': waf.max_request_body_size_in_kb
        }


def _get_webhooks(gateway_dict: Dict[str, Any], network_client: Any, gateway_name: str) -> None:
    """Get webhooks for the application gateway."""
    # Application Gateways don't have webhooks - this is a placeholder
    # for future expansion if needed
    pass


def _has_ssl_certificates(app_gateways: List[Dict[str, Any]]) -> bool:
    """Check if any application gateway has SSL certificates."""
    return any(gw.get('ssl_certificates_formatted') for gw in app_gateways)


def _ensure_ssl_certificate_variable(output_dir: Path) -> None:
    """Ensure SSL certificate password variable is created."""
    from terraback.cli.azure.security.variable_stub import SSL_CERTIFICATE_PASSWORD_VARIABLE_BLOCK, _ensure_variable_stub
    _ensure_variable_stub(
        output_dir,
        'variable "ssl_certificate_password"',
        SSL_CERTIFICATE_PASSWORD_VARIABLE_BLOCK,
        "ssl_certificate_password"
    )


@app.command("scan")
def scan_app_gateways_cli(
    output_dir: Path = typer.Option("generated", "-o", help="Directory for generated Terraform files."),
    subscription_id: str = typer.Option(..., help="Azure Subscription ID."),
    resource_group_name: Optional[str] = typer.Option(None, help="Filter by a specific resource group.")
):
    """Scans Azure Application Gateways and generates Terraform code."""
    typer.echo(f"Scanning for Azure Application Gateways in subscription '{subscription_id}'...")
    
    try:
        scan_application_gateways(output_dir=output_dir, subscription_id=subscription_id)
    except Exception as e:
        typer.echo(f"Error scanning Application Gateways: {e}", err=True)
        raise typer.Exit(code=1)


@app.command("list")
def list_application_gateways(
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Lists all Application Gateway resources previously generated."""
    ImportManager(output_dir, "azure_application_gateway").list_all()


@app.command("import")
def import_application_gateway(
    resource_id: str = typer.Argument(..., help="Azure resource ID of the Application Gateway to import."),
    output_dir: Path = typer.Option("generated", "-o", help="Directory containing Terraform files.")
):
    """Runs terraform import for a specific Application Gateway."""
    ImportManager(output_dir, "azure_application_gateway").find_and_import(resource_id)