from terraback.terraform_generator.writer import generate_tf


def test_alias_record_omits_ttl_and_records(tmp_path):
    record = {
        "ZoneId": "Z123",
        "Name": "alias.example.com.",
        "Type": "A",
        "TTL": 300,
        "ResourceRecords": [{"Value": "1.2.3.4"}],
        "AliasTarget": {
            "DNSName": "target.example.com",
            "HostedZoneId": "Z456",
            "EvaluateTargetHealth": False,
        },
    }

    output_file = tmp_path / "route53_record.tf"
    generate_tf([record], "route53_record", output_file)

    content = output_file.read_text()
    assert "alias" in content
    assert "ttl" not in content.lower()
    assert "records" not in content


def test_txt_record_value_not_double_quoted(tmp_path):
    record = {
        "ZoneId": "Z123",
        "Name": "txt.example.com.",
        "Type": "TXT",
        "TTL": 300,
        "ResourceRecords": [{"Value": "\"hello world\""}],
    }

    output_file = tmp_path / "txt_record.tf"
    generate_tf([record], "route53_record", output_file)

    content = output_file.read_text()
    # The record value should match the AWS value exactly without added escapes
    assert '"hello world"' in content
    assert '\\"hello world\\"' not in content

