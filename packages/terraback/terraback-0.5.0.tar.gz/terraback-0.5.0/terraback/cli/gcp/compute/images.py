# terraback/cli/gcp/compute/images.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="image", help="Scan and import GCP Compute Engine images.")

def get_image_data(project_id: str, family_filter: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch image data from GCP."""
    images = []

    try:
        client = compute_v1.ImagesClient()

        # Scan project-specific images (custom images)
        typer.echo(f"Scanning custom images in project {project_id}...")
        try:
            image_list = client.list(project=project_id)
            for image in image_list:
                # Apply family filter if specified
                if family_filter and hasattr(image, 'family') and image.family:
                    if family_filter not in image.family:
                        continue

                image_data = {
                    'id': f"{project_id}/{image.name}",
                    'name': image.name,
                    'name_sanitized': image.name.replace('-', '_').replace('.', '_'),
                    'project': project_id,
                    'terraform_type': 'google_compute_image',

                    # Core properties
                    'description': getattr(image, 'description', ''),
                    'family': getattr(image, 'family', ''),
                    'source_type': getattr(image, 'source_type', ''),
                    'status': getattr(image, 'status', ''),

                    # Source information
                    'source_disk': getattr(image, 'source_disk', ''),
                    'source_image': getattr(image, 'source_image', ''),
                    'source_snapshot': getattr(image, 'source_snapshot', ''),

                    # Size and storage
                    'disk_size_gb': getattr(image, 'disk_size_gb', 0),
                    'archive_size_bytes': getattr(image, 'archive_size_bytes', 0),
                    'storage_locations': getattr(image, 'storage_locations', []),

                    # Guest OS features
                    'guest_os_features': [
                        feature.type_ for feature in getattr(image, 'guest_os_features', [])
                        if hasattr(feature, 'type_')
                    ],

                    # Licensing and usage
                    'licenses': getattr(image, 'licenses', []),
                    'license_codes': getattr(image, 'license_codes', []),

                    # Image encryption
                    'image_encryption_key': {
                        'raw_key': getattr(image.image_encryption_key, 'raw_key', '')
                            if hasattr(image, 'image_encryption_key') and image.image_encryption_key else '',
                        'sha256': getattr(image.image_encryption_key, 'sha256', '')
                            if hasattr(image, 'image_encryption_key') and image.image_encryption_key else '',
                        'kms_key_name': getattr(image.image_encryption_key, 'kms_key_name', '')
                            if hasattr(image, 'image_encryption_key') and image.image_encryption_key else ''
                    } if hasattr(image, 'image_encryption_key') and image.image_encryption_key else None,

                    # Source disk encryption
                    'source_disk_encryption_key': {
                        'raw_key': getattr(image.source_disk_encryption_key, 'raw_key', '')
                            if hasattr(image, 'source_disk_encryption_key') and image.source_disk_encryption_key else '',
                        'sha256': getattr(image.source_disk_encryption_key, 'sha256', '')
                            if hasattr(image, 'source_disk_encryption_key') and image.source_disk_encryption_key else '',
                        'kms_key_name': getattr(image.source_disk_encryption_key, 'kms_key_name', '')
                            if hasattr(image, 'source_disk_encryption_key') and image.source_disk_encryption_key else ''
                    } if hasattr(image, 'source_disk_encryption_key') and image.source_disk_encryption_key else None,

                    # Labels and metadata
                    'labels': dict(getattr(image, 'labels', {})),

                    # Lifecycle information
                    'creation_timestamp': getattr(image, 'creation_timestamp', ''),
                    'deprecated': {
                        'state': getattr(image.deprecated, 'state', '')
                            if hasattr(image, 'deprecated') and image.deprecated else '',
                        'replacement': getattr(image.deprecated, 'replacement', '')
                            if hasattr(image, 'deprecated') and image.deprecated else '',
                        'deprecated': getattr(image.deprecated, 'deprecated', '')
                            if hasattr(image, 'deprecated') and image.deprecated else '',
                        'obsolete': getattr(image.deprecated, 'obsolete', '')
                            if hasattr(image, 'deprecated') and image.deprecated else '',
                        'deleted': getattr(image.deprecated, 'deleted', '')
                            if hasattr(image, 'deprecated') and image.deprecated else ''
                    } if hasattr(image, 'deprecated') and image.deprecated else None,

                    # Raw data for templates
                    'raw': image
                }
                images.append(image_data)

        except exceptions.GoogleAPIError as e:
            if "not found" not in str(e).lower() and "disabled" not in str(e).lower():
                typer.echo(f"Warning: Could not scan custom images: {str(e)}", err=True)

    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching images: {str(e)}", err=True)
        raise typer.Exit(code=1)

    return images

@app.command("scan")
def scan_images(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    family: Optional[str] = typer.Option(None, "--family", "-f", help="Filter images by family name"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP Compute Engine images and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan

    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)

    if with_deps:
        typer.echo("Scanning GCP images with dependencies...")
        recursive_scan(
            "gcp_image",
            output_dir=output_dir,
            project_id=project_id,
            family_filter=family
        )
    else:
        typer.echo(f"Scanning for custom images in project '{project_id}'...")
        if family:
            typer.echo(f"Filtering by family: {family}")

        image_data = get_image_data(project_id, family)

        if not image_data:
            typer.echo("No custom images found.")
            return

        # Generate Terraform files
        output_file = output_dir / "gcp_image.tf"
        generate_tf(image_data, "gcp_image", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(image_data)} images -> {output_file}")

        # Generate import file
        generate_imports_file(
            "gcp_image",
            image_data,
            remote_resource_id_key="id",
            output_dir=output_dir,
            provider="gcp"
        )

@app.command("list")
def list_images(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """List all GCP image resources previously generated."""
    ImportManager(output_dir, "gcp_image").list_all()

@app.command("import")
def import_image(
    image_id: str = typer.Argument(..., help="GCP image ID to import (project/image_name)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP image."""
    ImportManager(output_dir, "gcp_image").find_and_import(image_id)

# Scan function for cross-scan registry
def scan_gcp_images(
    output_dir: Path,
    project_id: Optional[str] = None,
    family_filter: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""

    if not project_id:
        project_id = get_default_project_id()
    if not project_id:
        typer.echo("Error: No GCP project found", err=True)
        raise typer.Exit(code=1)

    typer.echo(f"[Cross-scan] Scanning GCP images in project {project_id}")

    image_data = get_image_data(project_id, family_filter)

    if image_data:
        output_file = output_dir / "gcp_image.tf"
        generate_tf(image_data, "gcp_image", output_file, provider="gcp")
        generate_imports_file(
            "gcp_image",
            image_data,
            remote_resource_id_key="id",
            output_dir=output_dir,
            provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(image_data)} GCP images")