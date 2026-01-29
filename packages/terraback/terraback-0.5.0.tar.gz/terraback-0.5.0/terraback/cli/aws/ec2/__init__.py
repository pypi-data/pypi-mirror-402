# terraback/cli/aws/ec2/__init__.py
"""EC2 module for AWS provider."""

import typer
from pathlib import Path
from typing import Optional

# Import EC2 scan functions
from .instances import scan_ec2, list_ec2, import_ec2
from .volumes import scan_volumes, list_volumes, import_volume
from .snapshots import scan_snapshots, list_snapshots, import_snapshot
from .amis import scan_amis, list_amis, import_ami
from .key_pairs import scan_key_pairs, list_key_pairs, import_key_pair
from .launch_templates import scan_launch_templates, list_launch_templates, import_launch_template
from .network_interfaces import scan_network_interfaces, list_network_interfaces, import_network_interface

# Import cross-scan registry
from terraback.utils.cross_scan_registry import register_scan_function, cross_scan_registry

# Create EC2 app
app = typer.Typer(
    name="ec2",
    help="Manage EC2 resources like instances, volumes, snapshots, AMIs, and more.",
    no_args_is_help=True
)

# --- EC2 Instance Commands ---
@app.command(name="scan-instances", help="Scan EC2 instances.")
def scan_instances_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, help="AWS CLI profile to use"),
    region: str = typer.Option("us-east-1", help="AWS region"),
    with_deps: bool = typer.Option(False, help="Scan with dependencies")
):
    scan_ec2(output_dir, profile or "", region, with_deps)

@app.command(name="list-instances", help="List scanned EC2 instances.")
def list_instances_command(output_dir: Path = typer.Option("generated")):
    list_ec2(output_dir)

@app.command(name="import-instance", help="Import an EC2 instance by ID.")
def import_instance_command(
    instance_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_ec2(instance_id, output_dir)

# --- EBS Volume Commands ---
@app.command(name="scan-volumes", help="Scan EBS volumes.")
def scan_volumes_command(
    output_dir: Path = typer.Option("generated", help="Directory to save Terraform files"),
    profile: Optional[str] = typer.Option(None, help="AWS CLI profile to use"),
    region: str = typer.Option("us-east-1", help="AWS region")
):
    scan_volumes(output_dir, profile or "", region)

@app.command(name="list-volumes", help="List scanned EBS volumes.")
def list_volumes_command(output_dir: Path = typer.Option("generated")):
    list_volumes(output_dir)

@app.command(name="import-volume", help="Import an EBS volume by ID.")
def import_volume_command(
    volume_id: str,
    output_dir: Path = typer.Option("generated")
):
    import_volume(volume_id, output_dir)

# --- Registration Function ---
def register():
    """Register all EC2 resources with cross-scan registry."""
    # EC2 instances
    register_scan_function("aws_ec2", scan_ec2)
    
    # EBS volumes
    register_scan_function("aws_ebs_volume", scan_volumes)
    
    # EBS snapshots
    register_scan_function("aws_ebs_snapshot", scan_snapshots)
    
    # AMIs
    register_scan_function("aws_ami", scan_amis)
    
    # Key pairs
    register_scan_function("aws_key_pair", scan_key_pairs)
    
    # Launch templates
    register_scan_function("aws_launch_template", scan_launch_templates)
    
    # Network interfaces
    register_scan_function("aws_network_interface", scan_network_interfaces)
    
    # Define dependencies
    cross_scan_registry.register_dependency("aws_ec2", "aws_vpc")
    cross_scan_registry.register_dependency("aws_ec2", "aws_security_groups")
    cross_scan_registry.register_dependency("aws_ec2", "aws_subnets")
    cross_scan_registry.register_dependency("aws_ec2", "aws_key_pair")
    cross_scan_registry.register_dependency("aws_ec2", "aws_ami")
    cross_scan_registry.register_dependency("aws_ec2", "aws_ebs_volume")
    cross_scan_registry.register_dependency("aws_ec2", "aws_network_interface")
    cross_scan_registry.register_dependency("aws_ebs_volume", "aws_ebs_snapshot")
    cross_scan_registry.register_dependency("aws_launch_template", "aws_ami")
    cross_scan_registry.register_dependency("aws_launch_template", "aws_security_groups")
    cross_scan_registry.register_dependency("aws_network_interface", "aws_subnets")