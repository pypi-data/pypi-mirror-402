import typer
from pathlib import Path
from typing import Optional

from . import networks, subnets, firewalls, routers, nat_gateways

app = typer.Typer(
    name="network",
    help="Work with GCP networking resources like VPCs, subnets, and firewall rules.",
    no_args_is_help=True,
)

def register():
    """Register network scan functions with cross-scan registry."""
    from terraback.utils.cross_scan_registry import register_scan_function

    from .networks import scan_gcp_networks
    from .subnets import scan_gcp_subnets
    from .firewalls import scan_gcp_firewalls
    from .routers import scan_gcp_routers
    from .nat_gateways import scan_gcp_nat_gateways

    register_scan_function("gcp_network", scan_gcp_networks)
    register_scan_function("gcp_subnet", scan_gcp_subnets)
    register_scan_function("gcp_firewall", scan_gcp_firewalls)
    register_scan_function("gcp_router", scan_gcp_routers)
    register_scan_function("gcp_nat_gateway", scan_gcp_nat_gateways)

# Add sub-commands for each network resource type
app.add_typer(networks.app, name="vpc")
app.add_typer(subnets.app, name="subnet")
app.add_typer(firewalls.app, name="firewall")
app.add_typer(routers.app, name="router")
app.add_typer(nat_gateways.app, name="nat")

@app.command("scan-all")
def scan_all_network(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p", envvar="GOOGLE_CLOUD_PROJECT"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps"),
):
    """Scan all GCP network resources."""
    from terraback.cli.gcp.session import get_default_project_id

    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found. Please run 'gcloud config set project' or set GOOGLE_CLOUD_PROJECT", err=True)
            raise typer.Exit(code=1)

    if with_deps:
        from terraback.utils.cross_scan_registry import recursive_scan
        recursive_scan("gcp_network", output_dir=output_dir, project_id=project_id, region=region)
    else:
        from .networks import scan_gcp_networks
        from .subnets import scan_gcp_subnets
        from .firewalls import scan_gcp_firewalls
        from .routers import scan_gcp_routers
        from .nat_gateways import scan_gcp_nat_gateways

        scan_gcp_networks(output_dir=output_dir, project_id=project_id, region=region)
        scan_gcp_subnets(output_dir=output_dir, project_id=project_id, region=region)
        scan_gcp_firewalls(output_dir=output_dir, project_id=project_id)
        scan_gcp_routers(output_dir=output_dir, project_id=project_id, region=region)
        scan_gcp_nat_gateways(output_dir=output_dir, project_id=project_id, region=region)
