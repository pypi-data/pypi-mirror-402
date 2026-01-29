# terraback/cli/azure/loadbalancer/load_balancers.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from azure.mgmt.network import NetworkManagementClient
from azure.core.exceptions import AzureError

from terraback.cli.azure.session import get_cached_azure_session, get_default_subscription_id
from terraback.terraform_generator.writer import generate_tf_auto
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.azure.resource_processor import process_resources

app = typer.Typer(name="standard", help="Scan and import Azure Load Balancers.")

def get_load_balancer_data(subscription_id: str = None, resource_group_name: Optional[str] = None, location: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Load Balancer data from Azure.
    
    Args:
        subscription_id: Azure subscription ID (optional)
        resource_group_name: Optional resource group filter
        location: Optional location filter
    
    Returns:
        List of load balancer data dictionaries
    """
    session = get_cached_azure_session(subscription_id)
    network_client = NetworkManagementClient(**session)
    
    load_balancers = []
    
    try:
        # Get load balancers either from specific resource group or all
        if resource_group_name:
            lb_list = network_client.load_balancers.list(resource_group_name)
        else:
            lb_list = network_client.load_balancers.list_all()
        
        for lb in lb_list:
            # Apply location filter if specified
            if location and lb.location != location:
                continue
                
            # Parse resource group from ID
            rg_name = lb.id.split('/')[4]
            
            # Build load balancer data structure matching Terraform schema
            lb_data = {
                "name": lb.name,
                "id": lb.id,
                "resource_group_name": rg_name,
                "location": lb.location,
                "tags": lb.tags or {},
                
                # SKU
                "sku": lb.sku.name if lb.sku else "Basic",
                "sku_tier": lb.sku.tier if lb.sku else "Regional",
                
                # Frontend IP configurations
                "frontend_ip_configuration": [],
                
                # Backend address pools
                "backend_address_pool": [],
                
                # Health probes
                "probe": [],
                
                # Load balancing rules
                "lb_rule": [],
                
                # Inbound NAT rules
                "inbound_nat_rule": [],
                
                # Outbound rules
                # "outbound_rule": [],
                
                # For resource naming
                "name_sanitized": lb.name.replace('-', '_').lower(),
                
                # State
                "provisioning_state": lb.provisioning_state,
            }
            
            # Extract frontend IP configurations
            if lb.frontend_ip_configurations:
                for frontend in lb.frontend_ip_configurations:
                    frontend_data = {
                        "name": frontend.name,
                        "id": frontend.id,
                        "private_ip_address": frontend.private_ip_address,
                        "private_ip_address_allocation": frontend.private_ip_allocation_method,
                        "private_ip_address_version": frontend.private_ip_address_version or "IPv4",
                        "subnet_id": frontend.subnet.id if frontend.subnet else None,
                        "public_ip_address_id": frontend.public_ip_address.id if frontend.public_ip_address else None,
                        "public_ip_prefix_id": frontend.public_ip_prefix.id if hasattr(frontend, 'public_ip_prefix') and frontend.public_ip_prefix else None,
                        "zones": frontend.zones if hasattr(frontend, 'zones') else [],
                    }
                    lb_data["frontend_ip_configuration"].append(frontend_data)
            
            # Extract backend address pools
            if lb.backend_address_pools:
                for backend in lb.backend_address_pools:
                    backend_data = {
                        "name": backend.name,
                        "id": backend.id,
                    }
                    lb_data["backend_address_pool"].append(backend_data)
            
            # Extract health probes
            if lb.probes:
                for probe in lb.probes:
                    probe_data = {
                        "name": probe.name,
                        "id": probe.id,
                        "protocol": probe.protocol,
                        "port": probe.port,
                        "request_path": probe.request_path if probe.protocol.upper() in ["HTTP", "HTTPS"] else None,
                        "interval_in_seconds": probe.interval_in_seconds,
                        "number_of_probes": probe.number_of_probes,
                    }
                    lb_data["probe"].append(probe_data)
            
            # Extract load balancing rules
            if lb.load_balancing_rules:
                for rule in lb.load_balancing_rules:
                    rule_data = {
                        "name": rule.name,
                        "id": rule.id,
                        "protocol": rule.protocol,
                        "frontend_port": rule.frontend_port,
                        "backend_port": rule.backend_port,
                        "frontend_ip_configuration_id": rule.frontend_ip_configuration.id if rule.frontend_ip_configuration else None,
                        "backend_address_pool_id": rule.backend_address_pool.id if rule.backend_address_pool else None,
                        "probe_id": rule.probe.id if rule.probe else None,
                        "enable_floating_ip": rule.enable_floating_ip,
                        "idle_timeout_in_minutes": rule.idle_timeout_in_minutes,
                        "load_distribution": rule.load_distribution,
                        "disable_outbound_snat": rule.disable_outbound_snat if hasattr(rule, 'disable_outbound_snat') else False,
                        "enable_tcp_reset": rule.enable_tcp_reset if hasattr(rule, 'enable_tcp_reset') else False,
                    }
                    lb_data["lb_rule"].append(rule_data)
            
            # Extract inbound NAT rules
            if lb.inbound_nat_rules:
                for nat_rule in lb.inbound_nat_rules:
                    nat_data = {
                        "name": nat_rule.name,
                        "id": nat_rule.id,
                        "protocol": nat_rule.protocol,
                        "frontend_port": nat_rule.frontend_port,
                        "backend_port": nat_rule.backend_port,
                        "frontend_ip_configuration_id": nat_rule.frontend_ip_configuration.id if nat_rule.frontend_ip_configuration else None,
                        "idle_timeout_in_minutes": nat_rule.idle_timeout_in_minutes,
                        "enable_floating_ip": nat_rule.enable_floating_ip,
                        "enable_tcp_reset": nat_rule.enable_tcp_reset if hasattr(nat_rule, 'enable_tcp_reset') else False,
                    }
                    lb_data["inbound_nat_rule"].append(nat_data)
            
            # Extract outbound rules (for Standard SKU)
            # Outbound rules are not rendered in the template, so this section is removed.
            
            load_balancers.append(lb_data)
            
    except AzureError as e:
        typer.echo(f"Error fetching load balancers: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return load_balancers

def _generate_lb_subresource_imports(lb_data: List[Dict[str, Any]], output_dir: Path) -> None:
    """Generate separate import JSON files for LB sub-resources."""
    
    backend_pool_imports = []
    probe_imports = []
    rule_imports = []
    nat_rule_imports = []
    
    for lb in lb_data:
        lb_name_sanitized = lb.get("name_sanitized", "")
        
        # Backend address pools
        for pool in lb.get("backend_address_pool", []):
            pool_name_sanitized = pool["name"].replace('-', '').replace('_', '').lower()
            backend_pool_imports.append({
                "resource_type": "azurerm_lb_backend_address_pool",
                "resource_name": f"{lb_name_sanitized}_{pool_name_sanitized}",
                "remote_id": pool["id"],
                "resource_data": pool
            })
        
        # Health probes
        for probe in lb.get("probe", []):
            probe_name_sanitized = probe["name"].replace('-', '_').lower()
            probe_imports.append({
                "resource_type": "azurerm_lb_probe", 
                "resource_name": f"{lb_name_sanitized}_{probe_name_sanitized}",
                "remote_id": probe["id"],
                "resource_data": probe
            })
        
        # LB rules
        for rule in lb.get("lb_rule", []):
            rule_name_sanitized = rule["name"].replace('-', '_').lower()
            rule_imports.append({
                "resource_type": "azurerm_lb_rule",
                "resource_name": f"{lb_name_sanitized}_{rule_name_sanitized}", 
                "remote_id": rule["id"],
                "resource_data": rule
            })
        
        # NAT rules
        for nat_rule in lb.get("inbound_nat_rule", []):
            nat_name_sanitized = nat_rule["name"].replace('-', '_').lower()
            nat_rule_imports.append({
                "resource_type": "azurerm_lb_nat_rule",
                "resource_name": f"{lb_name_sanitized}_{nat_name_sanitized}",
                "remote_id": nat_rule["id"], 
                "resource_data": nat_rule
            })
    
    # Write sub-resource import files to import/ subdirectory
    import_dir = output_dir / "import"
    import_dir.mkdir(exist_ok=True)

    if backend_pool_imports:
        import json
        pool_file = import_dir / "lb_backend_pool_import.json"
        with open(pool_file, 'w') as f:
            json.dump(backend_pool_imports, f, indent=2)

    if probe_imports:
        import json
        probe_file = import_dir / "lb_probe_import.json"
        with open(probe_file, 'w') as f:
            json.dump(probe_imports, f, indent=2)

    if rule_imports:
        import json
        rule_file = import_dir / "lb_rule_import.json"
        with open(rule_file, 'w') as f:
            json.dump(rule_imports, f, indent=2)

    if nat_rule_imports:
        import json
        nat_file = import_dir / "lb_nat_rule_import.json"
        with open(nat_file, 'w') as f:
            json.dump(nat_rule_imports, f, indent=2)

@app.command("scan")
def scan_load_balancers(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory for generated Terraform files."),
    subscription_id: Optional[str] = typer.Option(None, "--subscription-id", "-s", help="Azure Subscription ID.", envvar="AZURE_SUBSCRIPTION_ID"),
    location: Optional[str] = typer.Option(None, "--location", "-l", help="Filter by Azure location.", envvar="AZURE_LOCATION"),
    resource_group_name: Optional[str] = typer.Option(None, "--resource-group", "-g", help="Filter by a specific resource group."),
    with_deps: bool = typer.Option(False, "--with-deps", help="Scan all dependencies.")
):
    """Scans Azure Load Balancers and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
        if not subscription_id:
            typer.echo("Error: No Azure subscription found. Please run 'az login' or set AZURE_SUBSCRIPTION_ID", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning Azure Load Balancers with dependencies...")
        recursive_scan(
            "azure_lb",
            output_dir=output_dir,
            subscription_id=subscription_id,
            resource_group_name=resource_group_name,
            location=location
        )
    else:
        typer.echo(f"Scanning for Azure Load Balancers in subscription '{subscription_id}'...")
        if resource_group_name:
            typer.echo(f"Filtering by resource group: {resource_group_name}")
        if location:
            typer.echo(f"Filtering by location: {location}")
        
        lb_data = get_load_balancer_data(subscription_id, resource_group_name, location)

        if not lb_data:
            typer.echo("No load balancers found.")
            return

        lb_data = process_resources(lb_data, "azure_lb")

        # Generate Terraform files
        generate_tf_auto(lb_data, "azure_lb", output_dir)

        # Generate import file for main LB resources
        generate_imports_file(
            "azure_lb",
            lb_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
        
        # Generate additional import entries for sub-resources
        _generate_lb_subresource_imports(lb_data, output_dir)

@app.command("list")
def list_load_balancers(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing import file")
):
    """List all Azure Load Balancer resources previously generated."""
    ImportManager(output_dir, "azure_lb").list_all()

@app.command("import")
def import_load_balancer(
    lb_id: str = typer.Argument(..., help="Azure Load Balancer resource ID to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory with import file")
):
    """Run terraform import for a specific Azure Load Balancer by its resource ID."""
    ImportManager(output_dir, "azure_lb").find_and_import(lb_id)

# Scan function for cross-scan registry
def scan_azure_load_balancers(
    output_dir: Path,
    subscription_id: str = None,
    resource_group_name: Optional[str] = None,
    location: Optional[str] = None
):
    """Scan function to be registered with cross-scan registry."""
    # Get default subscription if not provided
    if not subscription_id:
        subscription_id = get_default_subscription_id()
    
    typer.echo(f"[Cross-scan] Scanning Azure Load Balancers in subscription {subscription_id}")
    
    lb_data = get_load_balancer_data(subscription_id, resource_group_name, location)

    if lb_data:
        lb_data = process_resources(lb_data, "azure_lb")
        generate_tf_auto(lb_data, "azure_lb", output_dir)
        generate_imports_file(
            "azure_lb",
            lb_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="azure"
        )
        _generate_lb_subresource_imports(lb_data, output_dir)
        typer.echo(f"[Cross-scan] Generated Terraform for {len(lb_data)} Azure Load Balancers")
