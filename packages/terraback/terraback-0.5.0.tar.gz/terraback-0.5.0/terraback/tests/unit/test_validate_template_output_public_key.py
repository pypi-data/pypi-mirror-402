import pytest
from terraback.terraform_generator import writer


def test_public_key_line_not_split():
    writer.reset_template_loader()
    writer.AutoDiscoveryTemplateLoader._instance = None
    loader = writer.get_template_loader()

    line = 'public_key = "ssh-rsa AAAAB3Nza...hGiTAX= generated-by-azure"'
    output = loader.validate_template_output(line, "ssh_key")
    assert output.strip().splitlines() == [line]

