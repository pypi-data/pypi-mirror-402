from pathlib import Path
from unittest.mock import MagicMock, patch

import terraback.cli.aws.lambda_func.functions as functions
import terraback.cli.aws.lambda_func.layers as layers


def test_scan_lambda_functions_passes_used_layers(tmp_path):
    funcs = [{
        "FunctionName": "f1",
        "Layers": [{"Arn": "arn:aws:lambda:us-east-1:123:layer:util:1"}],
        "Tags": {},
    }]

    with (
        patch("terraback.cli.aws.lambda_func.functions.get_boto_session") as m_sess,
        patch("terraback.cli.aws.lambda_func.functions._get_all_function_names", return_value=["f1"]),
        patch("terraback.cli.aws.lambda_func.functions._get_function_details", return_value=funcs),
        patch("terraback.cli.aws.lambda_func.functions.generate_tf"),
        patch("terraback.cli.aws.lambda_func.functions.generate_imports_file"),
        patch("terraback.cli.aws.lambda_func.functions.scan_lambda_layers") as m_scan,
    ):
        m_sess.return_value.client.return_value = MagicMock()
        functions.scan_lambda_functions(Path(tmp_path))
        m_scan.assert_called_once()
        assert m_scan.call_args.kwargs["versions_in_use"] == {("util", 1)}


def test_fetch_layer_versions_parallel_skips_unused_versions():
    lambda_client = MagicMock()

    def fake_get(client, name):
        if name == "util":
            return [
                {"LayerVersionArn": "arn:layer:util:1", "Version": 1, "ImportId": "util:1"},
                {"LayerVersionArn": "arn:layer:util:2", "Version": 2, "ImportId": "util:2"},
            ]
        return [{"LayerVersionArn": "arn:layer:other:3", "Version": 3, "ImportId": "other:3"}]

    with patch("terraback.cli.aws.lambda_func.layers._get_layer_versions", side_effect=fake_get) as m_get:
        result = layers._fetch_layer_versions_parallel(
            lambda_client,
            ["util", "other"],
            versions_in_use={("util", 1)},
        )

    assert m_get.call_count == 1
    assert m_get.call_args.args[1] == "util"
    assert len(result) == 1
    assert result[0]["Version"] == 1
