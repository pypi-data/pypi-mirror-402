# terraback/cli/gcp/compute/instances.py
import typer
from pathlib import Path
from typing import Optional, List, Dict, Any
from google.cloud import compute_v1
from google.api_core import exceptions

from terraback.cli.gcp.session import get_default_project_id
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

app = typer.Typer(name="instance", help="Scan and import GCP Compute Engine instances.")

def get_instance_data(project_id: str, zone: str = None) -> List[Dict[str, Any]]:
    """Fetch instance data from GCP."""
    client = compute_v1.InstancesClient()
    instances = []
    
    try:
        if zone:
            # List instances in specific zone
            request = compute_v1.ListInstancesRequest(
                project=project_id,
                zone=zone
            )
            instance_list = client.list(request=request)
        else:
            # List all instances across all zones
            request = compute_v1.AggregatedListInstancesRequest(
                project=project_id
            )
            aggregated_list = client.aggregated_list(request=request)
            instance_list = []
            for zone_name, scoped_list in aggregated_list:
                if scoped_list.instances:
                    for instance in scoped_list.instances:
                        # Extract zone from the scoped list key
                        instance_zone = zone_name.split('/')[-1]
                        instance_list.append((instance, instance_zone))
        
        for item in instance_list:
            if zone:
                instance = item
                instance_zone = zone
            else:
                instance, instance_zone = item
            
            instance_data = {
                "name": instance.name,
                "id": f"{project_id}/{instance_zone}/{instance.name}",
                "project": project_id,
                "zone": instance_zone,
                "machine_type": instance.machine_type.split('/')[-1] if instance.machine_type else None,
                "tags": list(instance.tags.items) if instance.tags and hasattr(instance.tags, 'items') and instance.tags.items else [],
                
                # Network interfaces
                "network_interfaces": [],
                
                # Disks
                "boot_disk": None,
                "attached_disks": [],
                
                # Metadata - read actual instance metadata
                "metadata": dict(instance.metadata.items()) if hasattr(instance, 'metadata') and instance.metadata else {},
                "metadata_startup_script": (
                    instance.metadata.get('startup-script')
                    if hasattr(instance, 'metadata') and instance.metadata and 'startup-script' in instance.metadata
                    else None
                ),
                "labels": dict(instance.labels) if instance.labels else {},
                
                # Scheduling
                "can_ip_forward": instance.can_ip_forward if hasattr(instance, 'can_ip_forward') else False,
                "deletion_protection": instance.deletion_protection if hasattr(instance, 'deletion_protection') else False,
                "scheduling": None,
                
                # Advanced features
                "guest_accelerators": [],
                "min_cpu_platform": instance.min_cpu_platform if hasattr(instance, 'min_cpu_platform') else None,
                "shielded_instance_config": None,
                "confidential_instance_config": None,
                "enable_display": instance.enable_display if hasattr(instance, 'enable_display') else None,
                
                # Service account
                "service_accounts": [],
                
                # State
                "status": instance.status,
                
                # For resource naming
                "name_sanitized": instance.name.replace('-', '_').lower()
            }
            
            # Process network interfaces
            if instance.network_interfaces:
                for nic in instance.network_interfaces:
                    nic_data = {
                        "network": nic.network.split('/')[-1] if nic.network else None,
                        "subnetwork": nic.subnetwork.split('/')[-1] if nic.subnetwork else None,
                        "network_ip": nic.network_i_p if hasattr(nic, 'network_i_p') else None,
                        "access_configs": []
                    }
                    
                    if nic.access_configs:
                        for ac in nic.access_configs:
                            nic_data["access_configs"].append({
                                "nat_ip": ac.nat_i_p if hasattr(ac, 'nat_i_p') else None,
                                "network_tier": ac.network_tier if hasattr(ac, 'network_tier') and ac.network_tier else None
                            })
                    
                    instance_data["network_interfaces"].append(nic_data)
            
            # Process disks
            if instance.disks:
                for disk in instance.disks:
                    disk_data = {
                        "source": disk.source.split('/')[-1] if disk.source else None,
                        "device_name": disk.device_name if hasattr(disk, 'device_name') else None,
                        "mode": disk.mode if hasattr(disk, 'mode') and disk.mode else None,
                        "boot": disk.boot if hasattr(disk, 'boot') else False,
                        "auto_delete": disk.auto_delete if hasattr(disk, 'auto_delete') else None
                    }
                    
                    if disk.boot:
                        # Boot disk configuration
                        boot_disk_data = {
                            "source": disk.source.split('/')[-1] if disk.source else None,
                            "auto_delete": disk.auto_delete if hasattr(disk, 'auto_delete') else None,
                            "device_name": disk.device_name if hasattr(disk, 'device_name') else None
                        }
                        
                        # If the disk has initialize params (for new disks), include them
                        if hasattr(disk, 'initialize_params') and disk.initialize_params:
                            init_params = disk.initialize_params
                            boot_disk_data["initialize_params"] = {
                                "size": init_params.disk_size_gb if hasattr(init_params, 'disk_size_gb') else None,
                                "type": init_params.disk_type.split('/')[-1] if hasattr(init_params, 'disk_type') and init_params.disk_type else None,
                                "image": init_params.source_image.split('/')[-1] if hasattr(init_params, 'source_image') and init_params.source_image else None
                            }
                        instance_data["boot_disk"] = boot_disk_data
                    else:
                        instance_data["attached_disks"].append(disk_data)
            
            # Process metadata
            if hasattr(instance, 'metadata') and instance.metadata:
                if hasattr(instance.metadata, 'items') and instance.metadata.items:
                    for item in instance.metadata.items:
                        if item.key == 'startup-script':
                            instance_data["metadata_startup_script"] = item.value
                        else:
                            instance_data["metadata"][item.key] = item.value
            
            # Process service accounts
            if hasattr(instance, 'service_accounts') and instance.service_accounts:
                for sa in instance.service_accounts:
                    instance_data["service_accounts"].append({
                        "email": sa.email,
                        "scopes": list(sa.scopes) if sa.scopes else []
                    })
            
            # Process scheduling
            if hasattr(instance, 'scheduling') and instance.scheduling:
                instance_data["scheduling"] = {
                    "preemptible": instance.scheduling.preemptible if hasattr(instance.scheduling, 'preemptible') else None,
                    "on_host_maintenance": instance.scheduling.on_host_maintenance if hasattr(instance.scheduling, 'on_host_maintenance') and instance.scheduling.on_host_maintenance else None,
                    "automatic_restart": instance.scheduling.automatic_restart if hasattr(instance.scheduling, 'automatic_restart') else None,
                    "provisioning_model": instance.scheduling.provisioning_model if hasattr(instance.scheduling, 'provisioning_model') and instance.scheduling.provisioning_model else None,
                    "instance_termination_action": instance.scheduling.instance_termination_action if hasattr(instance.scheduling, 'instance_termination_action') else None
                }
            
            # Process guest accelerators (GPUs)
            if hasattr(instance, 'guest_accelerators') and instance.guest_accelerators:
                for accel in instance.guest_accelerators:
                    instance_data["guest_accelerators"].append({
                        "type": accel.accelerator_type.split('/')[-1] if accel.accelerator_type else None,
                        "count": accel.accelerator_count if hasattr(accel, 'accelerator_count') else 1
                    })
            
            # Process shielded instance config
            if hasattr(instance, 'shielded_instance_config') and instance.shielded_instance_config:
                sic = instance.shielded_instance_config
                instance_data["shielded_instance_config"] = {
                    "enable_secure_boot": sic.enable_secure_boot if hasattr(sic, 'enable_secure_boot') else None,
                    "enable_vtpm": sic.enable_vtpm if hasattr(sic, 'enable_vtpm') else None,
                    "enable_integrity_monitoring": sic.enable_integrity_monitoring if hasattr(sic, 'enable_integrity_monitoring') else None
                }
            
            # Process confidential instance config
            if hasattr(instance, 'confidential_instance_config') and instance.confidential_instance_config:
                cic = instance.confidential_instance_config
                instance_data["confidential_instance_config"] = {
                    "enable_confidential_compute": cic.enable_confidential_compute if hasattr(cic, 'enable_confidential_compute') else False
                }
            
            instances.append(instance_data)
            
    except exceptions.GoogleAPIError as e:
        typer.echo(f"Error fetching instances: {str(e)}", err=True)
        raise typer.Exit(code=1)
    
    return instances

@app.command("scan")
def scan_instances(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir"),
    project_id: Optional[str] = typer.Option(None, "--project-id", "-p"),
    zone: Optional[str] = typer.Option(None, "--zone", "-z"),
    with_deps: bool = typer.Option(False, "--with-deps")
):
    """Scans GCP Compute Engine instances and generates Terraform code."""
    from terraback.utils.cross_scan_registry import recursive_scan
    
    if not project_id:
        project_id = get_default_project_id()
        if not project_id:
            typer.echo("Error: No GCP project found", err=True)
            raise typer.Exit(code=1)
    
    if with_deps:
        typer.echo("Scanning GCP instances with dependencies...")
        recursive_scan(
            "gcp_instance",
            output_dir=output_dir,
            project_id=project_id,
            zone=zone
        )
    else:
        typer.echo(f"Scanning for GCP instances in project '{project_id}'...")
        if zone:
            typer.echo(f"Zone: {zone}")
        else:
            typer.echo("Zone: all zones")
        
        instance_data = get_instance_data(project_id, zone)
        
        if not instance_data:
            typer.echo("No instances found.")
            return
        
        # Generate Terraform files
        output_file = output_dir / "gcp_instance.tf"
        generate_tf(instance_data, "gcp_instance", output_file, provider="gcp")
        typer.echo(f"Generated Terraform for {len(instance_data)} instances -> {output_file}")
        
        # Generate import file
        generate_imports_file(
            "gcp_instance",
            instance_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )

@app.command("list")
def list_instances(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """List all GCP instance resources previously generated."""
    ImportManager(output_dir, "gcp_instance").list_all()

@app.command("import")
def import_instance(
    instance_id: str = typer.Argument(..., help="GCP instance ID (project/zone/name)"),
    output_dir: Path = typer.Option("generated", "-o", "--output-dir")
):
    """Run terraform import for a specific GCP instance."""
    ImportManager(output_dir, "gcp_instance").find_and_import(instance_id)

# Scan function for cross-scan registry
def scan_gcp_instances(
    output_dir: Path,
    project_id: str = None,
    zone: Optional[str] = None,
    region: Optional[str] = None,
    **kwargs
):
    """Scan function to be registered with cross-scan registry."""
    if not project_id:
        project_id = get_default_project_id()
    
    typer.echo(f"[Cross-scan] Scanning GCP instances in project {project_id}")
    
    instance_data = get_instance_data(project_id, zone)
    
    if instance_data:
        output_file = output_dir / "gcp_instance.tf"
        generate_tf(instance_data, "gcp_instance", output_file, provider="gcp")
        generate_imports_file(
            "gcp_instance",
            instance_data,
            remote_resource_id_key="id",
            output_dir=output_dir, provider="gcp"
        )
        typer.echo(f"[Cross-scan] Generated Terraform for {len(instance_data)} GCP instances")
