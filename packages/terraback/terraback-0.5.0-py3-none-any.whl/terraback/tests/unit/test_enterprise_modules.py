from pathlib import Path

from terraback.utils.enterprise_modules import EnterpriseModuleGenerator


def _write_tf(path: Path, content: str) -> None:
    path.write_text(content.strip() + "\n")


def test_enterprise_module_generation_aws(tmp_path):
    output_dir = tmp_path

    # Root Terraform files that should remain untouched
    _write_tf(output_dir / "provider.tf", "terraform {}")

    # Files containing resources that map to enterprise modules
    _write_tf(
        output_dir / "elbv2_load_balancer.tf",
        """
        resource "aws_lb" "main" {
          name = "example"
        }
        """,
    )

    _write_tf(
        output_dir / "elbv2_listener.tf",
        """
        resource "aws_lb_listener" "http" {
          load_balancer_arn = aws_lb.main.arn
        }
        """,
    )

    _write_tf(
        output_dir / "autoscaling_group.tf",
        """
        resource "aws_autoscaling_group" "asg" {
          name = "asg"
        }

        resource "aws_ami" "unmapped" {
          name = "example-ami"
        }
        """,
    )

    generator = EnterpriseModuleGenerator(provider="aws")
    generated = generator.generate(output_dir)

    module_files = {path.relative_to(output_dir) for path in generated}
    assert Path("modules/alb/lb.tf") in module_files
    assert Path("modules/alb/listeners.tf") in module_files
    assert Path("modules/asg/asg.tf") in module_files

    alb_lb = (output_dir / "modules" / "alb" / "lb.tf").read_text()
    assert "resource \"aws_lb\"" in alb_lb

    alb_listeners = (output_dir / "modules" / "alb" / "listeners.tf").read_text()
    assert "aws_lb_listener" in alb_listeners

    asg_file = (output_dir / "modules" / "asg" / "asg.tf").read_text()
    assert "aws_autoscaling_group" in asg_file

    # The original autoscaling file should now only contain the unmapped ami
    remaining = (output_dir / "autoscaling_group.tf").read_text()
    assert "aws_ami" in remaining
    assert "aws_autoscaling_group" not in remaining

    # Root files that are not part of module generation remain untouched
    assert (output_dir / "provider.tf").exists()


def test_enterprise_module_generation_azure(tmp_path):
    output_dir = tmp_path

    _write_tf(
        output_dir / "network.tf",
        """
        resource "azurerm_virtual_network" "vnet" {
          name                = "core-vnet"
          address_space       = ["10.0.0.0/16"]
          resource_group_name = "rg"
        }

        resource "azurerm_subnet" "subnet" {
          name                 = "app"
          resource_group_name  = "rg"
          virtual_network_name = azurerm_virtual_network.vnet.name
          address_prefixes     = ["10.0.1.0/24"]
        }
        """,
    )

    _write_tf(
        output_dir / "compute.tf",
        """
        resource "azurerm_linux_virtual_machine" "vm" {
          name                = "app-vm"
          resource_group_name = "rg"
          network_interface_ids = []
        }

        resource "azurerm_resource_group" "rg" {
          name     = "rg"
          location = "westus"
        }
        """,
    )

    generator = EnterpriseModuleGenerator(provider="azure")
    generated = generator.generate(output_dir)

    module_files = {path.relative_to(output_dir) for path in generated}
    assert Path("modules/networking/vnet/virtual-network.tf") in module_files
    assert Path("modules/networking/vnet/subnets.tf") in module_files
    assert Path("modules/compute/virtual-machine/vm.tf") in module_files

    vnet_content = (output_dir / "modules" / "networking" / "vnet" / "virtual-network.tf").read_text()
    assert "azurerm_virtual_network" in vnet_content

    subnet_content = (output_dir / "modules" / "networking" / "vnet" / "subnets.tf").read_text()
    assert "azurerm_subnet" in subnet_content

    vm_content = (output_dir / "modules" / "compute" / "virtual-machine" / "vm.tf").read_text()
    assert "azurerm_linux_virtual_machine" in vm_content

    # Original file with only module-managed resources should be removed
    assert not (output_dir / "network.tf").exists()

    # The compute file should retain the resource group that is not mapped
    remaining_compute = (output_dir / "compute.tf").read_text()
    assert "azurerm_resource_group" in remaining_compute
    assert "azurerm_linux_virtual_machine" not in remaining_compute


def test_enterprise_module_generation_gcp(tmp_path):
    output_dir = tmp_path

    _write_tf(
        output_dir / "network.tf",
        """
        resource "google_compute_network" "vpc" {
          name = "core-vpc"
        }

        resource "google_compute_subnetwork" "subnet" {
          name          = "app"
          network       = google_compute_network.vpc.name
          ip_cidr_range = "10.0.1.0/24"
        }
        """,
    )

    _write_tf(
        output_dir / "compute.tf",
        """
        resource "google_compute_instance" "vm" {
          name         = "instance"
          machine_type = "n1-standard-1"
          boot_disk {}
          network_interface {}
        }

        resource "google_dataflow_job" "unmapped" {
          name = "example-job"
          template_gcs_path = "gs://bucket/template"
          temp_gcs_location = "gs://bucket/temp"
        }
        """,
    )

    _write_tf(
        output_dir / "storage.tf",
        """
        resource "google_storage_bucket" "bucket" {
          name = "bucket"
        }
        """,
    )

    generator = EnterpriseModuleGenerator(provider="gcp")
    generated = generator.generate(output_dir)

    module_files = {path.relative_to(output_dir) for path in generated}
    assert Path("modules/networking/vpc/network.tf") in module_files
    assert Path("modules/networking/vpc/subnets.tf") in module_files
    assert Path("modules/compute/instances/instances.tf") in module_files
    assert Path("modules/storage/buckets/buckets.tf") in module_files

    network_module = (output_dir / "modules" / "networking" / "vpc" / "network.tf").read_text()
    assert "google_compute_network" in network_module

    subnet_module = (output_dir / "modules" / "networking" / "vpc" / "subnets.tf").read_text()
    assert "google_compute_subnetwork" in subnet_module

    instances_module = (output_dir / "modules" / "compute" / "instances" / "instances.tf").read_text()
    assert "google_compute_instance" in instances_module

    buckets_module = (output_dir / "modules" / "storage" / "buckets" / "buckets.tf").read_text()
    assert "google_storage_bucket" in buckets_module

    # ensure original files cleaned up or trimmed appropriately
    assert not (output_dir / "network.tf").exists()

    remaining_compute = (output_dir / "compute.tf").read_text()
    assert "google_dataflow_job" in remaining_compute
    assert "google_compute_instance" not in remaining_compute


def test_module_metadata_files_generation(tmp_path):
    """Test that variables.tf, outputs.tf, and locals.tf are created for each module."""
    output_dir = tmp_path

    _write_tf(
        output_dir / "lb.tf",
        """
        resource "aws_lb" "main" {
          name = "example-alb"
        }
        """,
    )

    _write_tf(
        output_dir / "ecs.tf",
        """
        resource "aws_ecs_cluster" "cluster" {
          name = "example-cluster"
        }

        resource "aws_ecs_service" "service" {
          name = "example-service"
        }
        """,
    )

    generator = EnterpriseModuleGenerator(provider="aws")
    generated = generator.generate(output_dir)

    # Check that metadata files were created for ALB module
    alb_dir = output_dir / "modules" / "alb"
    assert (alb_dir / "variables.tf").exists()
    assert (alb_dir / "outputs.tf").exists()
    assert (alb_dir / "locals.tf").exists()

    # Check that metadata files were created for ECS module
    ecs_dir = output_dir / "modules" / "ecs"
    assert (ecs_dir / "variables.tf").exists()
    assert (ecs_dir / "outputs.tf").exists()
    assert (ecs_dir / "locals.tf").exists()

    # Verify variables.tf content
    variables_content = (alb_dir / "variables.tf").read_text()
    assert "variable \"tags\"" in variables_content
    assert "variable \"environment\"" in variables_content

    # Verify outputs.tf was created (even if empty)
    outputs_content = (alb_dir / "outputs.tf").read_text()
    assert "# Module outputs" in outputs_content

    # Verify locals.tf content
    locals_content = (alb_dir / "locals.tf").read_text()
    assert "locals {" in locals_content
    assert "common_tags" in locals_content

    # Verify metadata files are included in generated list
    module_files = {path.relative_to(output_dir) for path in generated}
    assert Path("modules/alb/variables.tf") in module_files
    assert Path("modules/alb/outputs.tf") in module_files
    assert Path("modules/alb/locals.tf") in module_files


def test_readme_generation(tmp_path):
    """Test that README.md files are auto-generated for each module."""
    output_dir = tmp_path

    _write_tf(
        output_dir / "vpc.tf",
        """
        resource "aws_vpc" "main" {
          cidr_block = "10.0.0.0/16"
          enable_dns_support = true
        }

        resource "aws_subnet" "public" {
          vpc_id = aws_vpc.main.id
          cidr_block = "10.0.1.0/24"
        }
        """,
    )

    _write_tf(
        output_dir / "ec2.tf",
        """
        resource "aws_instance" "web" {
          ami = "ami-12345678"
          instance_type = "t2.micro"
        }
        """,
    )

    generator = EnterpriseModuleGenerator(provider="aws")
    generated = generator.generate(output_dir)

    # Check that README.md was created for VPC module
    vpc_dir = output_dir / "modules" / "vpc"
    readme_path = vpc_dir / "README.md"
    assert readme_path.exists()

    readme_content = readme_path.read_text()

    # Verify README structure
    assert "# Vpc" in readme_content
    assert "## Resources" in readme_content
    assert "## Inputs" in readme_content
    assert "## Outputs" in readme_content
    assert "## Usage" in readme_content

    # Verify resource types are listed
    assert "aws_vpc" in readme_content
    assert "aws_subnet" in readme_content

    # Verify variables table is present
    assert "| Name | Description | Type | Default |" in readme_content
    assert "| tags |" in readme_content
    assert "| environment |" in readme_content

    # Verify usage example is present
    assert "```hcl" in readme_content
    assert 'module "vpc"' in readme_content
    assert 'source = "./modules/vpc"' in readme_content

    # Check EC2 module README
    ec2_dir = output_dir / "modules" / "ec2-instance"
    ec2_readme_path = ec2_dir / "README.md"
    assert ec2_readme_path.exists()

    ec2_readme_content = ec2_readme_path.read_text()
    # Title converts dashes to spaces and uses title case
    assert "# Ec2 Instance" in ec2_readme_content
    assert "aws_instance" in ec2_readme_content

    # Verify README.md is included in generated list
    module_files = {path.relative_to(output_dir) for path in generated}
    assert Path("modules/vpc/README.md") in module_files
    assert Path("modules/ec2-instance/README.md") in module_files
