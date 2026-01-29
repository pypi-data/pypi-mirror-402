from pathlib import Path

from terraback.terraform_generator.writer import generate_tf


def test_resources_separated_by_blank_line(tmp_path: Path):
    vpc1 = {
        "VpcId": "vpc-aaa",
        "CidrBlock": "10.0.0.0/16",
        "InstanceTenancy": "default",
    }
    vpc2 = {
        "VpcId": "vpc-bbb",
        "CidrBlock": "10.1.0.0/16",
        "InstanceTenancy": "default",
    }

    output_file = tmp_path / "vpc.tf"
    generate_tf([vpc1, vpc2], "vpc", output_file)

    content = output_file.read_text()
    assert "}\n\nresource" in content

