from pathlib import Path
from terraback.terraform_generator.writer import generate_tf
from terraback.utils.template_syntax_fixer import TerraformSyntaxFixer


def test_sns_subscription_optional_fields(tmp_path: Path):
    sub = {
        "name_sanitized": "mysub",
        "TopicArn": "arn:aws:sns:us-east-1:123:topic",
        "Protocol": "email",
        "Endpoint": "user@example.com",
        "endpoint_auto_confirms": True,
        "confirmation_timeout_in_minutes": 5,
    }
    output_file = tmp_path / "sub.tf"
    generate_tf([sub], "sns_subscription", output_file)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    content = output_file.read_text()
    assert "endpoint_auto_confirms = true" in content
    assert "confirmation_timeout_in_minutes = 5" in content
