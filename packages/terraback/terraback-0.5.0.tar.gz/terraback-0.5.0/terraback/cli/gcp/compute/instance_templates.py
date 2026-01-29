# terraback/cli/gcp/compute/instance_templates.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="instance-template", help="Scan and import GCP Compute Engine instance templates.")

def get_instance_template_data(project_id: str) -> List[Dict[str, Any]]:
    """Fetch instance template data from GCP."""
    client = compute_v1.InstanceTemplatesClient()
    templates = []
    
    try:
        request = compute_v1.ListInstanceTemplatesRequest(project=project_id)
        template_list = client.list(request=request)
        
        for template in template_list:
            template_data = {
                "name": template.name,
                "id": f"{project_id}/{template.name}",
                "project": project_id,
                "description": template.description if hasattr(template, 'description') else "",
                
                # Instance properties
                "machine_type": template.properties.machine_type if template.properties and hasattr(template.properties, 'machine_type') else None,
                "can_ip_forward": template.properties.can_ip_forward if template.properties and hasattr(template.properties, 'can_ip_forward') else False,
                "tags": list(template.properties.tags.items) if template.properties and template.properties.tags and template.properties.tags.items else [],
                "labels": dict(template.properties.labels) if template.properties and hasattr(template.properties, 'labels') and template.properties.labels else {},
                "metadata": (
                    dict(template.properties.metadata.items()) 
                    if template.properties and hasattr(template.properties, 'metadata') and template.properties.metadata 
                    else {}
                ),
                "metadata_startup_script": (
                    template.properties.metadata.get('startup-script')
                    if template.properties and hasattr(template.properties, 'metadata') and template.properties.metadata and 'startup-script' in template.properties.metadata
                    else None
                ),
                
                # Network interfaces
                "network_interfaces": [],
                
                # Disks
                "boot_disk": None,
                "attached_disks": [],
                
                # Service accounts
                "service_accounts": [],
                
                # Scheduling
                "scheduling": None,
                
                # Advanced features
                "guest_accelerators": [],
                "min_cpu_platform": template.properties.min_cpu_platform if template.properties and hasattr(template.properties, 'min_cpu_platform') else None,
                "shielded_instance_config": None,
                "confidential_instance_config": None,
                
                # For resource naming
                "name_sanitized": template.name.replace('-', '_').lower(),
                "creation_timestamp": template.creation_timestamp if hasattr(template, 'creation_timestamp') else None,
            }
            
            if not template.properties:
                templates.append(template_data)
                continue
                
            # Process network interfaces
            if hasattr(template.properties, 'network_interfaces') and template.properties.network_interfaces:
                for nic in template.properties.network_interfaces:
                    nic_data = {
                        "network": nic.network.split('/')[-1] if nic.network else None,
                        "subnetwork": nic.subnetwork.split('/')[-1] if nic.subnetwork else None,
                        "access_configs": []
                    }
                    
                    if hasattr(nic, 'access_configs') and nic.access_configs:
                        for ac in nic.access_configs:
                            nic_data["access_configs"].append({
                                "name": ac.name if hasattr(ac, 'name') else "External NAT",
                                "nat_ip": ac.nat_i_p if hasattr(ac, 'nat_i_p') else None,
                                "network_tier": ac.network_tier if hasattr(ac, 'network_tier') else "PREMIUM"
                            })
                    
                    template_data["network_interfaces"].append(nic_data)
            
            # Process disks
            if hasattr(template.properties, 'disks') and template.properties.disks:
                for disk in template.properties.disks:
                    disk_data = {
                        "source": disk.source.split('/')[-1] if disk.source else None,
                        "device_name": disk.device_name if hasattr(disk, 'device_name') else None,
                        "mode": disk.mode if hasattr(disk, 'mode') else "READ_WRITE",
                        "boot": disk.boot if hasattr(disk, 'boot') else False,
                        "auto_delete": disk.auto_delete if hasattr(disk, 'auto_delete') else True,
                        "type": disk.type if hasattr(disk, 'type') else "PERSISTENT",
                        "interface": disk.interface if hasattr(disk, 'interface') else "SCSI"
                    }
                    
                    # Handle initialize params for new disks
                    if hasattr(disk, 'initialize_params') and disk.initialize_params:
                        init_params = disk.initialize_params
                        disk_data["initialize_params"] = {
                            "disk_size_gb": init_params.disk_size_gb if hasattr(init_params, 'disk_size_gb') else None,
                            "disk_type": init_params.disk_type.split('/')[-1] if hasattr(init_params, 'disk_type') and init_params.disk_type else "pd-standard",
                            "source_image": init_params.source_image.split('/')[-1] if hasattr(init_params, 'source_image') and init_params.source_image else None,
                            "source_snapshot": init_params.source_snapshot.split('/')[-1] if hasattr(init_params, 'source_snapshot') and init_params.source_snapshot else None,
                            "labels": dict(init_params.labels) if hasattr(init_params, 'labels') and init_params.labels else {}
                        }
                    
                    if disk.boot:
                        template_data["boot_disk"] = disk_data
                    else:
                        template_data["attached_disks"].append(disk_data)
            
            # Process metadata
            if hasattr(template.properties, 'metadata') and template.properties.metadata:
                if hasattr(template.properties.metadata, 'items') and template.properties.metadata.items:
                    for item in template.properties.metadata.items:
                        if item.key == 'startup-script':
                            template_data["metadata_startup_script"] = item.value
                        else:
                            template_data["metadata"][item.key] = item.value
            
            # Process service accounts
            if hasattr(template.properties, 'service_accounts') and template.properties.service_accounts:
                for sa in template.properties.service_accounts:
                    template_data["service_accounts"].append({
                        "email": sa.email,
                        "scopes": list(sa.scopes) if sa.scopes else []
                    })
            
            # Process scheduling
            if hasattr(template.properties, 'scheduling') and template.properties.scheduling:
                template_data["scheduling"] = {
                    "preemptible": template.properties.scheduling.preemptible if hasattr(template.properties.scheduling, 'preemptible') else None,
                    "on_host_maintenance": template.properties.scheduling.on_host_maintenance if hasattr(template.properties.scheduling, 'on_host_maintenance') and template.properties.scheduling.on_host_maintenance else None,
                    "automatic_restart": template.properties.scheduling.automatic_restart if hasattr(template.properties.scheduling, 'automatic_restart') else None,
                    "provisioning_model": template.properties.scheduling.provisioning_model if hasattr(template.properties.scheduling, 'provisioning_model') and template.properties.scheduling.provisioning_model else None
                }
            
            # Process guest accelerators (GPUs)
            if hasattr(template.properties, 'guest_accelerators') and template.properties.guest_accelerators:
                for accel in template.properties.guest_accelerators:
                    template_data["guest_accelerators"].append({
                        "type": accel.accelerator_type.split('/')[-1] if accel.accelerator_type else None,
                        "count": accel.accelerator_count if hasattr(accel, 'accelerator_count') else 1
                    })
            
            # Process shielded instance config
            if hasattr(template.properties, 'shielded_instance_config') and template.properties.shielded_instance_config:
                sic = template.properties.shielded_instance_config
                template_data["shielded_instance_config"] = {
                    "enable_secure_boot": sic.enable_secure_boot if hasattr(sic, 'enable_secure_boot') else False,
                    "enable_vtpm": sic.enable_vtpm if hasattr(sic, 'enable_vtpm') else True,
                    "enable_integrity_monitoring": sic.enable_integrity_monitoring if hasattr(sic, 'enable_integrity_monitoring') else True
                }
            
            # Process confidential instance config
            if hasattr(template.properties, 'confidential_instance_config') and template.properties.confidential_instance_config:
                cic = template.properties.confidential_instance_config
                template_data["confidential_instance_config"] = {
                    "enable_confidential_compute": cic.enable_confidential_compute if hasattr(cic, 'enable_confidential_compute') else False
                }
            
            templates.append(template_data)
            
    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching instance templates: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return templates

@app.command("scan")
def scan_instance_templates(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP Compute Engine instance templates and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning GCP instance templates with dependencies...")
        recursive_scan(
            "gcp_instance_template",
            output_dir=output_dir,
            project_id=project_id
        )
    else:
        typer.echo(f"Scanning for GCP instance templates in project '{project_id}'...")
        
        template_data = get_instance_template_data(project_id)
        
        if not template_data:
            typer.echo("No instance templates found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_instance_template.tf"
        generate_tf(template_data, "gcp_instance_template", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(template_data)} instance templates -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_instance_template",
            template_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )

@app.command("list")
def list_instance_templates(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """List all GCP instance template resources previously generated."""
    ImportManager(output_dir, "gcp_instance_template").list_all()

@app.command("import")
def import_instance_template(
    template_id: str = typer.Argument(..., help="GCP instance template ID (project/name)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP instance template."""
    ImportManager(output_dir, "gcp_instance_template").find_and_import(template_id)

# Scan function for cross-scan registry
def scan_gcp_instance_templates(
    output_dir: Path,
    project_id: str = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP instance templates in project {project_id}")
    
    template_data = get_instance_template_data(project_id)
    
    if template_data:
        output_file = output_dir / "gcp_instance_template.tf"
        generate_tf(template_data, "gcp_instance_template", output_file, provider="gcp")
        generate_imports_file(
            "gcp_instance_template",
            template_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(template_data)} GCP instance templates")