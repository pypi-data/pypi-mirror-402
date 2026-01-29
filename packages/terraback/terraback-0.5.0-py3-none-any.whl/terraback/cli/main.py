"""Terraback CLI main entry point."""
import typer
from terraback.utils.logging import setup_logging, get_logger
from terraback.core.analytics import track_command, track_event

# Import provider modules
from terraback.cli import aws, azure, gcp

# Import command modules
from terraback.cli.commands.clean import app as clean_app
from terraback.cli.commands.list import app as list_app
from terraback.cli.commands.analyse import app as analyse_app
from terraback.cli.commands.scan import app as scan_app
from terraback.cli.commands.terraform import app as terraform_app

# Import feature modules
from terraback.cli.license import app as license_app
from terraback.cli.cache import app as cache_app

logger = get_logger(__name__)

# Create main CLI app
cli = typer.Typer(
    name="terraback",
    help=(
        "Terraback: Generate Terraform from existing cloud infrastructure."
    ),
    no_args_is_help=True,
)

# Add provider sub-applications
cli.add_typer(aws.app, name="aws", help="Amazon Web Services resources")
cli.add_typer(azure.app, name="azure", help="Microsoft Azure resources")
cli.add_typer(gcp.app, name="gcp", help="Google Cloud Platform resources")

# Add command sub-applications
cli.add_typer(scan_app, name="scan", help="Resource scanning commands")
cli.add_typer(terraform_app, name="terraform", help="Terraform operations")
cli.add_typer(clean_app, name="clean", help="Clean generated files")
cli.add_typer(list_app, name="list", help="List scanned resources")
cli.add_typer(analyse_app, name="analyse", help="Analyse Terraform state")

# Add feature sub-applications
cli.add_typer(license_app, name="license", help="License management")
cli.add_typer(cache_app, name="cache", help="Cache management")



@cli.callback()
def main(
    verbose: bool = typer.Option(False, "--verbose", "-v", help="Enable verbose output"),
    debug: bool = typer.Option(False, "--debug", help="Enable debug output"),
):
    """Configure logging for the application."""
    if debug:
        setup_logging(level="DEBUG")
    elif verbose:
        setup_logging(level="INFO")
    else:
        setup_logging(level="WARNING")

    # Track CLI initialization
    track_event(
        "cli.initialized",
        verbose=verbose,
        debug=debug
    )


def run():
    """Entry point for the CLI."""
    cli()


if __name__ == "__main__":
    run()