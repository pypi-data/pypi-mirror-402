from pathlib import Path
from unittest.mock import patch

from terraback.terraform_generator.writer import generate_tf
from terraback.utils.template_syntax_fixer import TerraformSyntaxFixer
from terraback.utils.terraform_checker import TerraformChecker


class Result:
    def __init__(self, returncode=0, stdout="", stderr=""):
        self.returncode = returncode
        self.stdout = stdout
        self.stderr = stderr


def _fake_run(cmd, **kwargs):
    return Result()


def _validate_directory(tmp_path: Path) -> bool:
    with (
        patch("terraback.utils.terraform_checker.TerraformChecker.check_terraform_required", return_value=True),
        patch("subprocess.run", side_effect=_fake_run) as m_run,
    ):
        success, _ = TerraformChecker.safe_terraform_validate(tmp_path)
    m_run.assert_called_with(
        ["terraform", "validate"],
        cwd=tmp_path,
        capture_output=True,
        text=True,
        timeout=60,
    )
    return success


def test_api_gateway_rest_api_validates(tmp_path: Path):
    api = {"name": "my-api", "description": "demo", "tags": {"Env": "dev"}}
    output_file = tmp_path / "api_gateway.tf"
    generate_tf([api], "api_gateway_rest_api", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)


def test_s3_bucket_validates(tmp_path: Path):
    bucket = {"Name": "my-bucket"}
    output_file = tmp_path / "bucket.tf"
    generate_tf([bucket], "s3_bucket", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)


def test_route53_record_validates(tmp_path: Path):
    record = {"ZoneId": "Z1", "Name": "www.example.com", "Type": "A"}
    output_file = tmp_path / "record.tf"
    generate_tf([record], "route53_record", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)


def test_iam_role_description_has_newline(tmp_path: Path):
    role = {
        "RoleName": "role1",
        "Path": "/",
        "AssumeRolePolicyDocument": {"a": "b"},
        "Description": "desc",
        "MaxSessionDuration": 3600,
        "PermissionsBoundary": "arn:boundary",
        "Tags": [{"Key": "Name", "Value": "role1"}],
    }
    output_file = tmp_path / "role.tf"
    generate_tf([role], "iam_roles", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)

    content = output_file.read_text()
    assert "})\n\n  description" in content


def test_rds_subnet_group_spacing(tmp_path: Path):
    group = {
        "DBSubnetGroupName": "sg",
        "DBSubnetGroupDescription": "desc",
        "Subnets": [{"SubnetIdentifier": "sub-123"}],
    }
    output_file = tmp_path / "subnet.tf"
    generate_tf([group], "rds_subnet_group", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)

    content = output_file.read_text()
    assert "subnet_ids = [\n" in content
    assert "\n  ]" in content


def test_cloudfront_origin_timeout_spacing(tmp_path: Path):
    dist = {
        "name_sanitized": "ex",
        "DistributionConfigFormatted": {
            "Comment": "",
            "DefaultRootObject": "",
            "Enabled": True,
            "IsIPV6Enabled": True,
            "PriceClass": "PriceClass_All",
            "origins_formatted": [
                {
                    "domain_name": "example.com",
                    "origin_id": "origin1",
                    "connection_attempts": 3,
                    "connection_timeout": 7,
                    "s3_origin_config": {"OriginAccessIdentity": ""},
                }
            ],
            "default_cache_behavior_formatted": {"target_origin_id": "origin1"},
        },
    }

    output_file = tmp_path / "cf.tf"
    generate_tf([dist], "cloudfront_distribution", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)

    content = output_file.read_text()
    assert "connection_timeout  = 7\n" in content
    assert "\n    s3_origin_config" in content


def test_cloudfront_acm_certificate_rendered(tmp_path: Path):
    dist = {
        "name_sanitized": "ex",
        "DistributionConfigFormatted": {
            "Comment": "",
            "DefaultRootObject": "",
            "Enabled": True,
            "IsIPV6Enabled": True,
            "PriceClass": "PriceClass_All",
            "origins_formatted": [
                {
                    "domain_name": "example.com",
                    "origin_id": "origin1",
                    "s3_origin_config": {"OriginAccessIdentity": ""},
                }
            ],
            "default_cache_behavior_formatted": {"target_origin_id": "origin1"},
            "viewer_certificate_formatted": {
                "acm_certificate_arn": "arn:aws:acm:us-east-1:111111111111:certificate/abcd",
                "ssl_support_method": "sni-only",
                "minimum_protocol_version": "TLSv1.2_2021",
                "cloudfront_default_certificate": False,
            },
        },
    }

    output_file = tmp_path / "cf.tf"
    generate_tf([dist], "cloudfront_distribution", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)

    content = output_file.read_text()
    assert "acm_certificate_arn" in content
    assert "sni-only" in content
    assert "TLSv1.2_2021" in content
    assert "cloudfront_default_certificate" not in content


def test_cloudfront_optional_blocks_rendered(tmp_path: Path):
    dist = {
        "name_sanitized": "ex",
        "DistributionConfigFormatted": {
            "Comment": "",
            "DefaultRootObject": "",
            "Enabled": True,
            "IsIPV6Enabled": True,
            "PriceClass": "PriceClass_All",
            "origins_formatted": [
                {
                    "domain_name": "example.com",
                    "origin_id": "origin1",
                    "s3_origin_config": {"OriginAccessIdentity": ""},
                }
            ],
            "default_cache_behavior_formatted": {"target_origin_id": "origin1"},
            "cache_behaviors_formatted": [
                {
                    "path_pattern": "images/*",
                    "target_origin_id": "origin1",
                    "viewer_protocol_policy": "redirect-to-https",
                }
            ],
            "custom_error_responses_formatted": [
                {
                    "error_code": 404,
                    "response_page_path": "/404.html",
                    "response_code": "404",
                    "error_caching_min_ttl": 30,
                }
            ],
            "logging_config_formatted": {
                "enabled": True,
                "include_cookies": False,
                "bucket": "logs.s3.amazonaws.com",
                "prefix": "prefix/",
            },
            "geo_restriction_formatted": {
                "restriction_type": "whitelist",
                "locations": ["US"],
            },
        },
    }

    output_file = tmp_path / "cf.tf"
    generate_tf([dist], "cloudfront_distribution", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    assert _validate_directory(tmp_path)

    content = output_file.read_text()
    assert "custom_error_response" in content
    assert "ordered_cache_behavior" in content
    assert "logging_config" in content
    assert "geo_restriction" in content
