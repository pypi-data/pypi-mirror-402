from pathlib import Path

def clean_generated_files(output_dir: Path, resource_prefix: str):
    """
    Deletes generated .tf and _import.json files for a given resource.
    Example: "ec2" -> deletes ec2.tf and ec2_import.json
    """
    filenames = [
        f"{resource_prefix}.tf",
        f"{resource_prefix}_import.json",
    ]
    for filename in filenames:
        file_path = output_dir / filename
        if file_path.exists():
            file_path.unlink()


def clean_import_artifacts(terraform_dir: Path) -> None:
    """Remove temporary Terraform files created during import."""
    patterns = [
        "terraback_import_blocks.tf",
        "import.plan",
        "import.tfplan",
        "terraform.tfstate",
        "terraform.tfstate.backup",
        "terraform_import_debug.log",
        "import_*.tf",
        "generated.tf",
        "workspace_*",
    ]
    for pattern in patterns:
        for path in terraform_dir.glob(pattern):
            if path.is_file():
                path.unlink()
            elif path.is_dir():
                import shutil
                shutil.rmtree(path, ignore_errors=True)
