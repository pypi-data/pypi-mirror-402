"""Terraform-related commands for plan and validation operations."""
import typer
from pathlib import Path
from typing import Optional, List
import sys
import subprocess
import shutil
import platform

from terraback.utils.logging import get_logger
from terraback.terraform_generator.writer import (
    get_template_loader,
    validate_all_templates,
)
from terraback.utils.terraform_checker import TerraformChecker

logger = get_logger(__name__)

app = typer.Typer(name="terraform", help="Terraform operations")


def _check_terraform_installation() -> bool:
    """Check if Terraform is installed and show helpful error if not."""
    if shutil.which('terraform') is not None:
        return True
    typer.echo()
    typer.secho("Error: Terraform Not Found", fg="red", bold=True)
    typer.echo()
    typer.echo("Terraback requires Terraform to be installed and available in your PATH.")
    typer.echo()
    typer.secho("Installation Options:", fg="blue", bold=True)
    typer.echo()
    system = platform.system().lower()
    if system == 'darwin':
        typer.echo('macOS:')
        typer.echo('  brew tap hashicorp/tap')
        typer.echo('  brew install hashicorp/tap/terraform')
    elif system == 'linux':
        typer.echo('Linux:')
        typer.echo('  # Ubuntu/Debian:')
        typer.echo('  wget -O- https://apt.releases.hashicorp.com/gpg | sudo gpg --dearmor -o /usr/share/keyrings/hashicorp-archive-keyring.gpg')
        typer.echo('  sudo apt update && sudo apt install terraform')
        typer.echo()
        typer.echo('  # Or download from: https://www.terraform.io/downloads')
    elif system == 'windows':
        typer.echo('Windows:')
        typer.echo('  # Using Chocolatey:')
        typer.echo('  choco install terraform')
        typer.echo()
        typer.echo('  # Or download from: https://www.terraform.io/downloads')
    else:
        typer.echo('Download from: https://www.terraform.io/downloads')
    typer.echo()
    typer.secho('Official Download:', fg='cyan')
    typer.echo('  https://www.terraform.io/downloads')
    typer.echo()
    typer.echo("After installation, make sure 'terraform' is available in your PATH.")
    typer.echo('Test with: terraform version')
    typer.echo()
    return False


def _terraform_plan(terraform_dir: Path, output: Optional[Path] = None):
    """Run terraform plan on imported resources."""
    terraform_dir = Path(terraform_dir).expanduser().resolve()
    if not terraform_dir.is_dir():
        typer.secho(f"Error: Terraform directory {terraform_dir} does not exist", fg=typer.colors.RED)
        raise typer.Exit(code=1)
    success = _check_terraform_installation()
    if not success:
        raise typer.Exit(code=1)
    if not (terraform_dir / '.terraform').exists():
        typer.echo("Terraform not initialized. Running 'terraform init'...")
        success, error = TerraformChecker.safe_terraform_init(terraform_dir)
        if not success:
            typer.secho(f"Error: {error}", fg=typer.colors.RED)
            raise typer.Exit(code=1)
    cmd = ['terraform', 'plan']
    if output:
        cmd.extend(['-out', str(output)])
    typer.echo('Running terraform plan...')
    result = subprocess.run(
        cmd,
        cwd=terraform_dir,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        typer.secho("terraform plan failed", fg="red")
        typer.secho(result.stderr or result.stdout)
        raise typer.Exit(code=1)
    typer.echo(result.stdout)


@app.command("plan")
def cmd_terraform_plan(
    output_dir: Path = typer.Option("generated", "-o", "--output-dir", help="Directory containing Terraform files"),
    detailed: bool = typer.Option(False, "--detailed", "-d", help="Show detailed plan output"),
    out: Optional[Path] = typer.Option(None, "--out", help="Save plan to file"),
    target: Optional[List[str]] = typer.Option(None, "--target", "-t", help="Target specific resources"),
    var_file: Optional[Path] = typer.Option(None, "--var-file", help="Path to variables file"),
    refresh: bool = typer.Option(True, "--refresh/--no-refresh", help="Update state before planning"),
    workspace: Optional[str] = typer.Option(None, "--workspace", help="Terraform workspace to use"),
):
    """Run Terraform plan on generated files."""
    _terraform_plan(
        terraform_dir=output_dir,
        output=out,
    )


@app.command("validate-templates")
def cmd_validate_templates(
    fix: bool = typer.Option(False, "--fix", help="Attempt to fix template issues"),
    show_warnings: bool = typer.Option(False, "--show-warnings", help="Show warnings in addition to errors"),
):
    """Validate all Terraform templates."""
    template_loader = get_template_loader()
    errors, warnings = validate_all_templates(template_loader, fix=fix)
    
    if errors:
        typer.echo("\n[X] Template validation failed with errors:", err=True)
        for error in errors:
            typer.echo(f"  - {error}", err=True)
        sys.exit(1)
    elif warnings and show_warnings:
        typer.echo("\n[!]  Template validation passed with warnings:")
        for warning in warnings:
            typer.echo(f"  - {warning}")
    else:
        typer.echo("[OK] All templates validated successfully!")


@app.callback()
def terraform_callback(ctx: typer.Context):
    """Check Terraform installation before running commands."""
    if ctx.invoked_subcommand:
        if ctx.invoked_subcommand in ["plan"]:
            if not _check_terraform_installation():
                typer.echo("[X] Terraform is not installed or not in PATH", err=True)
                typer.echo("\nPlease install Terraform from: https://www.terraform.io/downloads", err=True)
                raise typer.Exit(1)