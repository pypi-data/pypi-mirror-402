import typer
from pathlib import Path
from typing import List, Dict, Any, Optional
from terraback.cli.gcp.session import get_gcp_credentials
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from google.api_core.exceptions import GoogleAPIError

app = typer.Typer()


def _process_registry_data(registry: Any, project_id: str) -> Dict[str, Any]:
    """Process GCP container registry data for Terraform generation."""
    # Extract location and name from the full resource name
    parts = registry.name.split('/')
    location = parts[3]
    registry_name = parts[-1]
    
    registry_data = {
        'repository_id': registry_name,
        'project': project_id,
        'location': location,
        'description': registry.description if hasattr(registry, 'description') else '',
        'format': registry.format.name if hasattr(registry, 'format') else 'DOCKER',
        'labels': dict(registry.labels) if registry.labels else {},
        'create_time': registry.create_time.isoformat() if hasattr(registry, 'create_time') else None,
        'update_time': registry.update_time.isoformat() if hasattr(registry, 'update_time') else None,
    }
    
    # Mode configuration
    if hasattr(registry, 'mode') and registry.mode:
        registry_data['mode'] = registry.mode.name
    
    # Maven configuration
    if hasattr(registry, 'maven_config') and registry.maven_config:
        maven = registry.maven_config
        registry_data['maven_config'] = {
            'allow_snapshot_overwrites': maven.allow_snapshot_overwrites if hasattr(maven, 'allow_snapshot_overwrites') else False,
            'version_policy': maven.version_policy.name if hasattr(maven, 'version_policy') else 'VERSION_POLICY_UNSPECIFIED',
        }
    
    # Docker configuration
    if hasattr(registry, 'docker_config') and registry.docker_config:
        docker = registry.docker_config
        registry_data['docker_config'] = {
            'immutable_tags': docker.immutable_tags if hasattr(docker, 'immutable_tags') else False,
        }
    
    # Cleanup policies
    if hasattr(registry, 'cleanup_policies') and registry.cleanup_policies:
        registry_data['cleanup_policies'] = []
        for policy_name, policy in registry.cleanup_policies.items():
            policy_data = {
                'id': policy_name,
                'action': policy.action.name if hasattr(policy, 'action') else 'DELETE',
            }
            
            # Condition
            if hasattr(policy, 'condition') and policy.condition:
                condition = policy.condition
                policy_data['condition'] = {}
                
                if hasattr(condition, 'tag_state'):
                    policy_data['condition']['tag_state'] = condition.tag_state.name
                if hasattr(condition, 'tag_prefixes'):
                    policy_data['condition']['tag_prefixes'] = list(condition.tag_prefixes)
                if hasattr(condition, 'version_name_prefixes'):
                    policy_data['condition']['version_name_prefixes'] = list(condition.version_name_prefixes)
                if hasattr(condition, 'package_name_prefixes'):
                    policy_data['condition']['package_name_prefixes'] = list(condition.package_name_prefixes)
                if hasattr(condition, 'older_than'):
                    policy_data['condition']['older_than'] = f"{condition.older_than.seconds}s"
                if hasattr(condition, 'newer_than'):
                    policy_data['condition']['newer_than'] = f"{condition.newer_than.seconds}s"
            
            registry_data['cleanup_policies'].append(policy_data)
    
    return registry_data


def get_registry_data(project_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch Container Registry data from GCP.
    
    Args:
        project_id: GCP project ID. If not provided, uses default from credentials.
    
    Returns:
        List of registry data dictionaries
    """
    from terraback.cli.gcp.session import get_default_project_id
    credentials = get_gcp_credentials()
    project_id = project_id or get_default_project_id()
    
    # Container Registry is being deprecated in favor of Artifact Registry
    # For now, return empty as GCR doesn't have a direct API client
    print("Note: Container Registry is deprecated. Consider using Artifact Registry instead.")
    return []


def scan_container_registries_legacy(output_dir: Path, project_id: Optional[str] = None, with_deps: bool = False):
    """
    Scan GCP container registries and generate Terraform configuration.
    
    Args:
        output_dir: Directory to save Terraform files
        project_id: GCP project ID
        with_deps: Whether to scan dependencies
    """
    registries = get_registry_data(project_id)
    
    if not registries:
        print("No container registries found.")
        return
        
    output_file = output_dir / "gcp_container_registries.tf"
    generate_tf(registries, "gcp_container_registries", output_file)
    print(f"Generated Terraform for {len(registries)} GCP Container Registries -> {output_file}")
    
    # Generate import file
    generate_imports_file(
        "gcp_container_registries", 
        registries, 
        remote_resource_id_key="repository_id",
        output_dir=output_dir, provider="gcp"
    )

# Scan function for cross-scan registry
def scan_container_registries(
    output_dir: Path,
    project_id: str = None,
    region: str = None,
    zone: str = None,
    with_deps: bool = False,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    from terraback.cli.gcp.session import get_default_project_id
    
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning Container Registry repositories in project {project_id}")
    
    registries = get_registry_data(project_id)
    
    if registries:
        output_file = output_dir / "gcp_container_registries.tf"
        generate_tf(registries, "gcp_container_registries", output_file, provider="gcp")
        generate_imports_file(
            "gcp_container_registries",
            registries,
            remote_resource_id_key="repository_id",
            output_dir=output_dir,
            provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(registries)} Container Registry repositories")


@app.command("scan")
def scan_command(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    with_deps: bool = typer.Option(False, "--with-deps"),
):
    """Scan GCP container registries."""
    scan_container_registries_legacy(output_dir, project_id, with_deps)


@app.command("list")
def list_command(output_dir: Path = typer.Option("generated", "-o", "--output-dir")):
    """List all imported container registries."""
    ImportManager(output_dir, "gcp_container_registries").list_all()


@app.command("import")
def import_command(
    registry_id: str = typer.Argument(..., help="Repository ID to import"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
):
    """Import a specific container registry."""
    ImportManager(output_dir, "gcp_container_registries").find_and_import(registry_id)