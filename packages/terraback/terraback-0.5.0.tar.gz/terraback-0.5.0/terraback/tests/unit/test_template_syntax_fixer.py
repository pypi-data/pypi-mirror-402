import textwrap
from terraback.utils.template_syntax_fixer import TerraformSyntaxFixer


def test_fix_missing_commas_tags(tmp_path):
    tf_content = textwrap.dedent(
        """
        resource "aws_instance" "ex" {
          tags = {"Name" = "example" "Env" = "dev"}
        }
        """
    )
    tf_file = tmp_path / "instance.tf"
    tf_file.write_text(tf_content)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    fixed = tf_file.read_text()
    assert 'tags = {"Name" = "example", "Env" = "dev"}' in fixed
    assert 'tags = {,' not in fixed


def test_split_double_close_brace(tmp_path):
    tf_content = textwrap.dedent(
        """
        resource "aws_example" "ex" {
          gateway_id = "gw"} }
        """
    )
    tf_file = tmp_path / "double.tf"
    tf_file.write_text(tf_content)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    fixed = tf_file.read_text()
    assert '}\n}' in fixed


def test_split_brace_followed_by_argument(tmp_path):
    tf_content = textwrap.dedent(
        """
        resource "aws_example" "ex" {
          dimension {
            name = "x"
          } alarm_actions = ["arn"]
        }
        """
    )
    tf_file = tmp_path / "argument.tf"
    tf_file.write_text(tf_content)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    fixed = tf_file.read_text()
    assert '}\n  alarm_actions' in fixed


def test_assignment_followed_by_brace(tmp_path):
    tf_content = textwrap.dedent(
        """
        resource "aws_cloudfront_distribution" "ex" {
          cache_policy_id = "abcd"}
        }
        """
    )
    tf_file = tmp_path / "policy.tf"
    tf_file.write_text(tf_content)

    fixer = TerraformSyntaxFixer(tmp_path)
    fixer.fix_all_files()

    fixed = tf_file.read_text()
    assert 'cache_policy_id = "abcd"\n}' in fixed
