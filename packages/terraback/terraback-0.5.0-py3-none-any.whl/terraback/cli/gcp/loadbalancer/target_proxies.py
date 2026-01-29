# terraback/cli/gcp/loadbalancer/target_proxies.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="target-proxy", help="Scan and import GCP target proxies.")

def get_target_proxy_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch target proxy data from GCP."""
    target_proxies = []

    try:
        # Scan global target proxies when no region specified
        if not region:
            # 1. Global HTTP Target Proxies
            try:
                http_client = compute_v1.TargetHttpProxiesClient()
                http_request = compute_v1.ListTargetHttpProxiesRequest(project=project_id)
                http_list = http_client.list(request=http_request)

                for proxy in http_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{proxy.name}",
                        "project": project_id,
                        "region": None,  # Global proxies don't have a region
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "http",
                        "scope": "global",

                        # Core properties
                        "url_map": proxy.url_map.split('/')[-1] if hasattr(proxy, 'url_map') and proxy.url_map else None,
                        "ssl_certificates": [],  # HTTP proxies don't have SSL certificates
                        "ssl_policy": None,  # HTTP proxies don't have SSL policy
                        "quic_override": None,  # HTTP proxies don't have QUIC
                        "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_target_http_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan global HTTP target proxies: {str(e)}", err=True)

            # 2. Global HTTPS Target Proxies
            try:
                https_client = compute_v1.TargetHttpsProxiesClient()
                https_request = compute_v1.ListTargetHttpsProxiesRequest(project=project_id)
                https_list = https_client.list(request=https_request)

                for proxy in https_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{proxy.name}",
                        "project": project_id,
                        "region": None,  # Global proxies don't have a region
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "https",
                        "scope": "global",

                        # Core properties
                        "url_map": proxy.url_map.split('/')[-1] if hasattr(proxy, 'url_map') and proxy.url_map else None,
                        "ssl_certificates": [cert.split('/')[-1] for cert in proxy.ssl_certificates] if hasattr(proxy, 'ssl_certificates') and proxy.ssl_certificates else [],
                        "ssl_policy": proxy.ssl_policy.split('/')[-1] if hasattr(proxy, 'ssl_policy') and proxy.ssl_policy else None,
                        "quic_override": proxy.quic_override if hasattr(proxy, 'quic_override') and proxy.quic_override else None,
                        "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                        "certificate_map": proxy.certificate_map.split('/')[-1] if hasattr(proxy, 'certificate_map') and proxy.certificate_map else None,
                        "server_tls_policy": proxy.server_tls_policy.split('/')[-1] if hasattr(proxy, 'server_tls_policy') and proxy.server_tls_policy else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_target_https_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan global HTTPS target proxies: {str(e)}", err=True)

            # 3. Global SSL Target Proxies
            try:
                ssl_client = compute_v1.TargetSslProxiesClient()
                ssl_request = compute_v1.ListTargetSslProxiesRequest(project=project_id)
                ssl_list = ssl_client.list(request=ssl_request)

                for proxy in ssl_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{proxy.name}",
                        "project": project_id,
                        "region": None,  # Global proxies don't have a region
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "ssl",
                        "scope": "global",

                        # Core properties
                        "backend_service": proxy.service.split('/')[-1] if hasattr(proxy, 'service') and proxy.service else None,
                        "ssl_certificates": [cert.split('/')[-1] for cert in proxy.ssl_certificates] if hasattr(proxy, 'ssl_certificates') and proxy.ssl_certificates else [],
                        "ssl_policy": proxy.ssl_policy.split('/')[-1] if hasattr(proxy, 'ssl_policy') and proxy.ssl_policy else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                        "certificate_map": proxy.certificate_map.split('/')[-1] if hasattr(proxy, 'certificate_map') and proxy.certificate_map else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_target_ssl_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan global SSL target proxies: {str(e)}", err=True)

            # 4. Global TCP Target Proxies
            try:
                tcp_client = compute_v1.TargetTcpProxiesClient()
                tcp_request = compute_v1.ListTargetTcpProxiesRequest(project=project_id)
                tcp_list = tcp_client.list(request=tcp_request)

                for proxy in tcp_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{proxy.name}",
                        "project": project_id,
                        "region": None,  # Global proxies don't have a region
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "tcp",
                        "scope": "global",

                        # Core properties
                        "backend_service": proxy.service.split('/')[-1] if hasattr(proxy, 'service') and proxy.service else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                        "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_target_tcp_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan global TCP target proxies: {str(e)}", err=True)

            # 5. Scan regional target proxies across all regions
            regions_client = compute_v1.RegionsClient()
            regions_request = compute_v1.ListRegionsRequest(project=project_id)
            regions_list = regions_client.list(request=regions_request)

            for region_obj in regions_list:
                region_name = region_obj.name
                try:
                    # Regional HTTP Target Proxies
                    try:
                        regional_http_client = compute_v1.RegionTargetHttpProxiesClient()
                        regional_http_request = compute_v1.ListRegionTargetHttpProxiesRequest(
                            project=project_id,
                            region=region_name
                        )
                        regional_http_list = regional_http_client.list(request=regional_http_request)

                        for proxy in regional_http_list:
                            proxy_data = {
                                "name": proxy.name,
                                "id": f"{project_id}/{region_name}/{proxy.name}",
                                "project": project_id,
                                "region": region_name,
                                "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                                "proxy_type": "http",
                                "scope": "regional",

                                # Core properties
                                "url_map": proxy.url_map.split('/')[-1] if hasattr(proxy, 'url_map') and proxy.url_map else None,
                                "ssl_certificates": [],  # Regional HTTP proxies don't have SSL certificates
                                "ssl_policy": None,  # Regional HTTP proxies don't have SSL policy
                                "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,
                                "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,

                                # Metadata
                                "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                                "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                                "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                                # For resource naming
                                "name_sanitized": proxy.name.replace('-', '_').lower(),
                                "terraform_resource_type": "google_compute_region_target_http_proxy"
                            }
                            target_proxies.append(proxy_data)

                    except exceptions.GoogleAPIError as e:
                        if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                            pass  # Skip regions that don't support this resource

                    # Regional HTTPS Target Proxies
                    try:
                        regional_https_client = compute_v1.RegionTargetHttpsProxiesClient()
                        regional_https_request = compute_v1.ListRegionTargetHttpsProxiesRequest(
                            project=project_id,
                            region=region_name
                        )
                        regional_https_list = regional_https_client.list(request=regional_https_request)

                        for proxy in regional_https_list:
                            proxy_data = {
                                "name": proxy.name,
                                "id": f"{project_id}/{region_name}/{proxy.name}",
                                "project": project_id,
                                "region": region_name,
                                "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                                "proxy_type": "https",
                                "scope": "regional",

                                # Core properties
                                "url_map": proxy.url_map.split('/')[-1] if hasattr(proxy, 'url_map') and proxy.url_map else None,
                                "ssl_certificates": [cert.split('/')[-1] for cert in proxy.ssl_certificates] if hasattr(proxy, 'ssl_certificates') and proxy.ssl_certificates else [],
                                "ssl_policy": proxy.ssl_policy.split('/')[-1] if hasattr(proxy, 'ssl_policy') and proxy.ssl_policy else None,
                                "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,
                                "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                                "certificate_map": proxy.certificate_map.split('/')[-1] if hasattr(proxy, 'certificate_map') and proxy.certificate_map else None,
                                "server_tls_policy": proxy.server_tls_policy.split('/')[-1] if hasattr(proxy, 'server_tls_policy') and proxy.server_tls_policy else None,

                                # Metadata
                                "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                                "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                                "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                                # For resource naming
                                "name_sanitized": proxy.name.replace('-', '_').lower(),
                                "terraform_resource_type": "google_compute_region_target_https_proxy"
                            }
                            target_proxies.append(proxy_data)

                    except exceptions.GoogleAPIError as e:
                        if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                            pass  # Skip regions that don't support this resource

                    # Regional TCP Target Proxies
                    try:
                        regional_tcp_client = compute_v1.RegionTargetTcpProxiesClient()
                        regional_tcp_request = compute_v1.ListRegionTargetTcpProxiesRequest(
                            project=project_id,
                            region=region_name
                        )
                        regional_tcp_list = regional_tcp_client.list(request=regional_tcp_request)

                        for proxy in regional_tcp_list:
                            proxy_data = {
                                "name": proxy.name,
                                "id": f"{project_id}/{region_name}/{proxy.name}",
                                "project": project_id,
                                "region": region_name,
                                "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                                "proxy_type": "tcp",
                                "scope": "regional",

                                # Core properties
                                "backend_service": proxy.service.split('/')[-1] if hasattr(proxy, 'service') and proxy.service else None,
                                "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                                "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,

                                # Metadata
                                "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                                "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                                "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                                # For resource naming
                                "name_sanitized": proxy.name.replace('-', '_').lower(),
                                "terraform_resource_type": "google_compute_region_target_tcp_proxy"
                            }
                            target_proxies.append(proxy_data)

                    except exceptions.GoogleAPIError as e:
                        if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                            pass  # Skip regions that don't support this resource

                except exceptions.GoogleAPIError as e:
                    # Skip regions that have errors (e.g., disabled APIs)
                    if "not found" not in str(e).lower():
                        typer.echo(f"Warning: Could not scan region {region_name}: {str(e)}", err=True)
                    continue
        else:
            # Scan specific region
            # Regional HTTP Target Proxies
            try:
                regional_http_client = compute_v1.RegionTargetHttpProxiesClient()
                regional_http_request = compute_v1.ListRegionTargetHttpProxiesRequest(
                    project=project_id,
                    region=region
                )
                regional_http_list = regional_http_client.list(request=regional_http_request)

                for proxy in regional_http_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{region}/{proxy.name}",
                        "project": project_id,
                        "region": region,
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "http",
                        "scope": "regional",

                        # Core properties
                        "url_map": proxy.url_map.split('/')[-1] if hasattr(proxy, 'url_map') and proxy.url_map else None,
                        "ssl_certificates": [],
                        "ssl_policy": None,
                        "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_region_target_http_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan regional HTTP target proxies in {region}: {str(e)}", err=True)

            # Regional HTTPS Target Proxies
            try:
                regional_https_client = compute_v1.RegionTargetHttpsProxiesClient()
                regional_https_request = compute_v1.ListRegionTargetHttpsProxiesRequest(
                    project=project_id,
                    region=region
                )
                regional_https_list = regional_https_client.list(request=regional_https_request)

                for proxy in regional_https_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{region}/{proxy.name}",
                        "project": project_id,
                        "region": region,
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "https",
                        "scope": "regional",

                        # Core properties
                        "url_map": proxy.url_map.split('/')[-1] if hasattr(proxy, 'url_map') and proxy.url_map else None,
                        "ssl_certificates": [cert.split('/')[-1] for cert in proxy.ssl_certificates] if hasattr(proxy, 'ssl_certificates') and proxy.ssl_certificates else [],
                        "ssl_policy": proxy.ssl_policy.split('/')[-1] if hasattr(proxy, 'ssl_policy') and proxy.ssl_policy else None,
                        "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                        "certificate_map": proxy.certificate_map.split('/')[-1] if hasattr(proxy, 'certificate_map') and proxy.certificate_map else None,
                        "server_tls_policy": proxy.server_tls_policy.split('/')[-1] if hasattr(proxy, 'server_tls_policy') and proxy.server_tls_policy else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_region_target_https_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan regional HTTPS target proxies in {region}: {str(e)}", err=True)

            # Regional TCP Target Proxies
            try:
                regional_tcp_client = compute_v1.RegionTargetTcpProxiesClient()
                regional_tcp_request = compute_v1.ListRegionTargetTcpProxiesRequest(
                    project=project_id,
                    region=region
                )
                regional_tcp_list = regional_tcp_client.list(request=regional_tcp_request)

                for proxy in regional_tcp_list:
                    proxy_data = {
                        "name": proxy.name,
                        "id": f"{project_id}/{region}/{proxy.name}",
                        "project": project_id,
                        "region": region,
                        "description": proxy.description if hasattr(proxy, 'description') and proxy.description else "",
                        "proxy_type": "tcp",
                        "scope": "regional",

                        # Core properties
                        "backend_service": proxy.service.split('/')[-1] if hasattr(proxy, 'service') and proxy.service else None,
                        "proxy_header": proxy.proxy_header if hasattr(proxy, 'proxy_header') and proxy.proxy_header else None,
                        "proxy_bind": proxy.proxy_bind if hasattr(proxy, 'proxy_bind') else None,

                        # Metadata
                        "creation_timestamp": proxy.creation_timestamp if hasattr(proxy, 'creation_timestamp') else None,
                        "fingerprint": proxy.fingerprint if hasattr(proxy, 'fingerprint') else None,
                        "self_link": proxy.self_link if hasattr(proxy, 'self_link') else None,

                        # For resource naming
                        "name_sanitized": proxy.name.replace('-', '_').lower(),
                        "terraform_resource_type": "google_compute_region_target_tcp_proxy"
                    }
                    target_proxies.append(proxy_data)

            except exceptions.GoogleAPIError as e:
                if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                    typer.echo(f"Warning: Could not scan regional TCP target proxies in {region}: {str(e)}", err=True)

    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching target proxies: {str(e)}", err=True)
        raise typer.Exit(code=1)

    return target_proxies

@app.command("scan")
def scan_target_proxies(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP target proxies and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan

    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)

    if with_deps:
        typer.echo("Scanning GCP target proxies with dependencies...")
        recursive_scan(
            "gcp_target_proxy",
            output_dir=output_dir,
            project_id=project_id,
            region=region
        )
    else:
        typer.echo(f"Scanning for GCP target proxies in project '{project_id}'...")
        if region:
            typer.echo(f"Region: {region}")
        else:
            typer.echo("Scope: Global and All Regions")

        target_proxy_data = get_target_proxy_data(project_id, region)

        if not target_proxy_data:
            typer.echo("No target proxies found.")
            return

        # Group by Terraform resource type for different files
        by_resource_type = {}
        for proxy in target_proxy_data:
            resource_type = proxy["terraform_resource_type"]
            if resource_type not in by_resource_type:
                by_resource_type[resource_type] = []
            by_resource_type[resource_type].append(proxy)

        # Generate files for each resource type
        for resource_type, proxies in by_resource_type.items():
            # Map Terraform resource type to terraback template name
            template_name_map = {
                "google_compute_target_http_proxy": "gcp_target_http_proxy",
                "google_compute_target_https_proxy": "gcp_target_https_proxy",
                "google_compute_target_ssl_proxy": "gcp_target_ssl_proxy",
                "google_compute_target_tcp_proxy": "gcp_target_tcp_proxy",
                "google_compute_region_target_http_proxy": "gcp_region_target_http_proxy",
                "google_compute_region_target_https_proxy": "gcp_region_target_https_proxy",
                "google_compute_region_target_tcp_proxy": "gcp_region_target_tcp_proxy"
            }

            template_name = template_name_map.get(resource_type, resource_type)
            output_file = output_dir / f"{template_name}.tf"

            generate_tf(proxies, template_name, output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(proxies)} {template_name.replace('_', ' ')} -> {output_file}")

            # Generate import file
            generate_imports_file(
                template_name,
                proxies,
                remote_resource_id_key="id",
                output_dir=output_dir,
                provider="gcp"
            )

# Scan function for cross-scan registry
def scan_gcp_target_proxies(output_dir: Path, project_id: Optional[str] = None, region: Optional[str] = None, **kwargs):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    if not project_id:
        typer.echo("Error: No GCP project found", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"[Cross-scan] Scanning GCP target proxies in project {project_id}")

    target_proxy_data = get_target_proxy_data(project_id, region)

    if target_proxy_data:
        # Group by Terraform resource type for different files
        by_resource_type = {}
        for proxy in target_proxy_data:
            resource_type = proxy["terraform_resource_type"]
            if resource_type not in by_resource_type:
                by_resource_type[resource_type] = []
            by_resource_type[resource_type].append(proxy)

        # Generate files for each resource type
        for resource_type, proxies in by_resource_type.items():
            # Map Terraform resource type to terraback template name
            template_name_map = {
                "google_compute_target_http_proxy": "gcp_target_http_proxy",
                "google_compute_target_https_proxy": "gcp_target_https_proxy",
                "google_compute_target_ssl_proxy": "gcp_target_ssl_proxy",
                "google_compute_target_tcp_proxy": "gcp_target_tcp_proxy",
                "google_compute_region_target_http_proxy": "gcp_region_target_http_proxy",
                "google_compute_region_target_https_proxy": "gcp_region_target_https_proxy",
                "google_compute_region_target_tcp_proxy": "gcp_region_target_tcp_proxy"
            }

            template_name = template_name_map.get(resource_type, resource_type)
            output_file = output_dir / f"{template_name}.tf"

            generate_tf(proxies, template_name, output_file, provider="gcp")
            generate_imports_file(
                template_name,
                proxies,
                remote_resource_id_key="id",
                output_dir=output_dir,
                provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(proxies)} {template_name.replace('_', ' ')}")

@app.command("list")
def list_target_proxies(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    proxy_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by proxy type: http, https, ssl, tcp")
):
    """List all GCP target proxy resources previously generated."""
    proxy_types = [
        ("gcp_target_http_proxy", "Global HTTP Target Proxies"),
        ("gcp_target_https_proxy", "Global HTTPS Target Proxies"),
        ("gcp_target_ssl_proxy", "Global SSL Target Proxies"),
        ("gcp_target_tcp_proxy", "Global TCP Target Proxies"),
        ("gcp_region_target_http_proxy", "Regional HTTP Target Proxies"),
        ("gcp_region_target_https_proxy", "Regional HTTPS Target Proxies"),
        ("gcp_region_target_tcp_proxy", "Regional TCP Target Proxies")
    ]

    if proxy_type:
        # Filter by specific proxy type
        filtered_types = [
            (template, name) for template, name in proxy_types
            if proxy_type.lower() in template.lower()
        ]
        if not filtered_types:
            typer.echo(f"No proxy type matching '{proxy_type}' found.")
            return
        proxy_types = filtered_types

    for template_name, display_name in proxy_types:
        typer.echo(f"\n{display_name}:")
        ImportManager(output_dir, template_name).list_all()

@app.command("import")
def import_target_proxy(
    proxy_id: str = typer.Argument(..., help="GCP target proxy ID (project/name for global, project/region/name for regional)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    proxy_type: Optional[str] = typer.Option(None, "--type", "-t", help="Proxy type: http, https, ssl, tcp (auto-detected if not specified)"),
    scope: Optional[str] = typer.Option(None, "--scope", "-s", help="Scope: global or regional (auto-detected if not specified)")
):
    """Run terraform import for a specific GCP target proxy."""
    # Parse the proxy_id to determine scope and auto-detect type if needed
    parts = proxy_id.split('/')

    # Auto-detect scope based on ID format if not specified
    if scope is None:
        if len(parts) == 2:
            scope = "global"
        elif len(parts) == 3:
            scope = "regional"
        else:
            typer.echo("Error: Invalid proxy ID format. Expected project/name for global or project/region/name for regional.", err=True)
            raise typer.Exit(code=1)

    # If proxy type is not specified, we need to try to auto-detect or ask user
    if proxy_type is None:
        typer.echo("Error: Proxy type must be specified (--type http|https|ssl|tcp) as it cannot be auto-detected from ID alone.", err=True)
        raise typer.Exit(code=1)

    # Map to template name
    template_name_map = {
        ("http", "global"): "gcp_target_http_proxy",
        ("https", "global"): "gcp_target_https_proxy",
        ("ssl", "global"): "gcp_target_ssl_proxy",
        ("tcp", "global"): "gcp_target_tcp_proxy",
        ("http", "regional"): "gcp_region_target_http_proxy",
        ("https", "regional"): "gcp_region_target_https_proxy",
        ("tcp", "regional"): "gcp_region_target_tcp_proxy"
    }

    # Note: Regional SSL proxies don't exist in GCP
    if proxy_type.lower() == "ssl" and scope == "regional":
        typer.echo("Error: Regional SSL target proxies do not exist in GCP.", err=True)
        raise typer.Exit(code=1)

    template_name = template_name_map.get((proxy_type.lower(), scope))
    if not template_name:
        typer.echo(f"Error: Invalid combination of proxy type '{proxy_type}' and scope '{scope}'.", err=True)
        raise typer.Exit(code=1)

    ImportManager(output_dir, template_name).find_and_import(proxy_id)
