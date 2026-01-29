import tempfile
from pathlib import Path

from terraback.terraform_generator.writer import generate_tf


def test_zone_template_generates_resource(tmp_path):
    zone = {
        "Name": "example.com.",
        "ZoneId": "Z123",
        "Config": {"Comment": "example", "PrivateZone": False},
        "VPCs": [],
        "Tags": [],
        "name_sanitized": "example_com",
    }

    output_file = tmp_path / "route53_zone.tf"
    generate_tf([zone], "route53_zone", output_file)

    content = output_file.read_text()
    assert 'resource "aws_route53_zone" "example_com"' in content
    assert 'name    = "example.com."' in content


def test_duplicate_zones_write_once(tmp_path: Path):
    zone = {
        "Name": "example.com.",
        "ZoneId": "Z123",
        "Config": {"Comment": "example", "PrivateZone": False},
        "VPCs": [],
        "Tags": [],
        "name_sanitized": "example_com",
    }

    zones = [zone, zone.copy()]
    unique = list({z["ZoneId"]: z for z in zones}.values())

    output_file = tmp_path / "route53_zone.tf"
    generate_tf(unique, "route53_zone", output_file)

    content = output_file.read_text()
    assert content.count('resource "aws_route53_zone"') == 1


def test_duplicate_zone_names_get_suffix(tmp_path: Path):
    base = {
        "Config": {"Comment": "example", "PrivateZone": False},
        "VPCs": [],
        "Tags": [],
        "Name": "example.com.",
        "name_sanitized": "example_com",
    }

    zone1 = {"ZoneId": "Z1", **base}
    zone2 = {"ZoneId": "Z2", **base}

    output_file = tmp_path / "route53_zone.tf"
    generate_tf([zone1, zone2], "route53_zone", output_file)

    content = output_file.read_text()
    assert content.count('resource "aws_route53_zone"') == 2
    assert '"example_com"' in content
    assert '"example_com_2"' in content
