import tempfile
from pathlib import Path
from terraback.terraform_generator.writer import generate_tf


def test_policy_description_and_tags_render(tmp_path: Path):
    policy = {
        "PolicyName": "my-policy",
        "Path": "/",
        "Arn": "arn:aws:iam::123456789012:policy/my-policy",
        "PolicyDocument": "{}",
        "Description": "demo policy",
        "Tags": [
            {"Key": "Env", "Value": "dev"},
            {"Key": "Name", "Value": "my-policy"},
        ],
    }
    output_file = tmp_path / "policy.tf"
    generate_tf([policy], "iam_policies", output_file)

    content = output_file.read_text()
    assert 'description = "demo policy"' in content
    assert 'tags = {' in content
    assert '"Env" = "dev"' in content
    assert '"Name" = "my-policy"' in content


def test_policy_omits_optional_fields(tmp_path: Path):
    policy = {
        "PolicyName": "my-policy",
        "Path": "/",
        "Arn": "arn:aws:iam::123456789012:policy/my-policy",
        "PolicyDocument": "{}",
    }
    output_file = tmp_path / "policy.tf"
    generate_tf([policy], "iam_policies", output_file)

    content = output_file.read_text()
    assert "description" not in content
    assert "tags =" not in content

