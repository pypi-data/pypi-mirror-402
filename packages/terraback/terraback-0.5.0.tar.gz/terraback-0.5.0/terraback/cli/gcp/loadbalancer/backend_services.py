# terraback/cli/gcp/loadbalancer/backend_services.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="backend-service", help="Scan and import GCP backend services.")

def get_backend_service_data(project_id: str, region: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch backend service data from GCP."""
    backend_services = []

    try:
        if not region:
            # Scan global backend services
            client = compute_v1.BackendServicesClient()
            request = compute_v1.ListBackendServicesRequest(project=project_id)
            service_list = client.list(request=request)

            for service in service_list:
                service_data = {
                    "name": service.name,
                    "id": f"{project_id}/{service.name}",
                    "project": project_id,
                    "region": None,  # Global backend services don't have a region
                    "description": service.description if hasattr(service, 'description') and service.description else "",

                    # Core backend service properties
                    "protocol": service.protocol if hasattr(service, 'protocol') and service.protocol else None,
                    "port": service.port if hasattr(service, 'port') else None,
                    "port_name": service.port_name if hasattr(service, 'port_name') and service.port_name else None,
                    "timeout_sec": service.timeout_sec if hasattr(service, 'timeout_sec') else None,
                    "enable_cdn": service.enable_c_d_n if hasattr(service, 'enable_c_d_n') else False,
                    "session_affinity": service.session_affinity if hasattr(service, 'session_affinity') and service.session_affinity else None,
                    "affinity_cookie_ttl_sec": service.affinity_cookie_ttl_sec if hasattr(service, 'affinity_cookie_ttl_sec') else None,
                    "load_balancing_scheme": service.load_balancing_scheme if hasattr(service, 'load_balancing_scheme') and service.load_balancing_scheme else None,

                    # Health checks
                    "health_checks": [hc.split('/')[-1] for hc in service.health_checks] if hasattr(service, 'health_checks') and service.health_checks else [],

                    # Backends
                    "backends": [],

                    # Connection draining
                    "connection_draining": None,

                    # CDN policy
                    "cdn_policy": None,

                    # IAP (Identity-Aware Proxy)
                    "iap": None,

                    # Security policy
                    "security_policy": service.security_policy.split('/')[-1] if hasattr(service, 'security_policy') and service.security_policy else None,
                    "edge_security_policy": service.edge_security_policy.split('/')[-1] if hasattr(service, 'edge_security_policy') and service.edge_security_policy else None,

                    # Circuit breakers and outlier detection
                    "circuit_breakers": None,
                    "outlier_detection": None,

                    # Custom request headers
                    "custom_request_headers": list(service.custom_request_headers) if hasattr(service, 'custom_request_headers') and service.custom_request_headers else [],
                    "custom_response_headers": list(service.custom_response_headers) if hasattr(service, 'custom_response_headers') and service.custom_response_headers else [],

                    # Log config
                    "log_config": None,

                    # Locality load balancing policy
                    "locality_lb_policy": service.locality_lb_policy if hasattr(service, 'locality_lb_policy') and service.locality_lb_policy else None,

                    # Consistent hash (for session affinity)
                    "consistent_hash": None,

                    # Compression mode
                    "compression_mode": service.compression_mode if hasattr(service, 'compression_mode') and service.compression_mode else None,

                    # Labels and metadata
                    "labels": dict(service.labels) if hasattr(service, 'labels') and service.labels else {},
                    "fingerprint": service.fingerprint if hasattr(service, 'fingerprint') else None,
                    "creation_timestamp": service.creation_timestamp if hasattr(service, 'creation_timestamp') else None,

                    # For resource naming and identification
                    "name_sanitized": service.name.replace('-', '_').lower(),
                    "service_type": "global"
                }

                # Process backends
                if hasattr(service, 'backends') and service.backends:
                    for backend in service.backends:
                        backend_data = {
                            "group": backend.group.split('/')[-1] if hasattr(backend, 'group') and backend.group else None,
                            "balancing_mode": backend.balancing_mode if hasattr(backend, 'balancing_mode') and backend.balancing_mode else None,
                            "max_rate": backend.max_rate if hasattr(backend, 'max_rate') else None,
                            "max_rate_per_instance": backend.max_rate_per_instance if hasattr(backend, 'max_rate_per_instance') else None,
                            "max_rate_per_endpoint": backend.max_rate_per_endpoint if hasattr(backend, 'max_rate_per_endpoint') else None,
                            "max_connections": backend.max_connections if hasattr(backend, 'max_connections') else None,
                            "max_connections_per_instance": backend.max_connections_per_instance if hasattr(backend, 'max_connections_per_instance') else None,
                            "max_connections_per_endpoint": backend.max_connections_per_endpoint if hasattr(backend, 'max_connections_per_endpoint') else None,
                            "max_utilization": backend.max_utilization if hasattr(backend, 'max_utilization') else None,
                            "capacity_scaler": backend.capacity_scaler if hasattr(backend, 'capacity_scaler') else None,
                            "description": backend.description if hasattr(backend, 'description') and backend.description else ""
                        }
                        service_data["backends"].append(backend_data)

                # Process connection draining
                if hasattr(service, 'connection_draining') and service.connection_draining:
                    cd = service.connection_draining
                    service_data["connection_draining"] = {
                        "draining_timeout_sec": cd.draining_timeout_sec if hasattr(cd, 'draining_timeout_sec') else None
                    }

                # Process CDN policy
                if hasattr(service, 'cdn_policy') and service.cdn_policy:
                    cdn = service.cdn_policy
                    service_data["cdn_policy"] = {
                        "cache_key_policy": None,
                        "signed_url_cache_max_age_sec": cdn.signed_url_cache_max_age_sec if hasattr(cdn, 'signed_url_cache_max_age_sec') else None,
                        "default_ttl": cdn.default_ttl if hasattr(cdn, 'default_ttl') else None,
                        "max_ttl": cdn.max_ttl if hasattr(cdn, 'max_ttl') else None,
                        "client_ttl": cdn.client_ttl if hasattr(cdn, 'client_ttl') else None,
                        "negative_caching": cdn.negative_caching if hasattr(cdn, 'negative_caching') else None,
                        "negative_caching_policy": [],
                        "cache_mode": cdn.cache_mode if hasattr(cdn, 'cache_mode') and cdn.cache_mode else None,
                        "serve_while_stale": cdn.serve_while_stale if hasattr(cdn, 'serve_while_stale') else None
                    }

                    # Process cache key policy
                    if hasattr(cdn, 'cache_key_policy') and cdn.cache_key_policy:
                        ckp = cdn.cache_key_policy
                        service_data["cdn_policy"]["cache_key_policy"] = {
                            "include_protocol": ckp.include_protocol if hasattr(ckp, 'include_protocol') else None,
                            "include_host": ckp.include_host if hasattr(ckp, 'include_host') else None,
                            "include_query_string": ckp.include_query_string if hasattr(ckp, 'include_query_string') else None,
                            "query_string_whitelist": list(ckp.query_string_whitelist) if hasattr(ckp, 'query_string_whitelist') and ckp.query_string_whitelist else [],
                            "query_string_blacklist": list(ckp.query_string_blacklist) if hasattr(ckp, 'query_string_blacklist') and ckp.query_string_blacklist else [],
                            "include_http_headers": list(ckp.include_http_headers) if hasattr(ckp, 'include_http_headers') and ckp.include_http_headers else [],
                            "include_named_cookies": list(ckp.include_named_cookies) if hasattr(ckp, 'include_named_cookies') and ckp.include_named_cookies else []
                        }

                    # Process negative caching policy
                    if hasattr(cdn, 'negative_caching_policy') and cdn.negative_caching_policy:
                        for ncp in cdn.negative_caching_policy:
                            service_data["cdn_policy"]["negative_caching_policy"].append({
                                "code": ncp.code if hasattr(ncp, 'code') else None,
                                "ttl": ncp.ttl if hasattr(ncp, 'ttl') else None
                            })

                # Process IAP
                if hasattr(service, 'iap') and service.iap:
                    iap = service.iap
                    service_data["iap"] = {
                        "enabled": iap.enabled if hasattr(iap, 'enabled') else False,
                        "oauth2_client_id": iap.oauth2_client_id if hasattr(iap, 'oauth2_client_id') and iap.oauth2_client_id else None,
                        "oauth2_client_secret": "[SENSITIVE]"  # Don't expose the actual secret
                    }

                # Process circuit breakers
                if hasattr(service, 'circuit_breakers') and service.circuit_breakers:
                    cb = service.circuit_breakers
                    service_data["circuit_breakers"] = {
                        "max_requests_per_connection": cb.max_requests_per_connection if hasattr(cb, 'max_requests_per_connection') else None,
                        "max_connections": cb.max_connections if hasattr(cb, 'max_connections') else None,
                        "max_pending_requests": cb.max_pending_requests if hasattr(cb, 'max_pending_requests') else None,
                        "max_requests": cb.max_requests if hasattr(cb, 'max_requests') else None,
                        "max_retries": cb.max_retries if hasattr(cb, 'max_retries') else None,
                        "connect_timeout": None
                    }

                    if hasattr(cb, 'connect_timeout') and cb.connect_timeout:
                        ct = cb.connect_timeout
                        service_data["circuit_breakers"]["connect_timeout"] = {
                            "seconds": ct.seconds if hasattr(ct, 'seconds') else None,
                            "nanos": ct.nanos if hasattr(ct, 'nanos') else None
                        }

                # Process outlier detection
                if hasattr(service, 'outlier_detection') and service.outlier_detection:
                    od = service.outlier_detection
                    service_data["outlier_detection"] = {
                        "consecutive_errors": od.consecutive_errors if hasattr(od, 'consecutive_errors') else None,
                        "consecutive_gateway_failure": od.consecutive_gateway_failure if hasattr(od, 'consecutive_gateway_failure') else None,
                        "enforcing_consecutive_errors": od.enforcing_consecutive_errors if hasattr(od, 'enforcing_consecutive_errors') else None,
                        "enforcing_consecutive_gateway_failure": od.enforcing_consecutive_gateway_failure if hasattr(od, 'enforcing_consecutive_gateway_failure') else None,
                        "enforcing_success_rate": od.enforcing_success_rate if hasattr(od, 'enforcing_success_rate') else None,
                        "max_ejection_percent": od.max_ejection_percent if hasattr(od, 'max_ejection_percent') else None,
                        "min_health_percent": od.min_health_percent if hasattr(od, 'min_health_percent') else None,
                        "success_rate_minimum_hosts": od.success_rate_minimum_hosts if hasattr(od, 'success_rate_minimum_hosts') else None,
                        "success_rate_request_volume": od.success_rate_request_volume if hasattr(od, 'success_rate_request_volume') else None,
                        "success_rate_stdev_factor": od.success_rate_stdev_factor if hasattr(od, 'success_rate_stdev_factor') else None,
                        "base_ejection_time": None,
                        "interval": None
                    }

                    if hasattr(od, 'base_ejection_time') and od.base_ejection_time:
                        bet = od.base_ejection_time
                        service_data["outlier_detection"]["base_ejection_time"] = {
                            "seconds": bet.seconds if hasattr(bet, 'seconds') else None,
                            "nanos": bet.nanos if hasattr(bet, 'nanos') else None
                        }

                    if hasattr(od, 'interval') and od.interval:
                        interval = od.interval
                        service_data["outlier_detection"]["interval"] = {
                            "seconds": interval.seconds if hasattr(interval, 'seconds') else None,
                            "nanos": interval.nanos if hasattr(interval, 'nanos') else None
                        }

                # Process log config
                if hasattr(service, 'log_config') and service.log_config:
                    lc = service.log_config
                    service_data["log_config"] = {
                        "enable": lc.enable if hasattr(lc, 'enable') else False,
                        "sample_rate": lc.sample_rate if hasattr(lc, 'sample_rate') else None
                    }

                backend_services.append(service_data)
        else:
            # Scan regional backend services in specific region
            client = compute_v1.RegionBackendServicesClient()
            request = compute_v1.ListRegionBackendServicesRequest(
                project=project_id,
                region=region
            )
            service_list = client.list(request=request)

            for service in service_list:
                service_data = {
                    "name": service.name,
                    "id": f"{project_id}/{region}/{service.name}",
                    "project": project_id,
                    "region": region,
                    "description": service.description if hasattr(service, 'description') and service.description else "",

                    # Core backend service properties
                    "protocol": service.protocol if hasattr(service, 'protocol') and service.protocol else None,
                    "port": service.port if hasattr(service, 'port') else None,
                    "port_name": service.port_name if hasattr(service, 'port_name') and service.port_name else None,
                    "timeout_sec": service.timeout_sec if hasattr(service, 'timeout_sec') else None,
                    "enable_cdn": service.enable_c_d_n if hasattr(service, 'enable_c_d_n') else False,
                    "session_affinity": service.session_affinity if hasattr(service, 'session_affinity') and service.session_affinity else None,
                    "affinity_cookie_ttl_sec": service.affinity_cookie_ttl_sec if hasattr(service, 'affinity_cookie_ttl_sec') else None,
                    "load_balancing_scheme": service.load_balancing_scheme if hasattr(service, 'load_balancing_scheme') and service.load_balancing_scheme else None,

                    # Health checks
                    "health_checks": [hc.split('/')[-1] for hc in service.health_checks] if hasattr(service, 'health_checks') and service.health_checks else [],

                    # Backends
                    "backends": [],

                    # Connection draining
                    "connection_draining": None,

                    # Network (regional backend services can specify network)
                    "network": service.network.split('/')[-1] if hasattr(service, 'network') and service.network else None,

                    # Regional backend services typically don't have CDN, IAP, or some advanced features
                    "cdn_policy": None,
                    "iap": None,
                    "security_policy": service.security_policy.split('/')[-1] if hasattr(service, 'security_policy') and service.security_policy else None,
                    "edge_security_policy": None,  # Not available for regional
                    "circuit_breakers": None,
                    "outlier_detection": None,
                    "custom_request_headers": list(service.custom_request_headers) if hasattr(service, 'custom_request_headers') and service.custom_request_headers else [],
                    "custom_response_headers": list(service.custom_response_headers) if hasattr(service, 'custom_response_headers') and service.custom_response_headers else [],
                    "log_config": None,
                    "locality_lb_policy": service.locality_lb_policy if hasattr(service, 'locality_lb_policy') and service.locality_lb_policy else None,
                    "consistent_hash": None,
                    "compression_mode": service.compression_mode if hasattr(service, 'compression_mode') and service.compression_mode else None,

                    # Labels and metadata
                    "labels": dict(service.labels) if hasattr(service, 'labels') and service.labels else {},
                    "fingerprint": service.fingerprint if hasattr(service, 'fingerprint') else None,
                    "creation_timestamp": service.creation_timestamp if hasattr(service, 'creation_timestamp') else None,

                    # For resource naming and identification
                    "name_sanitized": service.name.replace('-', '_').lower(),
                    "service_type": "regional"
                }

                # Process backends (same logic as global)
                if hasattr(service, 'backends') and service.backends:
                    for backend in service.backends:
                        backend_data = {
                            "group": backend.group.split('/')[-1] if hasattr(backend, 'group') and backend.group else None,
                            "balancing_mode": backend.balancing_mode if hasattr(backend, 'balancing_mode') and backend.balancing_mode else None,
                            "max_rate": backend.max_rate if hasattr(backend, 'max_rate') else None,
                            "max_rate_per_instance": backend.max_rate_per_instance if hasattr(backend, 'max_rate_per_instance') else None,
                            "max_rate_per_endpoint": backend.max_rate_per_endpoint if hasattr(backend, 'max_rate_per_endpoint') else None,
                            "max_connections": backend.max_connections if hasattr(backend, 'max_connections') else None,
                            "max_connections_per_instance": backend.max_connections_per_instance if hasattr(backend, 'max_connections_per_instance') else None,
                            "max_connections_per_endpoint": backend.max_connections_per_endpoint if hasattr(backend, 'max_connections_per_endpoint') else None,
                            "max_utilization": backend.max_utilization if hasattr(backend, 'max_utilization') else None,
                            "capacity_scaler": backend.capacity_scaler if hasattr(backend, 'capacity_scaler') else None,
                            "description": backend.description if hasattr(backend, 'description') and backend.description else ""
                        }
                        service_data["backends"].append(backend_data)

                # Process connection draining
                if hasattr(service, 'connection_draining') and service.connection_draining:
                    cd = service.connection_draining
                    service_data["connection_draining"] = {
                        "draining_timeout_sec": cd.draining_timeout_sec if hasattr(cd, 'draining_timeout_sec') else None
                    }

                # Process log config
                if hasattr(service, 'log_config') and service.log_config:
                    lc = service.log_config
                    service_data["log_config"] = {
                        "enable": lc.enable if hasattr(lc, 'enable') else False,
                        "sample_rate": lc.sample_rate if hasattr(lc, 'sample_rate') else None
                    }

                backend_services.append(service_data)

        # Also scan regional backend services across all regions when not specifying a specific region
        if not region:
            # Scan all regions for regional backend services
            regions_client = compute_v1.RegionsClient()
            regions_request = compute_v1.ListRegionsRequest(project=project_id)
            regions_list = regions_client.list(request=regions_request)

            regional_client = compute_v1.RegionBackendServicesClient()

            for region_obj in regions_list:
                region_name = region_obj.name
                try:
                    regional_request = compute_v1.ListRegionBackendServicesRequest(
                        project=project_id,
                        region=region_name
                    )
                    regional_service_list = regional_client.list(request=regional_request)

                    for service in regional_service_list:
                        service_data = {
                            "name": service.name,
                            "id": f"{project_id}/{region_name}/{service.name}",
                            "project": project_id,
                            "region": region_name,
                            "description": service.description if hasattr(service, 'description') and service.description else "",

                            # Core backend service properties
                            "protocol": service.protocol if hasattr(service, 'protocol') and service.protocol else None,
                            "port": service.port if hasattr(service, 'port') else None,
                            "port_name": service.port_name if hasattr(service, 'port_name') and service.port_name else None,
                            "timeout_sec": service.timeout_sec if hasattr(service, 'timeout_sec') else None,
                            "enable_cdn": service.enable_c_d_n if hasattr(service, 'enable_c_d_n') else False,
                            "session_affinity": service.session_affinity if hasattr(service, 'session_affinity') and service.session_affinity else None,
                            "affinity_cookie_ttl_sec": service.affinity_cookie_ttl_sec if hasattr(service, 'affinity_cookie_ttl_sec') else None,
                            "load_balancing_scheme": service.load_balancing_scheme if hasattr(service, 'load_balancing_scheme') and service.load_balancing_scheme else None,

                            # Health checks
                            "health_checks": [hc.split('/')[-1] for hc in service.health_checks] if hasattr(service, 'health_checks') and service.health_checks else [],

                            # Backends
                            "backends": [],

                            # Connection draining
                            "connection_draining": None,

                            # Network (regional backend services can specify network)
                            "network": service.network.split('/')[-1] if hasattr(service, 'network') and service.network else None,

                            # Regional backend services typically don't have CDN, IAP, or some advanced features
                            "cdn_policy": None,
                            "iap": None,
                            "security_policy": service.security_policy.split('/')[-1] if hasattr(service, 'security_policy') and service.security_policy else None,
                            "edge_security_policy": None,  # Not available for regional
                            "circuit_breakers": None,
                            "outlier_detection": None,
                            "custom_request_headers": list(service.custom_request_headers) if hasattr(service, 'custom_request_headers') and service.custom_request_headers else [],
                            "custom_response_headers": list(service.custom_response_headers) if hasattr(service, 'custom_response_headers') and service.custom_response_headers else [],
                            "log_config": None,
                            "locality_lb_policy": service.locality_lb_policy if hasattr(service, 'locality_lb_policy') and service.locality_lb_policy else None,
                            "consistent_hash": None,
                            "compression_mode": service.compression_mode if hasattr(service, 'compression_mode') and service.compression_mode else None,

                            # Labels and metadata
                            "labels": dict(service.labels) if hasattr(service, 'labels') and service.labels else {},
                            "fingerprint": service.fingerprint if hasattr(service, 'fingerprint') else None,
                            "creation_timestamp": service.creation_timestamp if hasattr(service, 'creation_timestamp') else None,

                            # For resource naming and identification
                            "name_sanitized": service.name.replace('-', '_').lower(),
                            "service_type": "regional"
                        }

                        # Process backends (same logic as specific region)
                        if hasattr(service, 'backends') and service.backends:
                            for backend in service.backends:
                                backend_data = {
                                    "group": backend.group.split('/')[-1] if hasattr(backend, 'group') and backend.group else None,
                                    "balancing_mode": backend.balancing_mode if hasattr(backend, 'balancing_mode') and backend.balancing_mode else None,
                                    "max_rate": backend.max_rate if hasattr(backend, 'max_rate') else None,
                                    "max_rate_per_instance": backend.max_rate_per_instance if hasattr(backend, 'max_rate_per_instance') else None,
                                    "max_rate_per_endpoint": backend.max_rate_per_endpoint if hasattr(backend, 'max_rate_per_endpoint') else None,
                                    "max_connections": backend.max_connections if hasattr(backend, 'max_connections') else None,
                                    "max_connections_per_instance": backend.max_connections_per_instance if hasattr(backend, 'max_connections_per_instance') else None,
                                    "max_connections_per_endpoint": backend.max_connections_per_endpoint if hasattr(backend, 'max_connections_per_endpoint') else None,
                                    "max_utilization": backend.max_utilization if hasattr(backend, 'max_utilization') else None,
                                    "capacity_scaler": backend.capacity_scaler if hasattr(backend, 'capacity_scaler') else None,
                                    "description": backend.description if hasattr(backend, 'description') and backend.description else ""
                                }
                                service_data["backends"].append(backend_data)

                        # Process connection draining
                        if hasattr(service, 'connection_draining') and service.connection_draining:
                            cd = service.connection_draining
                            service_data["connection_draining"] = {
                                "draining_timeout_sec": cd.draining_timeout_sec if hasattr(cd, 'draining_timeout_sec') else None
                            }

                        # Process log config
                        if hasattr(service, 'log_config') and service.log_config:
                            lc = service.log_config
                            service_data["log_config"] = {
                                "enable": lc.enable if hasattr(lc, 'enable') else False,
                                "sample_rate": lc.sample_rate if hasattr(lc, 'sample_rate') else None
                            }

                        backend_services.append(service_data)

                except exceptions.GoogleAPIError as e:
                    # Skip regions that have errors (e.g., disabled APIs)
                    if "not found" not in str(e).lower():
                        typer.echo(f"Warning: Could not scan region {region_name}: {str(e)}", err=True)
                    continue

    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching backend services: {str(e)}", err=True)
        raise typer.Exit(code=1)

    return backend_services

@app.command("scan")
def scan_backend_services(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    region: Optional[str] = typer.Option(None, "--region", "-r"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP backend services and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning GCP backend services with dependencies...")
        recursive_scan(
            "gcp_backend_service",
            output_dir=output_dir,
            project_id=project_id,
            region=region
        )
    else:
        typer.echo(f"Scanning for GCP backend services in project '{project_id}'...")
        if region:
            typer.echo(f"Region: {region}")
        else:
            typer.echo("Scope: Global")
        
        backend_service_data = get_backend_service_data(project_id, region)

        if not backend_service_data:
            typer.echo("No backend services found.")
            return

        # Separate global and regional backend services for different resource types
        global_services = [svc for svc in backend_service_data if svc["service_type"] == "global"]
        regional_services = [svc for svc in backend_service_data if svc["service_type"] == "regional"]

        # Generate Terraform files for global backend services
        if global_services:
            output_file = output_dir / "gcp_backend_service.tf"
            generate_tf(global_services, "gcp_backend_service", output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(global_services)} global backend services -> {output_file}")

            # Generate import file for global backend services
            generate_imports_file(
                "gcp_backend_service",
                global_services,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )

        # Generate Terraform files for regional backend services
        if regional_services:
            output_file = output_dir / "gcp_region_backend_service.tf"
            generate_tf(regional_services, "gcp_region_backend_service", output_file, provider="gcp")
            typer.echo(f"Generated Terraform for {len(regional_services)} regional backend services -> {output_file}")

            # Generate import file for regional backend services
            generate_imports_file(
                "gcp_region_backend_service",
                regional_services,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )

@app.command("list")
def list_backend_services(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    service_type: Optional[str] = typer.Option(None, "--type", "-t", help="Filter by service type: global or regional")
):
    """List all GCP backend service resources previously generated."""
    if service_type == "global":
        typer.echo("Global backend services:")
        ImportManager(output_dir, "gcp_backend_service").list_all()
    elif service_type == "regional":
        typer.echo("Regional backend services:")
        ImportManager(output_dir, "gcp_region_backend_service").list_all()
    else:
        typer.echo("Global backend services:")
        ImportManager(output_dir, "gcp_backend_service").list_all()
        typer.echo("\nRegional backend services:")
        ImportManager(output_dir, "gcp_region_backend_service").list_all()

@app.command("import")
def import_backend_service(
    backend_service_id: str = typer.Argument(..., help="GCP backend service ID (project/name for global, project/region/name for regional)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    service_type: Optional[str] = typer.Option(None, "--type", "-t", help="Service type: global or regional (auto-detected if not specified)")
):
    """Run terraform import for a specific GCP backend service."""
    # Auto-detect service type based on ID format if not specified
    if service_type is None:
        parts = backend_service_id.split('/')
        if len(parts) == 2:
            service_type = "global"
        elif len(parts) == 3:
            service_type = "regional"
        else:
            typer.echo("Error: Invalid backend service ID format. Expected project/name for global or project/region/name for regional.", err=True)
            raise typer.Exit(code=1)

    if service_type == "global":
        ImportManager(output_dir, "gcp_backend_service").find_and_import(backend_service_id)
    elif service_type == "regional":
        ImportManager(output_dir, "gcp_region_backend_service").find_and_import(backend_service_id)
    else:
        typer.echo("Error: Service type must be 'global' or 'regional'", err=True)
        raise typer.Exit(code=1)

# Scan function for cross-scan registry
def scan_gcp_backend_services(
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
    
    typer.echo(f"[Cross-scan] Scanning GCP backend services in project {project_id}")
    
    backend_service_data = get_backend_service_data(project_id, region)

    if backend_service_data:
        # Separate global and regional backend services for different resource types
        global_services = [svc for svc in backend_service_data if svc["service_type"] == "global"]
        regional_services = [svc for svc in backend_service_data if svc["service_type"] == "regional"]

        # Generate files for global backend services
        if global_services:
            output_file = output_dir / "gcp_backend_service.tf"
            generate_tf(global_services, "gcp_backend_service", output_file, provider="gcp")
            generate_imports_file(
                "gcp_backend_service",
                global_services,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(global_services)} global GCP backend services")

        # Generate files for regional backend services
        if regional_services:
            output_file = output_dir / "gcp_region_backend_service.tf"
            generate_tf(regional_services, "gcp_region_backend_service", output_file, provider="gcp")
            generate_imports_file(
                "gcp_region_backend_service",
                regional_services,
                remote_resource_id_key="id",
                output_dir=output_dir, provider="gcp"
            )
            typer.echo(f"[Cross-scan] Generated Terraform for {len(regional_services)} regional GCP backend services")
