import os
from pathlib import Path
from unittest.mock import patch

import typer

import pytest

from terraback.cli.commands.terraform import _terraform_plan as terraform_plan


def _fake_result(returncode=0, stdout="", stderr=""):
    class Result:
        def __init__(self):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr
    return Result()


def test_plan_from_subdirectory(tmp_path, monkeypatch):
    home = tmp_path / "home"
    tf_dir = home / "tf"
    tf_dir.mkdir(parents=True)
    (tf_dir / ".terraform").mkdir()

    # ensure ~ expands to our temp home
    monkeypatch.setenv("HOME", str(home))

    subdir = tmp_path / "work"
    subdir.mkdir()

    with (
        patch("terraback.cli.commands.terraform._check_terraform_installation", return_value=True),
        patch("subprocess.run", return_value=_fake_result()) as m_run,
    ):
        cwd = os.getcwd()
        os.chdir(subdir)
        try:
            terraform_plan(terraform_dir="~/tf", output=None)
        finally:
            os.chdir(cwd)

    m_run.assert_called_with(
        ["terraform", "plan"],
        cwd=tf_dir,
        capture_output=True,
        text=True,
        check=False,
    )


def test_plan_failure_outputs_stderr(tmp_path, capsys):
    tf_dir = tmp_path / "tf"
    tf_dir.mkdir()
    (tf_dir / ".terraform").mkdir()

    with (
        patch("terraback.cli.commands.terraform._check_terraform_installation", return_value=True),
        patch("subprocess.run", return_value=_fake_result(returncode=1, stderr="boom")),
    ):
        with pytest.raises(typer.Exit):
            terraform_plan(terraform_dir=tf_dir, output=None)

    captured = capsys.readouterr()
    assert "boom" in captured.out or "boom" in captured.err
