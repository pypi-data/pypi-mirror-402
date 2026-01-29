import textwrap
from pathlib import Path

import pytest

from terraback.terraform_generator import writer
from terraback.utils.cross_scan_registry import cross_scan_registry


def _setup_templates(base: Path):
    templates_dir = base / "templates"
    (templates_dir / "aws").mkdir(parents=True)
    (templates_dir / "common").mkdir(parents=True)

    macros = templates_dir / "common" / "macros.j2"
    macros.write_text(textwrap.dedent(
        """
        {% macro render_depends_on(dep_list, indent=2) %}
        {% if dep_list %}
        {{ ' ' * indent }}depends_on = [
        {% for dep in dep_list %}
        {{ ' ' * (indent + 2) }}{{ dep }}{{ ',' if not loop.last }}
        {% endfor %}
        {{ ' ' * indent }}]
        {% endif %}
        {% endmacro %}
        """
    ))

    template = templates_dir / "aws" / "my_resource.tf.j2"
    template.write_text(textwrap.dedent(
        """
        {% import 'common/macros.j2' as macros %}
        {% for res in resources %}
        resource "{{ resource_type }}" "{{ res.name_sanitized }}" {
          name = "{{ res.name }}"
        {{ macros.render_depends_on(res.depends_on, indent=2) }}
        }
        {% endfor %}
        """
    ))

    return templates_dir


@pytest.fixture(autouse=True)
def clear_registry(tmp_path):
    cross_scan_registry.set_output_dir(tmp_path)
    cross_scan_registry.clear()
    yield
    cross_scan_registry.clear()


def test_generate_tf_writes_depends_on(tmp_path: Path):
    templates = _setup_templates(tmp_path)

    writer.reset_template_loader()
    writer.AutoDiscoveryTemplateLoader._instance = None
    writer._loader = writer.AutoDiscoveryTemplateLoader(template_dir_override=templates)

    cross_scan_registry.register("my_resource", "r1", {"name": "example"})
    cross_scan_registry.register("dep_resource", "d1", {"name": "dep"})
    cross_scan_registry.add_dependency("my_resource", "r1", "dep_resource", "d1")

    output_file = tmp_path / "output.tf"
    writer.generate_tf([{"id": "r1", "name": "example"}], "my_resource", output_file)

    content = output_file.read_text()
    assert "depends_on" in content
    assert "aws_dep_resource.d1" in content

    # Reset loader for other tests
    writer.reset_template_loader()
    writer.AutoDiscoveryTemplateLoader._instance = None
