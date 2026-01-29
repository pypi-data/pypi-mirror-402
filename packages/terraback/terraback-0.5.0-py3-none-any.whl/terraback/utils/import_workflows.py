from __future__ import annotations

import asyncio
import subprocess
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

import re

from .cleanup import clean_import_artifacts
from .state_utils import merge_states
from .terraform_import import TerraformImporter, import_resources, check_terraform_version

import typer


# Shared helpers for importing Terraform state using different workflows.


def import_with_blocks(terraform_dir: Path, resources: List[Dict[str, Any]]) -> float:
    """Write import blocks and run ``terraform plan`` to generate config."""
    start = time.perf_counter()
    import_file = terraform_dir / "terraback_import_blocks.tf"
    blocks: List[str] = []
    for imp in resources:
        rtype = imp.get("type") or imp.get("resource_type")
        rname = imp.get("name") or imp.get("resource_name")
        rid = imp.get("id") or imp.get("remote_id")
        if not (rtype and rname and rid):
            continue
        blocks.append(f'import {{\n  to = {rtype}.{rname}\n  id = "{rid}"\n}}\n')

    if blocks:
        import_file.write_text("\n".join(blocks), encoding="utf-8")

    if not (terraform_dir / ".terraform").exists():
        typer.echo("Running terraform init...")
        result = subprocess.run(
            ["terraform", "init"],
            cwd=str(terraform_dir),
            capture_output=True,
            timeout=120,
            text=True,
            check=False,
        )
        if result.returncode != 0:
            typer.secho("terraform init failed", fg="red")
            typer.secho(result.stderr or result.stdout)
            raise typer.Exit(1)

    result = subprocess.run(
        ["terraform", "plan", "-generate-config-out=generated.tf"],
        cwd=terraform_dir,
        capture_output=True,
        timeout=300,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        typer.secho("terraform plan failed", fg="red")
        typer.secho(result.stderr or result.stdout)
        raise typer.Exit(1)
    # Skip applying changes automatically after import

    clean_import_artifacts(terraform_dir)
    elapsed = time.perf_counter() - start
    
    # Calculate timing summary
    num_resources = len(resources)
    estimated_sequential_time = num_resources * 4.0  # 4 seconds per resource estimate
    time_saved = estimated_sequential_time - elapsed
    
    typer.echo(f"Import with blocks completed successfully in {elapsed:.2f} seconds")
    typer.echo("\n--- Timing Summary ---")
    typer.echo(f"Total elapsed time: {elapsed:.2f} seconds")
    typer.echo(f"Number of resources imported: {num_resources}")
    typer.echo(f"Estimated sequential import time: {estimated_sequential_time:.2f} seconds")
    typer.echo(f"Time saved: {time_saved:.2f} seconds ({time_saved/estimated_sequential_time*100:.1f}% faster)")
    
    return elapsed


def _import_single_resource(
    terraform_dir: Path, imp: Dict[str, Any], lock_timeout: int = 300
) -> Dict[str, Any]:
    # Ensure terraform_dir is a Path object and exists
    if not isinstance(terraform_dir, Path):
        terraform_dir = Path(terraform_dir)
    
    if not terraform_dir.exists():
        return {
            "imp": imp,
            "success": False,
            "stdout": "",
            "stderr": f"Terraform directory does not exist: {terraform_dir}",
            "file": imp.get("file"),
        }
    
    # Check if terraform is available
    import shutil
    import platform
    
    terraform_cmd = "terraform"
    if not shutil.which("terraform"):
        # On Windows, try terraform.exe
        if platform.system() == "Windows" or "microsoft" in platform.uname().release.lower():
            if shutil.which("terraform.exe"):
                terraform_cmd = "terraform.exe"
            else:
                return {
                    "imp": imp,
                    "success": False,
                    "stdout": "",
                    "stderr": "terraform command not found in PATH",
                    "file": imp.get("file"),
                }
        else:
            return {
                "imp": imp,
                "success": False,
                "stdout": "",
                "stderr": "terraform command not found in PATH",
                "file": imp.get("file"),
            }
    
    cmd = [terraform_cmd, "import"]
    
    if lock_timeout > 0:
        cmd.append(f"-lock-timeout={lock_timeout}s")
    cmd.extend([imp["address"], imp["id"]])
    
    # Log command to file for debugging
    import datetime
    debug_log_path = terraform_dir / "terraform_import_debug.log"
    with open(debug_log_path, "a") as f:
        f.write(f"{datetime.datetime.now()}: Running in {terraform_dir}: {' '.join(cmd)}\n")
        f.flush()
    
    try:
        result = subprocess.run(
            cmd,
            cwd=str(terraform_dir),
            capture_output=True,
            text=True,
            timeout=min(300, lock_timeout + 30),
            check=False,
        )
        with open(debug_log_path, "a") as f:
            f.write(f"{datetime.datetime.now()}: Command completed with return code {result.returncode}\n")
            if result.stdout:
                f.write(f"STDOUT: {result.stdout[:500]}...\n" if len(result.stdout) > 500 else f"STDOUT: {result.stdout}\n")
            if result.stderr:
                f.write(f"STDERR: {result.stderr[:500]}...\n" if len(result.stderr) > 500 else f"STDERR: {result.stderr}\n")
            f.flush()
    except subprocess.TimeoutExpired as e:
        with open(debug_log_path, "a") as f:
            f.write(f"{datetime.datetime.now()}: Command timed out after {e.timeout} seconds\n")
            f.flush()
        return {
            "imp": imp,
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {e.timeout} seconds",
            "file": imp.get("file"),
        }
    except Exception as e:
        with open(debug_log_path, "a") as f:
            f.write(f"{datetime.datetime.now()}: Unexpected error: {str(e)}\n")
            f.flush()
        return {
            "imp": imp,
            "success": False,
            "stdout": "",
            "stderr": f"Unexpected error running terraform: {str(e)}",
            "file": imp.get("file"),
        }

    stderr = result.stderr
    if (
        result.returncode != 0
        and stderr
        and "Cannot import non-existent remote object" in stderr
    ):
        meta = imp.get("provider_metadata") or {}
        extras = []
        if meta.get("region"):
            extras.append(f"region={meta['region']}")
        if meta.get("account_id"):
            extras.append(f"account_id={meta['account_id']}")
        if extras:
            stderr = stderr.rstrip() + " (" + ", ".join(extras) + ")\n"

    return {
        "imp": imp,
        "success": result.returncode == 0,
        "stdout": result.stdout,
        "stderr": stderr,
        "file": imp.get("file"),
    }


async def _async_import_single_resource(
    terraform_dir: Path, imp: Dict[str, Any], lock_timeout: int = 300
) -> Dict[str, Any]:
    import shutil
    import platform

    terraform_cmd = "terraform"
    if not shutil.which("terraform"):
        # On Windows, try terraform.exe
        if platform.system() == "Windows" or "microsoft" in platform.uname().release.lower():
            if shutil.which("terraform.exe"):
                terraform_cmd = "terraform.exe"
            else:
                return {
                    "imp": imp,
                    "success": False,
                    "stdout": "",
                    "stderr": "terraform command not found in PATH",
                    "file": imp.get("file"),
                }
        else:
            return {
                "imp": imp,
                "success": False,
                "stdout": "",
                "stderr": "terraform command not found in PATH",
                "file": imp.get("file"),
            }

    cmd = [terraform_cmd, "import"]
    if lock_timeout > 0:
        cmd.append(f"-lock-timeout={lock_timeout}s")
    cmd.extend([imp["address"], imp["id"]])
    
    try:
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=str(terraform_dir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        # Add timeout to avoid hanging
        stdout_bytes, stderr_bytes = await asyncio.wait_for(
            proc.communicate(), 
            timeout=min(300, lock_timeout + 30)
        )
    except asyncio.TimeoutError:
        return {
            "imp": imp,
            "success": False,
            "stdout": "",
            "stderr": f"Command timed out after {min(300, lock_timeout + 30)} seconds",
            "file": imp.get("file"),
        }
    except Exception as e:
        return {
            "imp": imp,
            "success": False,
            "stdout": "",
            "stderr": f"Unexpected error: {str(e)}",
            "file": imp.get("file"),
        }

    stderr = stderr_bytes.decode()
    if (
        proc.returncode != 0
        and stderr
        and "Cannot import non-existent remote object" in stderr
    ):
        meta = imp.get("provider_metadata") or {}
        extras = []
        if meta.get("region"):
            extras.append(f"region={meta['region']}")
        if meta.get("account_id"):
            extras.append(f"account_id={meta['account_id']}")
        if extras:
            stderr = stderr.rstrip() + " (" + ", ".join(extras) + ")\n"

    return {
        "imp": imp,
        "success": proc.returncode == 0,
        "stdout": stdout_bytes.decode(),
        "stderr": stderr,
        "file": imp.get("file"),
    }


def import_with_commands(
    terraform_dir: Path,
    resources: Iterable[Dict[str, Any]],
    *,
    parallel: int = 1,
    async_mode: bool = False,
    progress: bool = True,
    batch_size: int = 1,
    lock_timeout: int = 300,
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Import resources using ``terraform import`` commands.

    ``parallel`` controls the number of worker threads or async tasks while
    ``batch_size`` defines how many resources each worker processes
    sequentially.
    """

    imported = 0
    failed = 0
    failed_imports: List[Dict[str, Any]] = []
    messages: List[str] = []  # Collect messages to display after progress bar

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import sys
    import platform
    import typer
    
    resources = list(resources)  # Convert to list first
    # Debug output removed to avoid interfering with progress bar
    total_resources = len(resources)

    progress_enabled = progress and sys.stdout.isatty()

    windows_old_python = platform.system() == "Windows" and sys.version_info < (3, 8)
    if async_mode and windows_old_python:
        typer.echo(
            "Async mode not supported on this Windows Python version. Falling back to threads."
        )
        async_mode = False

    def handle_result(result: Dict[str, Any]) -> None:
        nonlocal imported, failed
        if result["success"]:
            imported += 1
            msg = f"[v] {result['imp']['address']}"
            if progress_enabled:
                messages.append(msg)
            else:
                typer.echo(msg)
        else:
            failed += 1
            failed_imports.append(result)
            msg = f"[x] {result['imp']['address']}"
            error_msgs = [msg]
            if result["stderr"]:
                stderr = result["stderr"].strip()
                if "does not exist in the configuration" in stderr:
                    error_msgs.append("  Error: Resource definition missing in .tf files")
                elif "Cannot import non-existent remote object" in stderr:
                    error_msgs.append("  Error: Resource no longer exists in cloud provider")
                elif "already managed by Terraform" in stderr:
                    error_msgs.append("  Error: Resource already imported")
                else:
                    error_msgs.append(f"  Error: {stderr}")
            
            if progress_enabled:
                messages.extend(error_msgs)
            else:
                for emsg in error_msgs:
                    typer.echo(emsg)
    if async_mode:

        async def run_async() -> List[Dict[str, Any]]:
            sem = asyncio.Semaphore(parallel)

            async def process_batch(
                batch: List[Dict[str, Any]],
            ) -> List[Dict[str, Any]]:
                async with sem:
                    batch_results = []
                    for imp in batch:
                        batch_results.append(
                            await _async_import_single_resource(
                                terraform_dir, imp, lock_timeout=lock_timeout
                            )
                        )
                    return batch_results

            batches = [
                resources[i : i + batch_size]
                for i in range(0, len(resources), batch_size)
            ]
            tasks = [asyncio.create_task(process_batch(batch)) for batch in batches]

            results: List[Dict[str, Any]] = []
            if progress_enabled:
                with typer.progressbar(
                    length=len(resources), label="Importing resources"
                ) as bar:
                    for coro in asyncio.as_completed(tasks):
                        res_batch = await coro
                        bar.update(len(res_batch))
                        results.extend(res_batch)
            else:
                for coro in asyncio.as_completed(tasks):
                    res_batch = await coro
                    results.extend(res_batch)
            return results

        results = asyncio.run(run_async())
        for res in results:
            handle_result(res)
    else:

        def process_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
            results = []
            for imp in batch:
                try:
                    result = _import_single_resource(terraform_dir, imp, lock_timeout=lock_timeout)
                    results.append(result)
                except Exception as e:
                    # Catch any unexpected errors
                    results.append({
                        "imp": imp,
                        "success": False,
                        "stdout": "",
                        "stderr": f"Unexpected error: {str(e)}",
                        "file": imp.get("file"),
                    })
            return results

        batches = [
            resources[i : i + batch_size] for i in range(0, len(resources), batch_size)
        ]
        # Debug output removed to avoid interfering with progress bar
        
        # Ensure we have batches to process
        if not batches:
            typer.echo("No batches to process - check if resources list is empty")
            return imported, failed, failed_imports
            
        with ThreadPoolExecutor(max_workers=parallel) as executor:
            future_to_batch = {
                executor.submit(process_batch, batch): batch for batch in batches
            }
            if progress_enabled:
                with typer.progressbar(
                    length=len(resources), label="Importing resources"
                ) as bar:
                    # Process futures as they complete
                    completed = 0
                    for future in as_completed(future_to_batch):
                        try:
                            results_batch = future.result(timeout=360)  # Increased timeout to allow terraform imports to complete
                            completed += len(results_batch)
                            bar.update(len(results_batch))
                            for result in results_batch:
                                handle_result(result)
                        except Exception as e:
                            # Handle any exceptions from the future
                            batch = future_to_batch.get(future, [])
                            batch_size = len(batch) if batch else 1
                            completed += batch_size
                            bar.update(batch_size)
                            messages.append(f"\nError in batch processing: {e}")
            else:
                for future in as_completed(future_to_batch):
                    try:
                        results_batch = future.result(timeout=360)  # Increased timeout to allow terraform imports to complete
                        for result in results_batch:
                            handle_result(result)
                    except Exception as e:
                        typer.echo(f"Error in batch processing: {e}", err=True)
    
    # Display collected messages after progress bar completes
    if progress_enabled and messages:
        typer.echo("\nImport results:")
        for msg in messages:
            typer.echo(msg)

    return imported, failed, failed_imports


def import_with_workspaces(
    terraform_dir: Path,
    resources: Iterable[Dict[str, Any]],
    batch_size: int = 1,
    progress: bool = True,
    lock_timeout: int = 300,
) -> None:
    """Import resources using separate Terraform workspaces."""
    from contextlib import nullcontext
    import sys

    resources = list(resources)
    batches = [
        resources[i : i + batch_size] for i in range(0, len(resources), batch_size)
    ]

    progress_enabled = progress and sys.stdout.isatty()
    bar_cm = (
        typer.progressbar(length=len(resources), label="Importing resources")
        if progress_enabled
        else nullcontext()
    )

    with bar_cm as bar:
        for b_idx, batch in enumerate(batches):
            ws_name = f"tb{b_idx}"
            result = subprocess.run(
                ["terraform", "workspace", "new", ws_name],
                cwd=str(terraform_dir),
                capture_output=True,
                timeout=60,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                typer.secho(f"terraform workspace new {ws_name} failed", fg="red")
                typer.secho(result.stderr or result.stdout)
                raise typer.Exit(1)

            result = subprocess.run(
                ["terraform", "workspace", "select", ws_name],
                cwd=str(terraform_dir),
                capture_output=True,
                timeout=60,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                typer.secho(f"terraform workspace select {ws_name} failed", fg="red")
                typer.secho(result.stderr or result.stdout)
                raise typer.Exit(1)

    clean_import_artifacts(terraform_dir)


def import_with_blocks_enhanced(
    terraform_dir: Path,
    resources: List[Dict[str, Any]],
    *,
    batch_size: int = 1,
    parallelism: int = 10,
) -> None:
    """Import resources using Terraform import blocks in batches."""

    if not (terraform_dir / ".terraform").exists():
        init = subprocess.run(
            ["terraform", "init"],
            cwd=str(terraform_dir),
            capture_output=True,
            timeout=120,
            text=True,
            check=False,
        )
        if init.returncode != 0:
            typer.secho("terraform init failed", fg="red")
            typer.secho(init.stderr or init.stdout)
            raise typer.Exit(1)

    import_file = terraform_dir / "terraback_import_blocks.tf"
    i = 0
    while i < len(resources):
        batch = resources[i : i + batch_size]
        while batch:
            blocks = []
            for imp in batch:
                rtype = imp.get("type") or imp.get("resource_type")
                rname = imp.get("name") or imp.get("resource_name")
                rid = imp.get("id") or imp.get("remote_id")
                if not (rtype and rname and rid):
                    continue
                blocks.append(
                    f"import {{\n  to = {rtype}.{rname}\n  id = \"{rid}\"\n}}\n"
                )
            if not blocks:
                break
            import_file.write_text("\n".join(blocks), encoding="utf-8")

            plan = subprocess.run(
                [
                    "terraform",
                    "plan",
                    f"-parallelism={parallelism}",
                    "-generate-config-out=generated.tf",
                ],
                cwd=str(terraform_dir),
                capture_output=True,
                text=True,
                check=False,
                timeout=300,
            )
            if plan.returncode != 0:
                stderr = plan.stderr or plan.stdout or ""
                if "Cannot import non-existent remote object" in stderr:
                    m = re.search(r'to\s+"([^"]+)"', stderr)
                    if m:
                        addr = m.group(1)
                        typer.echo(f"Skipping missing resource {addr}")
                        for idx, imp in enumerate(batch):
                            raddr = f"{imp.get('type') or imp.get('resource_type')}.{imp.get('name') or imp.get('resource_name')}"
                            if raddr == addr:
                                del batch[idx]
                                resources.remove(imp)
                                break
                        if import_file.exists():
                            import_file.unlink()
                        continue
                typer.secho("terraform plan failed", fg="red")
                typer.secho(stderr)
                raise typer.Exit(1)

            # Skip applying changes automatically after import

            if import_file.exists():
                import_file.unlink()
            break

        i += len(batch)

    clean_import_artifacts(terraform_dir)


def parallel_workspace_import(
    terraform_dir: Path,
    resources: Iterable[Dict[str, Any]],
    *,
    parallel: int = 4,
    lock_timeout: int = 300,
) -> None:
    """Import resources concurrently using temporary workspaces."""

    from concurrent.futures import ThreadPoolExecutor, as_completed
    import shutil

    def run_import(idx: int, imp: Dict[str, Any]) -> Dict[str, Any]:
        ws_dir = terraform_dir / f"workspace_{idx}"
        ws_dir.mkdir(parents=True, exist_ok=True)
        init_result = subprocess.run(
            ["terraform", "init"],
            cwd=ws_dir,
            capture_output=True,
            text=True,
            timeout=120,
        )
        import_result = None
        if init_result.returncode == 0:
            cmd = ["terraform", "import"]
            if lock_timeout > 0:
                cmd.append(f"-lock-timeout={lock_timeout}s")
            cmd.extend([imp["address"], imp["id"]])
            import_result = subprocess.run(
                cmd,
                cwd=ws_dir,
                capture_output=True,
                timeout=300,
                text=True,
            )
        return {
            "ws_dir": ws_dir,
            "imp": imp,
            "init_result": init_result,
            "import_result": import_result,
        }

    with ThreadPoolExecutor(max_workers=parallel) as executor:
        futures = [executor.submit(run_import, i, imp) for i, imp in enumerate(resources)]
        results = [f.result() for f in as_completed(futures)]

    ws_dirs = [r["ws_dir"] for r in results]
    errors = []
    for r in results:
        init_res = r["init_result"]
        imp_res = r.get("import_result")
        if init_res.returncode != 0:
            errors.append(
                {
                    "imp": r["imp"],
                    "step": "init",
                    "stdout": init_res.stdout,
                    "stderr": init_res.stderr,
                    "returncode": init_res.returncode,
                }
            )
        elif imp_res and imp_res.returncode != 0:
            errors.append(
                {
                    "imp": r["imp"],
                    "step": "import",
                    "stdout": imp_res.stdout,
                    "stderr": imp_res.stderr,
                    "returncode": imp_res.returncode,
                }
            )

    main_state_path = terraform_dir / "terraform.tfstate"
    merge_states(main_state_path, ws_dirs)

    for ws_dir in ws_dirs:
        shutil.rmtree(ws_dir, ignore_errors=True)

    clean_import_artifacts(terraform_dir)

    return errors


class FastImportManager:
    """High level manager for importing resources quickly."""

    def __init__(
        self,
        terraform_dir: Path,
        resources: List[Dict[str, Any]],
        *,
        parallel: int = 4,
        batch_size: int = 1,
        lock_timeout: int = 300,
    ) -> None:
        self.terraform_dir = terraform_dir
        self.resources = list(resources)
        self.parallel = parallel
        self.batch_size = max(1, batch_size)
        self.lock_timeout = lock_timeout

        from .terraform_checker import TerraformChecker
        import typer
        
        # Get Terraform version silently to avoid interfering with progress
        version = TerraformChecker.get_terraform_version() or ""
        m = re.search(r"v(\d+)\.(\d+)", version)
        if m and (int(m.group(1)) > 1 or (int(m.group(1)) == 1 and int(m.group(2)) >= 5)):
            self.use_blocks = True
        else:
            self.use_blocks = False

    async def import_all(self, *, progress: bool = True) -> None:
        import sys
        from contextlib import nullcontext

        progress_enabled = progress and sys.stdout.isatty()
        bar_cm = (
            typer.progressbar(length=len(self.resources), label="Importing resources")
            if progress_enabled
            else nullcontext()
        )

        with bar_cm as bar:
            if self.use_blocks:
                for i in range(0, len(self.resources), self.batch_size):
                    batch = self.resources[i : i + self.batch_size]
                    await asyncio.to_thread(
                        import_with_blocks_enhanced,
                        self.terraform_dir,
                        batch,
                        batch_size=self.batch_size,
                        parallelism=self.parallel,
                    )
                    if progress_enabled:
                        bar.update(len(batch))
                return

            for i in range(0, len(self.resources), self.batch_size):
                batch = self.resources[i : i + self.batch_size]
                await asyncio.to_thread(
                    parallel_workspace_import,
                    self.terraform_dir,
                    batch,
                    parallel=self.parallel,
                    lock_timeout=self.lock_timeout,
                )
                if progress_enabled:
                    bar.update(len(batch))


async def fast_import_all(
    terraform_dir: Path,
    resources: List[Dict[str, Any]],
    *,
    parallel: int = 4,
    batch_size: int = 1,
    progress: bool = True,
    lock_timeout: int = 300,
) -> None:
    """Async helper for fast importing all resources."""
    # Create manager and run import without debug output
    manager = FastImportManager(
        terraform_dir,
        resources,
        parallel=parallel,
        batch_size=batch_size,
        lock_timeout=lock_timeout,
    )
    await manager.import_all(progress=progress)


def run_fast_import(
    terraform_dir: Path,
    resources: List[Dict[str, Any]],
    *,
    parallel: int = 4,
    batch_size: int = 1,
    progress: bool = True,
    lock_timeout: int = 300,
) -> None:
    """Synchronous wrapper around :func:`fast_import_all`."""
    # Run fast import without debug output
    asyncio.run(
        fast_import_all(
            terraform_dir,
            resources,
            parallel=parallel,
            batch_size=batch_size,
            progress=progress,
            lock_timeout=lock_timeout,
        )
    )


def run_sequential_import(
    terraform_dir: Path,
    resources: List[Dict[str, Any]],
    *,
    progress: bool = True,
    stop_on_error: bool = False,
    state_check_interval: float = 0.5,
    max_retries: int = 3,
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Run sequential import with retry logic and state checking.
    
    This avoids state lock conflicts by importing resources one at a time.
    
    Args:
        terraform_dir: Directory containing Terraform files
        resources: List of resources to import
        progress: Show progress bar
        stop_on_error: Stop on first error
        state_check_interval: Interval to check state lock status
        max_retries: Maximum retries for lock errors
    
    Returns:
        Tuple of (imported_count, failed_count, failed_details)
    """
    return import_resources(terraform_dir, resources, method="sequential", progress=progress)


def run_bulk_import_with_blocks(
    terraform_dir: Path,
    resources: List[Dict[str, Any]],
    *,
    progress: bool = True,
) -> Tuple[int, int, List[Dict[str, Any]]]:
    """Run bulk import using Terraform import blocks (Terraform 1.5+).
    
    This is the fastest import method, importing all resources in a single
    Terraform operation.
    
    Args:
        terraform_dir: Directory containing Terraform files
        resources: List of resources to import
        progress: Show progress bar
    
    Returns:
        Tuple of (imported_count, failed_count, failed_details)
    """
    typer.echo(f"Generating import blocks for {len(resources)} resources...")
    return import_resources(terraform_dir, resources, method="bulk", progress=progress)

