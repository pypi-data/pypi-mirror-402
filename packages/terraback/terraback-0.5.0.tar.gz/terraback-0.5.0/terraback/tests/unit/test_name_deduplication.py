from pathlib import Path

from terraback.terraform_generator import writer


def test_preprocess_deduplicates_names():
    writer.reset_template_loader()
    writer.AutoDiscoveryTemplateLoader._instance = None
    loader = writer.get_template_loader()

    resources = [
        {"TopicName": "example", "name_sanitized": "dup"},
        {"TopicName": "example", "name_sanitized": "dup"},
        {"TopicName": "example", "name_sanitized": "dup"},
    ]

    processed = loader.preprocess_resources(resources, "sns_topic")
    names = [r["name_sanitized"] for r in processed]

    assert names == ["dup", "dup_2", "dup_3"]


def test_generated_tf_uses_unique_names(tmp_path: Path):
    topics = [
        {"TopicName": "demo", "name_sanitized": "dup"},
        {"TopicName": "demo", "name_sanitized": "dup"},
    ]

    output_file = tmp_path / "topics.tf"
    writer.generate_tf(topics, "sns_topic", output_file)

    content = output_file.read_text()

    assert content.count('resource "aws_sns_topic"') == 2
    assert 'aws_sns_topic" "dup"' in content
    assert 'aws_sns_topic" "dup_2"' in content
