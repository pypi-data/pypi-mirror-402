from pathlib import Path
from typing import Optional
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager

def scan_vpcs(output_dir: Path, profile: Optional[str] = None, region: str = "us-east-1"):
    boto_session = get_boto_session(profile, region)
    ec2_client = boto_session.client("ec2")
    vpcs = ec2_client.describe_vpcs()["Vpcs"]
    
    # Fetch DNS attributes for each VPC
    for vpc in vpcs:
        vpc_id = vpc["VpcId"]
        try:
            # Get enableDnsSupport attribute
            dns_support = ec2_client.describe_vpc_attribute(
                VpcId=vpc_id,
                Attribute='enableDnsSupport'
            )
            vpc['EnableDnsSupport'] = dns_support.get('EnableDnsSupport', {}).get('Value', True)
            
            # Get enableDnsHostnames attribute
            dns_hostnames = ec2_client.describe_vpc_attribute(
                VpcId=vpc_id,
                Attribute='enableDnsHostnames'
            )
            vpc['EnableDnsHostnames'] = dns_hostnames.get('EnableDnsHostnames', {}).get('Value', False)
        except Exception as e:
            print(f"Warning: Could not fetch DNS attributes for VPC {vpc_id}: {e}")
            # Default values if we can't fetch
            vpc['EnableDnsSupport'] = True
            vpc['EnableDnsHostnames'] = False
    
    # Add sanitized names and normalize field names for template compatibility
    for vpc in vpcs:
        vpc_id = vpc['VpcId']
        vpc['name_sanitized'] = f"resource_vpc_{vpc_id.replace('-', '')}"
        
        # Add normalized field names that match template expectations
        vpc['vpcId'] = vpc_id  # Template expects vpcId 
        vpc['vpc_id'] = vpc_id  # Alternative field name
        vpc['cidrBlock'] = vpc.get('CidrBlock', '')  # Template expects cidrBlock
        vpc['cidr_block'] = vpc.get('CidrBlock', '')  # Alternative field name
        
        # Normalize DNS attributes
        vpc['enableDnsSupport'] = vpc.get('EnableDnsSupport', True)
        vpc['enable_dns_support'] = vpc.get('EnableDnsSupport', True)
        vpc['enableDnsHostnames'] = vpc.get('EnableDnsHostnames', False) 
        vpc['enable_dns_hostnames'] = vpc.get('EnableDnsHostnames', False)
        
        # Add instance tenancy if available
        if 'InstanceTenancy' in vpc:
            vpc['instanceTenancy'] = vpc['InstanceTenancy']
            vpc['instance_tenancy'] = vpc['InstanceTenancy']
    
    output_file = output_dir / "vpc.tf"
    generate_tf(vpcs, "aws_vpc", output_file)
    print(f"Generated Terraform for {len(vpcs)} VPCs -> {output_file}")
    generate_imports_file("vpc", vpcs, remote_resource_id_key="VpcId", output_dir=output_dir, provider="aws")

def list_vpcs(output_dir: Path):
    ImportManager(output_dir, "vpc").list_all()

def import_vpc(vpc_id: str, output_dir: Path):
    ImportManager(output_dir, "vpc").find_and_import(vpc_id)
