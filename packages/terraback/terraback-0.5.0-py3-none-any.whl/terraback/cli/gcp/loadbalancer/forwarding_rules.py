# terraback/cli/gcp/loadbalancer/forwarding_rules.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="forwarding-rule", help="Scan and import GCP forwarding rules.")

def get_forwarding_rule_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch forwarding rule data from GCP."""
    forwarding_rules = []

    try:
        # Scan global forwarding rules
        global_client = compute_v1.GlobalForwardingRulesClient()
        global_request = compute_v1.ListGlobalForwardingRulesRequest(
            project=project_id
        )
        global_rules = global_client.list(request=global_request)

        for rule in global_rules:
            rule_data = {
                "name": rule.name,
                "id": f"{project_id}/{rule.name}",
                "project": project_id,
                "region": None,  # Global rules don't have a region
                "description": rule.description if hasattr(rule, 'description') and rule.description else "",

                # Core forwarding rule properties
                "target": rule.target.split('/')[-1] if rule.target else None,
                "ip_address": rule.i_p_address if hasattr(rule, 'i_p_address') and rule.i_p_address else None,
                "ip_protocol": rule.i_p_protocol if hasattr(rule, 'i_p_protocol') and rule.i_p_protocol else None,
                "load_balancing_scheme": rule.load_balancing_scheme if hasattr(rule, 'load_balancing_scheme') and rule.load_balancing_scheme else None,
                "port_range": rule.port_range if hasattr(rule, 'port_range') and rule.port_range else None,
                "ports": list(rule.ports) if hasattr(rule, 'ports') and rule.ports else [],

                # Additional properties
                "ip_version": rule.ip_version if hasattr(rule, 'ip_version') and rule.ip_version else None,
                "network": rule.network.split('/')[-1] if hasattr(rule, 'network') and rule.network else None,
                "subnetwork": rule.subnetwork.split('/')[-1] if hasattr(rule, 'subnetwork') and rule.subnetwork else None,
                "network_tier": rule.network_tier if hasattr(rule, 'network_tier') and rule.network_tier else None,

                # Labels and metadata
                "labels": dict(rule.labels) if hasattr(rule, 'labels') and rule.labels else {},
                "fingerprint": rule.fingerprint if hasattr(rule, 'fingerprint') else None,
                "creation_timestamp": rule.creation_timestamp if hasattr(rule, 'creation_timestamp') else None,

                # Service directory configuration
                "service_directory_registrations": [],

                # For resource naming and identification
                "name_sanitized": rule.name.replace('-', '_').lower(),
                "rule_type": "global"
            }

            # Process service directory registrations if available
            if hasattr(rule, 'service_directory_registrations') and rule.service_directory_registrations:
                for reg in rule.service_directory_registrations:
                    rule_data["service_directory_registrations"].append({
                        "namespace": reg.namespace if hasattr(reg, 'namespace') else None,
                        "service": reg.service if hasattr(reg, 'service') else None
                    })

            forwarding_rules.append(rule_data)

        # Scan regional forwarding rules
        if region:
            # Scan specific region
            regional_client = compute_v1.ForwardingRulesClient()
            regional_request = compute_v1.ListForwardingRulesRequest(
                project=project_id,
                region=region
            )
            regional_rules = regional_client.list(request=regional_request)

            for rule in regional_rules:
                rule_data = {
                    "name": rule.name,
                    "id": f"{project_id}/{region}/{rule.name}",
                    "project": project_id,
                    "region": region,
                    "description": rule.description if hasattr(rule, 'description') and rule.description else "",

                    # Core forwarding rule properties
                    "target": rule.target.split('/')[-1] if rule.target else None,
                    "backend_service": rule.backend_service.split('/')[-1] if hasattr(rule, 'backend_service') and rule.backend_service else None,
                    "ip_address": rule.i_p_address if hasattr(rule, 'i_p_address') and rule.i_p_address else None,
                    "ip_protocol": rule.i_p_protocol if hasattr(rule, 'i_p_protocol') and rule.i_p_protocol else None,
                    "load_balancing_scheme": rule.load_balancing_scheme if hasattr(rule, 'load_balancing_scheme') and rule.load_balancing_scheme else None,
                    "port_range": rule.port_range if hasattr(rule, 'port_range') and rule.port_range else None,
                    "ports": list(rule.ports) if hasattr(rule, 'ports') and rule.ports else [],
                    "all_ports": rule.all_ports if hasattr(rule, 'all_ports') else None,

                    # Regional-specific properties
                    "network": rule.network.split('/')[-1] if hasattr(rule, 'network') and rule.network else None,
                    "subnetwork": rule.subnetwork.split('/')[-1] if hasattr(rule, 'subnetwork') and rule.subnetwork else None,
                    "network_tier": rule.network_tier if hasattr(rule, 'network_tier') and rule.network_tier else None,
                    "ip_version": rule.ip_version if hasattr(rule, 'ip_version') and rule.ip_version else None,

                    # Labels and metadata
                    "labels": dict(rule.labels) if hasattr(rule, 'labels') and rule.labels else {},
                    "fingerprint": rule.fingerprint if hasattr(rule, 'fingerprint') else None,
                    "creation_timestamp": rule.creation_timestamp if hasattr(rule, 'creation_timestamp') else None,

                    # Service directory configuration
                    "service_directory_registrations": [],

                    # For resource naming and identification
                    "name_sanitized": rule.name.replace('-', '_').lower(),
                    "rule_type": "regional"
                }

                # Process service directory registrations if available
                if hasattr(rule, 'service_directory_registrations') and rule.service_directory_registrations:
                    for reg in rule.service_directory_registrations:
                        rule_data["service_directory_registrations"].append({
                            "namespace": reg.namespace if hasattr(reg, 'namespace') else None,
                            "service": reg.service if hasattr(reg, 'service') else None
                        })

                forwarding_rules.append(rule_data)

        else:
            # Scan all regions
            regions_client = compute_v1.RegionsClient()
            regions_request = compute_v1.ListRegionsRequest(project=project_id)
            regions_list = regions_client.list(request=regions_request)

            regional_client = compute_v1.ForwardingRulesClient()

            for region_obj in regions_list:
                region_name = region_obj.name
                try:
                    regional_request = compute_v1.ListForwardingRulesRequest(
                        project=project_id,
                        region=region_name
                    )
                    regional_rules = regional_client.list(request=regional_request)

                    for rule in regional_rules:
                        rule_data = {
                            "name": rule.name,
                            "id": f"{project_id}/{region_name}/{rule.name}",
                            "project": project_id,
                            "region": region_name,
                            "description": rule.description if hasattr(rule, 'description') and rule.description else "",

                            # Core forwarding rule properties
                            "target": rule.target.split('/')[-1] if rule.target else None,
                            "backend_service": rule.backend_service.split('/')[-1] if hasattr(rule, 'backend_service') and rule.backend_service else None,
                            "ip_address": rule.i_p_address if hasattr(rule, 'i_p_address') and rule.i_p_address else None,
                            "ip_protocol": rule.i_p_protocol if hasattr(rule, 'i_p_protocol') and rule.i_p_protocol else None,
                            "load_balancing_scheme": rule.load_balancing_scheme if hasattr(rule, 'load_balancing_scheme') and rule.load_balancing_scheme else None,
                            "port_range": rule.port_range if hasattr(rule, 'port_range') and rule.port_range else None,
                            "ports": list(rule.ports) if hasattr(rule, 'ports') and rule.ports else [],
                            "all_ports": rule.all_ports if hasattr(rule, 'all_ports') else None,

                            # Regional-specific properties
                            "network": rule.network.split('/')[-1] if hasattr(rule, 'network') and rule.network else None,
                            "subnetwork": rule.subnetwork.split('/')[-1] if hasattr(rule, 'subnetwork') and rule.subnetwork else None,
                            "network_tier": rule.network_tier if hasattr(rule, 'network_tier') and rule.network_tier else None,
                            "ip_version": rule.ip_version if hasattr(rule, 'ip_version') and rule.ip_version else None,

                            # Labels and metadata
                            "labels": dict(rule.labels) if hasattr(rule, 'labels') and rule.labels else {},
                            "fingerprint": rule.fingerprint if hasattr(rule, 'fingerprint') else None,
                            "creation_timestamp": rule.creation_timestamp if hasattr(rule, 'creation_timestamp') else None,

                            # Service directory configuration
                            "service_directory_registrations": [],

                            # For resource naming and identification
                            "name_sanitized": rule.name.replace('-', '_').lower(),
                            "rule_type": "regional"
                        }

                        # Process service directory registrations if available
                        if hasattr(rule, 'service_directory_registrations') and rule.service_directory_registrations:
                            for reg in rule.service_directory_registrations:
                                rule_data["service_directory_registrations"].append({
                                    "namespace": reg.namespace if hasattr(reg, 'namespace') else None,
                                    "service": reg.service if hasattr(reg, 'service') else None
                                })

                        forwarding_rules.append(rule_data)

                except exceptions.GoogleAPIError as e:
                    # Skip regions that have errors (e.g., disabled APIs)
                    if "not found" not in str(e).lower():
                        typer.echo(f"Warning: Could not scan region {region_name}: {str(e)}", err=True)
                    continue

    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching forwarding rules: {str(e)}", err=True)
        raise typer.Exit(code=1)

    return forwarding_rules

@app.command("scan")
def scan_forwarding_rules(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP forwarding rules and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan

    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)

    if with_deps:
        typer.echo("Scanning GCP forwarding rules with dependencies...")
        recursive_scan(
            "gcp_global_forwarding_rule",
            output_dir=output_dir,
            project_id=project_id,
            region=region
        )
    else:
        typer.echo(f"Scanning for GCP forwarding rules in project '{project_id}'...")
        if region:
            typer.echo(f"Region: {region}")
        else:
            typer.echo("Region: all regions (plus global rules)")

        forwarding_rule_data = get_forwarding_rule_data(project_id, region)

        if not forwarding_rule_data:
            typer.echo("No forwarding rules found.")
            return

        # Separate global and regional rules for different resource types
        global_rules = [rule for rule in forwarding_rule_data if rule["rule_type"] == "global"]
        regional_rules = [rule for rule in forwarding_rule_data if rule["rule_type"] == "regional"]

        # Generate Terraform files for global rules
        if global_rules:
            output_file = output_dir / "gcp_global_forwarding_rule.tf"
            generate_tf(global_rules, "gcp_global_forwarding_rule", output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(global_rules)} global forwarding rules -> {output_file}")

            # Generate import file for global rules
            generate_imports_file(
                "gcp_global_forwarding_rule",
                global_rules,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )

        # Generate Terraform files for regional rules
        if regional_rules:
            output_file = output_dir / "gcp_compute_forwarding_rule.tf"
            generate_tf(regional_rules, "gcp_compute_forwarding_rule", output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(regional_rules)} regional forwarding rules -> {output_file}")

            # Generate import file for regional rules
            generate_imports_file(
                "gcp_compute_forwarding_rule",
                regional_rules,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )

# Scan function for cross-scan registry
def scan_gcp_forwarding_rules(
    output_dir: Path,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()

    typer.echo(f"[Cross-scan] Scanning GCP forwarding rules in project {project_id}")

    forwarding_rule_data = get_forwarding_rule_data(project_id, region)

    if forwarding_rule_data:
        # Separate global and regional rules for different resource types
        global_rules = [rule for rule in forwarding_rule_data if rule["rule_type"] == "global"]
        regional_rules = [rule for rule in forwarding_rule_data if rule["rule_type"] == "regional"]

        # Generate files for global rules
        if global_rules:
            output_file = output_dir / "gcp_global_forwarding_rule.tf"
            generate_tf(global_rules, "gcp_global_forwarding_rule", output_file, provider="gcp")
            generate_imports_file(
                "gcp_global_forwarding_rule",
                global_rules,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(global_rules)} global forwarding rules")

        # Generate files for regional rules
        if regional_rules:
            output_file = output_dir / "gcp_compute_forwarding_rule.tf"
            generate_tf(regional_rules, "gcp_compute_forwarding_rule", output_file, provider="gcp")
            generate_imports_file(
                "gcp_compute_forwarding_rule",
                regional_rules,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(regional_rules)} regional forwarding rules")

@app.command("list")
def list_forwarding_rules(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    rule_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by rule type: global or regional")
):
    """List all GCP forwarding rule resources previously generated."""
    if rule_type == "global":
        typer.echo("Global forwarding rules:")
        ImportManager(output_dir, "gcp_global_forwarding_rule").list_all()
    elif rule_type == "regional":
        typer.echo("Regional forwarding rules:")
        ImportManager(output_dir, "gcp_compute_forwarding_rule").list_all()
    else:
        typer.echo("Global forwarding rules:")
        ImportManager(output_dir, "gcp_global_forwarding_rule").list_all()
        typer.echo("\nRegional forwarding rules:")
        ImportManager(output_dir, "gcp_compute_forwarding_rule").list_all()

@app.command("import")
def import_forwarding_rule(
    rule_id: str = typer.Argument(..., help="GCP forwarding rule ID (project/name for global, project/region/name for regional)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    rule_type: Optional[str] = typer.Option(None, "--type", "-t", help="Rule type: global or regional (auto-detected if not specified)")
):
    """Run terraform import for a specific GCP forwarding rule."""
    # Auto-detect rule type based on ID format if not specified
    if rule_type is None:
        parts = rule_id.split('/')
        if len(parts) == 2:
            rule_type = "global"
        elif len(parts) == 3:
            rule_type = "regional"
        else:
            typer.echo("Error: Invalid rule ID format. Expected project/name for global or project/region/name for regional.", err=True)
            raise typer.Exit(code=1)

    if rule_type == "global":
        ImportManager(output_dir, "gcp_global_forwarding_rule").find_and_import(rule_id)
    elif rule_type == "regional":
        ImportManager(output_dir, "gcp_compute_forwarding_rule").find_and_import(rule_id)
    else:
        typer.echo("Error: Rule type must be 'global' or 'regional'", err=True)
        raise typer.Exit(code=1)
