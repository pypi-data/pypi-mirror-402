from terraback.terraform_generator.validator import TemplateValidator


def test_validator_reports_syntax_errors(tmp_path):
    tmpl_dir = tmp_path / "templates" / "aws"
    tmpl_dir.mkdir(parents=True)
    good = tmpl_dir / "good.tf.j2"
    good.write_text("{% for r in resources %}\nresource \"aws_s3_bucket\" \"{{ r.name }}\" {}\n{% endfor %}\n")
    bad = tmpl_dir / "bad.tf.j2"
    bad.write_text("{% if foo %}\nresource \"aws_s3_bucket\" \"bad\" {}\n")

    validator = TemplateValidator(templates_dir=tmp_path / "templates")
    results = validator.run_template_tests()

    assert "aws/bad.tf.j2" in results
    assert results["aws/bad.tf.j2"]
    assert "aws/good.tf.j2" not in results


def test_custom_check(tmp_path):
    tmpl_dir = tmp_path / "templates" / "aws"
    tmpl_dir.mkdir(parents=True)
    t = tmpl_dir / "check.tf.j2"
    t.write_text("resource \"aws_s3_bucket\" \"t\" {}\n\t")

    validator = TemplateValidator(templates_dir=tmp_path / "templates")

    def no_tabs(path, src):
        return ["tab character found"] if "\t" in src else []

    validator.add_check(no_tabs)
    results = validator.run_template_tests()

    rel = "aws/check.tf.j2"
    assert rel in results
    assert "tab character found" in results[rel]
