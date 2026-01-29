import typer
from terraback.core.license import (
    activate_license,
    get_active_license,
    get_license_status,
)

app = typer.Typer(help="Manage your Terraback license.")


@app.command("status")
def license_status():
    """Check the current license status and tier with validation details."""
    status = get_license_status()
    typer.echo(
        f"Active Feature Tier: {typer.style(status['active_tier'].capitalize(), bold=True)}"
    )
    if status["has_license"]:
        typer.secho("\nLicense Details:", fg=typer.colors.GREEN)
        typer.echo(f"  - Email: {status.get('email', 'N/A')}")
        typer.echo(f"  - Tier: {status.get('tier', 'N/A').capitalize()}")
        typer.echo(f"  - Expires: {status.get('expires', 'N/A')}")
        if status.get("order_id"):
            typer.echo(f"  - Order ID: {status.get('order_id')}")
        # Show beta tier info
        if status.get('tier') == 'beta':
            typer.secho("\n  Beta License - Professional features enabled", fg=typer.colors.BLUE)
        if "days_since_online_validation" in status:
            days_since = status["days_since_online_validation"]
            validation_count = status.get("validation_count", 0)
            typer.echo("\nValidation Status:")
            typer.echo(f"  - Days since last online check: {days_since}")
            typer.echo(f"  - Total validations performed: {validation_count}")
            from terraback.core.license import ValidationSettings
            if days_since >= ValidationSettings.MAX_OFFLINE_DAYS:
                typer.secho(
                    "  VALIDATION REQUIRED - Connect to internet",
                    fg=typer.colors.RED,
                    bold=True,
                )
            elif days_since >= ValidationSettings.OFFLINE_GRACE_DAYS:
                remaining = ValidationSettings.MAX_OFFLINE_DAYS - days_since
                typer.secho(
                    f"  Please connect to internet soon ({remaining} days remaining)",
                    fg=typer.colors.YELLOW,
                )
            elif days_since >= ValidationSettings.VALIDATION_INTERVAL_DAYS:
                typer.secho(
                    "  Validation recommended - connect to internet",
                    fg=typer.colors.YELLOW,
                )
            else:
                typer.secho("  Validation up to date", fg=typer.colors.GREEN)
    else:
        typer.secho("\nNo active license key found.", fg=typer.colors.YELLOW)
        typer.echo("Running in Community mode.")
        typer.echo("\nCommunity Edition includes:")
        typer.echo("  Unlimited core resources (EC2, VPC, S3, VMs, VNets, Storage)")
        typer.echo("  Basic dependency mapping")
        typer.echo("  Multi-cloud support (AWS, Azure, GCP)")
        typer.echo("  Community support via GitHub")
        typer.echo("\nTo unlock all 50+ services (RDS, Lambda, EKS, etc.):")
        typer.echo("  Get lifetime license ($499): https://terraback.lemonsqueezy.com/checkout/buy/d7168719-2f22-41d4-8c8b-84dcfc96ca51")
        typer.echo("  Activate: terraback license activate <key>")


@app.command("activate")
def license_activate(key: str = typer.Argument(..., help="Your license key.")):
    """Activate a new license key with enhanced security."""
    if activate_license(key):
        typer.secho("License activated successfully!", fg=typer.colors.GREEN, bold=True)
        typer.echo()
        status = get_license_status()
        if status["has_license"]:
            typer.echo(f"Licensed to: {status.get('email', 'N/A')}")
            typer.echo(f"Tier: {status.get('tier', 'N/A').capitalize()}")
            typer.echo(f"Expires: {status.get('expires', 'N/A')}")
            from terraback.core.license import _get_machine_fingerprint
            fingerprint = _get_machine_fingerprint()
            typer.echo(f"Machine fingerprint: {fingerprint[:8]}... (for security)")
            typer.echo("\nYour license is now protected with:")
            typer.echo("  Machine fingerprinting")
            typer.echo("  Periodic online validation")
            typer.echo("  Clock tampering detection")
    else:
        typer.secho("License activation failed.", fg=typer.colors.RED, bold=True)
        typer.echo("Please check that:")
        typer.echo("  - The license key is copied correctly")
        typer.echo("  - The license hasn't expired")
        typer.echo("  - You have internet connection")
        typer.echo("  - The license hasn't been activated on another machine")
        typer.echo("\nIf you continue to have issues, contact support@terraback.io")
        raise typer.Exit(code=1)


@app.command("refresh")
def license_refresh():
    """Force online license validation to refresh local data."""
    from terraback.core.license import force_license_refresh
    typer.echo("Attempting to refresh license validation...")
    if force_license_refresh():
        typer.secho("License validation refreshed successfully", fg=typer.colors.GREEN)
        status = get_license_status()
        if "days_since_online_validation" in status:
            typer.echo("Last validation: just now")
            typer.echo(f"Total validations: {status.get('validation_count', 0)}")
    else:
        typer.secho("License refresh failed", fg=typer.colors.RED)
        typer.echo("This could be due to:")
        typer.echo("  - No internet connection")
        typer.echo("  - License has expired or been revoked")
        typer.echo("  - Server maintenance")
        typer.echo("\nTry again later or contact support@terraback.io")
        raise typer.Exit(code=1)


@app.command("doctor")
def license_doctor():
    """Run comprehensive license diagnostics."""
    from terraback.core.license import (
        get_license_path,
        get_metadata_path,
        get_validation_path,
        _is_online,
        _get_machine_fingerprint,
        get_validation_info,
    )
    typer.echo("Running license diagnostics...\n")
    typer.echo("License Files:")
    license_path = get_license_path()
    metadata_path = get_metadata_path()
    validation_path = get_validation_path()
    files_status = [
        (license_path, "license.jwt"),
        (metadata_path, "license_metadata.json"),
        (validation_path, "license_validation.enc"),
    ]
    for path, name in files_status:
        if path.exists():
            size = path.stat().st_size
            typer.echo(f"  Found {name} ({size} bytes)")
        else:
            typer.echo(f"  Missing {name}")
    typer.echo("\nConnectivity:")
    is_online = _is_online()
    if is_online:
        typer.echo("  Internet connection available")
    else:
        typer.echo("  No internet connection")
    typer.echo("\nLicense Status:")
    license_data = get_active_license()
    if license_data:
        typer.echo("  Valid license found")
        typer.echo(f"  - Tier: {license_data.get('tier', 'unknown')}")
        typer.echo(f"  - Expires: {license_data.get('expiry', 'unknown')}")
    else:
        typer.echo("  No valid license")
    typer.echo("\nValidation Status:")
    validation_info = get_validation_info()
    if "days_since_online" in validation_info:
        days = validation_info["days_since_online"]
        typer.echo(f"  - Days since last validation: {days}")
        typer.echo(f"  - Validation count: {validation_info.get('validation_count', 0)}")
        if validation_info.get("validation_status") == "valid":
            typer.echo("  Validation status: Valid")
        else:
            typer.echo("  Validation status: Expired")
    else:
        typer.echo("  No validation data found")
    typer.echo("\nSecurity:")
    fingerprint = _get_machine_fingerprint()
    typer.echo(f"  - Machine fingerprint: {fingerprint[:12]}...")
    typer.echo("\nRecommendations:")
    if not license_data:
        typer.echo("  - Activate a license with: terraback license activate <key>")
    elif validation_info.get("needs_validation") and is_online:
        typer.echo("  - Refresh validation with: terraback license refresh")
    elif validation_info.get("needs_validation") and not is_online:
        typer.echo("  - Connect to internet and run: terraback license refresh")
    elif validation_info.get("in_grace_period"):
        typer.echo("  - Connect to internet soon to avoid service interruption")
    else:
        typer.echo("  - License system is working correctly")
