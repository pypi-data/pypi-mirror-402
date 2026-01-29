import tempfile
from pathlib import Path

from terraback.terraform_generator.writer import generate_tf


def test_vpc_template_uses_scanned_dns_attributes(tmp_path: Path):
    vpc = {
        "VpcId": "vpc-123456",
        "CidrBlock": "10.1.0.0/16",
        "InstanceTenancy": "default",
        "EnableDnsSupport": False,
        "EnableDnsHostnames": True,
        "Tags": [{"Key": "Name", "Value": "my-vpc"}],
    }

    output_file = tmp_path / "vpc.tf"
    generate_tf([vpc], "vpc", output_file)

    content = output_file.read_text()
    assert "enable_dns_support   = false" in content
    assert "enable_dns_hostnames = true" in content
