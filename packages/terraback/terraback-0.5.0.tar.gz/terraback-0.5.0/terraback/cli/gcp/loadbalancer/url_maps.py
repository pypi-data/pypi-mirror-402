# terraback/cli/gcp/loadbalancer/url_maps.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="url-map", help="Scan and import GCP URL maps.")

def _extract_url_redirect(redirect) -> Optional[Dict[str, Any]]:
    """Extract URL redirect data from a GCP URL redirect object."""
    if not redirect:
        return None

    return {
        "host_redirect": redirect.host_redirect if hasattr(redirect, 'host_redirect') and redirect.host_redirect else None,
        "path_redirect": redirect.path_redirect if hasattr(redirect, 'path_redirect') and redirect.path_redirect else None,
        "prefix_redirect": redirect.prefix_redirect if hasattr(redirect, 'prefix_redirect') and redirect.prefix_redirect else None,
        "redirect_response_code": redirect.redirect_response_code if hasattr(redirect, 'redirect_response_code') and redirect.redirect_response_code else None,
        "https_redirect": redirect.https_redirect if hasattr(redirect, 'https_redirect') else None,
        "strip_query": redirect.strip_query if hasattr(redirect, 'strip_query') else None
    }

def _extract_route_action(route_action) -> Optional[Dict[str, Any]]:
    """Extract route action data from a GCP route action object."""
    if not route_action:
        return None

    action_data = {
        "weighted_backend_services": [],
        "url_rewrite": None,
        "timeout": None,
        "retry_policy": None,
        "request_mirror_policy": None,
        "cors_policy": None,
        "fault_injection_policy": None
    }

    # Process weighted backend services
    if hasattr(route_action, 'weighted_backend_services') and route_action.weighted_backend_services:
        for wbs in route_action.weighted_backend_services:
            wbs_data = {
                "backend_service": wbs.backend_service.split('/')[-1] if hasattr(wbs, 'backend_service') and wbs.backend_service else None,
                "weight": wbs.weight if hasattr(wbs, 'weight') else None,
                "header_action": None
            }

            # Process header action for weighted backend service
            if hasattr(wbs, 'header_action') and wbs.header_action:
                wbs_data["header_action"] = _extract_header_action(wbs.header_action)

            action_data["weighted_backend_services"].append(wbs_data)

    # Process URL rewrite
    if hasattr(route_action, 'url_rewrite') and route_action.url_rewrite:
        url_rewrite = route_action.url_rewrite
        action_data["url_rewrite"] = {
            "path_prefix_rewrite": url_rewrite.path_prefix_rewrite if hasattr(url_rewrite, 'path_prefix_rewrite') and url_rewrite.path_prefix_rewrite else None,
            "host_rewrite": url_rewrite.host_rewrite if hasattr(url_rewrite, 'host_rewrite') and url_rewrite.host_rewrite else None
        }

    # Process timeout
    if hasattr(route_action, 'timeout') and route_action.timeout:
        timeout = route_action.timeout
        action_data["timeout"] = {
            "seconds": timeout.seconds if hasattr(timeout, 'seconds') else None,
            "nanos": timeout.nanos if hasattr(timeout, 'nanos') else None
        }

    return action_data

def _extract_header_action(header_action) -> Optional[Dict[str, Any]]:
    """Extract header action data from a GCP header action object."""
    if not header_action:
        return None

    action_data = {
        "request_headers_to_add": [],
        "request_headers_to_remove": [],
        "response_headers_to_add": [],
        "response_headers_to_remove": []
    }

    # Process request headers to add
    if hasattr(header_action, 'request_headers_to_add') and header_action.request_headers_to_add:
        for header in header_action.request_headers_to_add:
            action_data["request_headers_to_add"].append({
                "header_name": header.header_name if hasattr(header, 'header_name') else None,
                "header_value": header.header_value if hasattr(header, 'header_value') and header.header_value else None,
                "replace": header.replace if hasattr(header, 'replace') else None
            })

    # Process request headers to remove
    if hasattr(header_action, 'request_headers_to_remove') and header_action.request_headers_to_remove:
        action_data["request_headers_to_remove"] = list(header_action.request_headers_to_remove)

    # Process response headers to add
    if hasattr(header_action, 'response_headers_to_add') and header_action.response_headers_to_add:
        for header in header_action.response_headers_to_add:
            action_data["response_headers_to_add"].append({
                "header_name": header.header_name if hasattr(header, 'header_name') else None,
                "header_value": header.header_value if hasattr(header, 'header_value') and header.header_value else None,
                "replace": header.replace if hasattr(header, 'replace') else None
            })

    # Process response headers to remove
    if hasattr(header_action, 'response_headers_to_remove') and header_action.response_headers_to_remove:
        action_data["response_headers_to_remove"] = list(header_action.response_headers_to_remove)

    return action_data

def _process_url_map_common_data(url_map, project_id: str, region: Optional[str] = None) -> Dict[str, Any]:
    """Process common URL map data that applies to both global and regional URL maps."""
    url_map_data = {
        "name": url_map.name,
        "id": f"{project_id}/{region}/{url_map.name}" if region else f"{project_id}/{url_map.name}",
        "project": project_id,
        "region": region,
        "description": url_map.description if hasattr(url_map, 'description') and url_map.description else "",

        # Core URL map properties
        "default_service": url_map.default_service.split('/')[-1] if hasattr(url_map, 'default_service') and url_map.default_service else None,
        "default_url_redirect": _extract_url_redirect(getattr(url_map, 'default_url_redirect', None)),

        # Host rules for routing based on hostname
        "host_rules": [],

        # Path matchers for complex routing logic
        "path_matchers": [],

        # Tests for validation
        "tests": [],

        # Header action
        "header_action": _extract_header_action(getattr(url_map, 'header_action', None)),

        # Default route action
        "default_route_action": _extract_route_action(getattr(url_map, 'default_route_action', None)),

        # Labels and metadata
        "labels": dict(url_map.labels) if hasattr(url_map, 'labels') and url_map.labels else {},
        "fingerprint": url_map.fingerprint if hasattr(url_map, 'fingerprint') else None,
        "creation_timestamp": url_map.creation_timestamp if hasattr(url_map, 'creation_timestamp') else None,

        # For resource naming and identification
        "name_sanitized": url_map.name.replace('-', '_').lower(),
        "url_map_type": "regional" if region else "global"
    }

    # Process host rules
    if hasattr(url_map, 'host_rules') and url_map.host_rules:
        for host_rule in url_map.host_rules:
            host_rule_data = {
                "description": host_rule.description if hasattr(host_rule, 'description') and host_rule.description else "",
                "hosts": list(host_rule.hosts) if hasattr(host_rule, 'hosts') and host_rule.hosts else [],
                "path_matcher": host_rule.path_matcher if hasattr(host_rule, 'path_matcher') and host_rule.path_matcher else None
            }
            url_map_data["host_rules"].append(host_rule_data)

    # Process path matchers
    if hasattr(url_map, 'path_matchers') and url_map.path_matchers:
        for path_matcher in url_map.path_matchers:
            path_matcher_data = {
                "name": path_matcher.name if hasattr(path_matcher, 'name') else None,
                "description": path_matcher.description if hasattr(path_matcher, 'description') and path_matcher.description else "",
                "default_service": path_matcher.default_service.split('/')[-1] if hasattr(path_matcher, 'default_service') and path_matcher.default_service else None,
                "default_url_redirect": _extract_url_redirect(getattr(path_matcher, 'default_url_redirect', None)),
                "default_route_action": _extract_route_action(getattr(path_matcher, 'default_route_action', None)),
                "path_rules": [],
                "route_rules": [],
                "header_action": _extract_header_action(getattr(path_matcher, 'header_action', None))
            }

            # Process path rules
            if hasattr(path_matcher, 'path_rules') and path_matcher.path_rules:
                for path_rule in path_matcher.path_rules:
                    path_rule_data = {
                        "paths": list(path_rule.paths) if hasattr(path_rule, 'paths') and path_rule.paths else [],
                        "service": path_rule.service.split('/')[-1] if hasattr(path_rule, 'service') and path_rule.service else None,
                        "url_redirect": _extract_url_redirect(getattr(path_rule, 'url_redirect', None)),
                        "route_action": _extract_route_action(getattr(path_rule, 'route_action', None))
                    }
                    path_matcher_data["path_rules"].append(path_rule_data)

            # Process route rules (for advanced routing)
            if hasattr(path_matcher, 'route_rules') and path_matcher.route_rules:
                for route_rule in path_matcher.route_rules:
                    route_rule_data = {
                        "priority": route_rule.priority if hasattr(route_rule, 'priority') else None,
                        "description": route_rule.description if hasattr(route_rule, 'description') and route_rule.description else "",
                        "match_rules": [],
                        "service": route_rule.service.split('/')[-1] if hasattr(route_rule, 'service') and route_rule.service else None,
                        "url_redirect": _extract_url_redirect(getattr(route_rule, 'url_redirect', None)),
                        "route_action": _extract_route_action(getattr(route_rule, 'route_action', None)),
                        "header_action": _extract_header_action(getattr(route_rule, 'header_action', None))
                    }

                    # Process match rules
                    if hasattr(route_rule, 'match_rules') and route_rule.match_rules:
                        for match_rule in route_rule.match_rules:
                            match_rule_data = {
                                "full_path_match": match_rule.full_path_match if hasattr(match_rule, 'full_path_match') and match_rule.full_path_match else None,
                                "prefix_match": match_rule.prefix_match if hasattr(match_rule, 'prefix_match') and match_rule.prefix_match else None,
                                "regex_match": match_rule.regex_match if hasattr(match_rule, 'regex_match') and match_rule.regex_match else None,
                                "ignore_case": match_rule.ignore_case if hasattr(match_rule, 'ignore_case') else None,
                                "header_matches": [],
                                "query_parameter_matches": [],
                                "metadata_filters": []
                            }

                            # Process header matches
                            if hasattr(match_rule, 'header_matches') and match_rule.header_matches:
                                for header_match in match_rule.header_matches:
                                    header_match_data = {
                                        "header_name": header_match.header_name if hasattr(header_match, 'header_name') else None,
                                        "exact_match": header_match.exact_match if hasattr(header_match, 'exact_match') and header_match.exact_match else None,
                                        "regex_match": header_match.regex_match if hasattr(header_match, 'regex_match') and header_match.regex_match else None,
                                        "range_match": None,
                                        "present_match": header_match.present_match if hasattr(header_match, 'present_match') else None,
                                        "prefix_match": header_match.prefix_match if hasattr(header_match, 'prefix_match') and header_match.prefix_match else None,
                                        "suffix_match": header_match.suffix_match if hasattr(header_match, 'suffix_match') and header_match.suffix_match else None,
                                        "invert_match": header_match.invert_match if hasattr(header_match, 'invert_match') else None
                                    }

                                    # Process range match
                                    if hasattr(header_match, 'range_match') and header_match.range_match:
                                        range_match = header_match.range_match
                                        header_match_data["range_match"] = {
                                            "range_start": range_match.range_start if hasattr(range_match, 'range_start') else None,
                                            "range_end": range_match.range_end if hasattr(range_match, 'range_end') else None
                                        }

                                    match_rule_data["header_matches"].append(header_match_data)

                            # Process query parameter matches
                            if hasattr(match_rule, 'query_parameter_matches') and match_rule.query_parameter_matches:
                                for query_match in match_rule.query_parameter_matches:
                                    query_match_data = {
                                        "name": query_match.name if hasattr(query_match, 'name') else None,
                                        "exact_match": query_match.exact_match if hasattr(query_match, 'exact_match') and query_match.exact_match else None,
                                        "regex_match": query_match.regex_match if hasattr(query_match, 'regex_match') and query_match.regex_match else None,
                                        "present_match": query_match.present_match if hasattr(query_match, 'present_match') else None
                                    }
                                    match_rule_data["query_parameter_matches"].append(query_match_data)

                            route_rule_data["match_rules"].append(match_rule_data)

                    path_matcher_data["route_rules"].append(route_rule_data)

            url_map_data["path_matchers"].append(path_matcher_data)

    # Process tests
    if hasattr(url_map, 'tests') and url_map.tests:
        for test in url_map.tests:
            test_data = {
                "description": test.description if hasattr(test, 'description') and test.description else "",
                "host": test.host if hasattr(test, 'host') and test.host else None,
                "path": test.path if hasattr(test, 'path') and test.path else None,
                "service": test.service.split('/')[-1] if hasattr(test, 'service') and test.service else None,
                "headers": []
            }

            # Process headers for test
            if hasattr(test, 'headers') and test.headers:
                for header in test.headers:
                    header_data = {
                        "name": header.name if hasattr(header, 'name') else None,
                        "value": header.value if hasattr(header, 'value') and header.value else None
                    }
                    test_data["headers"].append(header_data)

            url_map_data["tests"].append(test_data)

    return url_map_data

def get_url_map_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch URL map data from GCP."""
    url_maps = []

    try:
        if not region:
            # Scan global URL maps
            typer.echo("Scanning global URL maps...")
            client = compute_v1.UrlMapsClient()
            request = compute_v1.ListUrlMapsRequest(project=project_id)
            url_map_list = client.list(request=request)

            global_count = 0
            for url_map in url_map_list:
                url_map_data = _process_url_map_common_data(url_map, project_id)
                url_maps.append(url_map_data)
                global_count += 1

            if global_count > 0:
                typer.echo(f"Found {global_count} global URL maps")

        else:
            # Scan regional URL maps in specific region
            typer.echo(f"Scanning regional URL maps in region {region}...")
            client = compute_v1.RegionUrlMapsClient()
            request = compute_v1.ListRegionUrlMapsRequest(
                project=project_id,
                region=region
            )
            url_map_list = client.list(request=request)

            regional_count = 0
            for url_map in url_map_list:
                url_map_data = _process_url_map_common_data(url_map, project_id, region)
                url_maps.append(url_map_data)
                regional_count += 1

            if regional_count > 0:
                typer.echo(f"Found {regional_count} regional URL maps in {region}")

        # Also scan regional URL maps across all regions when not specifying a specific region
        if not region:
            # Scan all regions for regional URL maps
            typer.echo("Scanning regional URL maps across all regions...")
            regions_client = compute_v1.RegionsClient()
            regions_request = compute_v1.ListRegionsRequest(project=project_id)
            regions_list = regions_client.list(request=regions_request)

            regional_client = compute_v1.RegionUrlMapsClient()
            total_regional = 0

            for region_obj in regions_list:
                region_name = region_obj.name
                try:
                    regional_request = compute_v1.ListRegionUrlMapsRequest(
                        project=project_id,
                        region=region_name
                    )
                    regional_url_map_list = regional_client.list(request=regional_request)

                    region_count = 0
                    for url_map in regional_url_map_list:
                        url_map_data = _process_url_map_common_data(url_map, project_id, region_name)
                        url_maps.append(url_map_data)
                        region_count += 1
                        total_regional += 1

                    if region_count > 0:
                        typer.echo(f"Found {region_count} regional URL maps in {region_name}")

                except exceptions.GoogleAPIError as e:
                    # Skip regions that have errors (e.g., disabled APIs)
                    if "not found" not in str(e).lower() and "not enabled" not in str(e).lower():
                        typer.echo(f"Warning: Could not scan region {region_name}: {str(e)}", err=True)
                    continue

            if total_regional > 0:
                typer.echo(f"Total regional URL maps found: {total_regional}")

    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching URL maps: {str(e)}", err=True)
        raise typer.Exit(code=1)
    except Exception as e:
        typer.echo(f"Unexpected error while fetching URL maps: {str(e)}", err=True)
        raise typer.Exit(code=1)

    return url_maps

@app.command("scan")
def scan_url_maps(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP URL maps and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan

    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)

    if with_deps:
        typer.echo("Scanning GCP URL maps with dependencies...")
        recursive_scan(
            "gcp_url_map",
            output_dir=output_dir,
            project_id=project_id,
            region=region
        )
    else:
        typer.echo(f"Scanning for GCP URL maps in project '{project_id}'...")
        if region:
            typer.echo(f"Region: {region}")
        else:
            typer.echo("Scope: Global and all regions")

        url_map_data = get_url_map_data(project_id, region)

        if not url_map_data:
            typer.echo("No URL maps found.")
            return

        # Separate global and regional URL maps for different resource types
        global_url_maps = [url_map for url_map in url_map_data if url_map["url_map_type"] == "global"]
        regional_url_maps = [url_map for url_map in url_map_data if url_map["url_map_type"] == "regional"]

        # Generate Terraform files for global URL maps
        if global_url_maps:
            output_file = output_dir / "gcp_url_map.tf"
            generate_tf(global_url_maps, "gcp_url_map", output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(global_url_maps)} global URL maps -> {output_file}")

            # Generate import file for global URL maps
            generate_imports_file(
                "gcp_url_map",
                global_url_maps,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )

        # Generate Terraform files for regional URL maps
        if regional_url_maps:
            output_file = output_dir / "gcp_region_url_map.tf"
            generate_tf(regional_url_maps, "gcp_region_url_map", output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(regional_url_maps)} regional URL maps -> {output_file}")

            # Generate import file for regional URL maps
            generate_imports_file(
                "gcp_region_url_map",
                regional_url_maps,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )

# Scan function for cross-scan registry
def scan_gcp_url_maps(
    output_dir: Path,
    project_id: Optional[str] = None,
    region: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    if not project_id:
        typer.echo("Error: No GCP project found", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"[Cross-scan] Scanning GCP URL maps in project {project_id}")

    url_map_data = get_url_map_data(project_id, region)

    if url_map_data:
        # Separate global and regional URL maps for different resource types
        global_url_maps = [url_map for url_map in url_map_data if url_map["url_map_type"] == "global"]
        regional_url_maps = [url_map for url_map in url_map_data if url_map["url_map_type"] == "regional"]

        # Generate files for global URL maps
        if global_url_maps:
            output_file = output_dir / "gcp_url_map.tf"
            generate_tf(global_url_maps, "gcp_url_map", output_file, provider="gcp")
            generate_imports_file(
                "gcp_url_map",
                global_url_maps,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(global_url_maps)} global GCP URL maps")

        # Generate files for regional URL maps
        if regional_url_maps:
            output_file = output_dir / "gcp_region_url_map.tf"
            generate_tf(regional_url_maps, "gcp_region_url_map", output_file, provider="gcp")
            generate_imports_file(
                "gcp_region_url_map",
                regional_url_maps,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(regional_url_maps)} regional GCP URL maps")

@app.command("list")
def list_url_maps(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    url_map_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by URL map type: global or regional")
):
    """List all GCP URL map resources previously generated."""
    if url_map_type == "global":
        typer.echo("Global URL maps:")
        ImportManager(output_dir, "gcp_url_map").list_all()
    elif url_map_type == "regional":
        typer.echo("Regional URL maps:")
        ImportManager(output_dir, "gcp_region_url_map").list_all()
    else:
        typer.echo("Global URL maps:")
        ImportManager(output_dir, "gcp_url_map").list_all()
        typer.echo("\nRegional URL maps:")
        ImportManager(output_dir, "gcp_region_url_map").list_all()

@app.command("import")
def import_url_map(
    url_map_id: str = typer.Argument(..., help="GCP URL map ID (project/name for global, project/region/name for regional)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    url_map_type: Optional[str] = typer.Option(None, "--type", "-t", help="URL map type: global or regional (auto-detected if not specified)")
):
    """Run terraform import for a specific GCP URL map."""
    # Auto-detect URL map type based on ID format if not specified
    if url_map_type is None:
        parts = url_map_id.split('/')
        if len(parts) == 2:
            url_map_type = "global"
        elif len(parts) == 3:
            url_map_type = "regional"
        else:
            typer.echo("Error: Invalid URL map ID format. Expected project/name for global or project/region/name for regional.", err=True)
            raise typer.Exit(code=1)

    if url_map_type == "global":
        ImportManager(output_dir, "gcp_url_map").find_and_import(url_map_id)
    elif url_map_type == "regional":
        ImportManager(output_dir, "gcp_region_url_map").find_and_import(url_map_id)
    else:
        typer.echo("Error: URL map type must be 'global' or 'regional'", err=True)
        raise typer.Exit(code=1)
