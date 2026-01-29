# terraback/terraform_generator/validator.py
"""Template validation utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from jinja2 import Environment

from .writer import AutoDiscoveryTemplateLoader


class TemplateValidator:
    """Run validation rules on Jinja templates."""

    def __init__(self, templates_dir: Optional[Path] = None) -> None:
        self.templates_dir = Path(templates_dir or Path(__file__).resolve().parent.parent / "templates")
        self.loader = AutoDiscoveryTemplateLoader(template_dir_override=self.templates_dir)
        self.env: Environment = self.loader.env
        self._checks: List[Callable[[Path, str], List[str]]] = []

    # ------------------------------------------------------------------
    # Check registration
    # ------------------------------------------------------------------
    def add_check(self, func: Callable[[Path, str], List[str]]) -> None:
        """Register a custom validation check."""
        self._checks.append(func)

    # ------------------------------------------------------------------
    # Core validation
    # ------------------------------------------------------------------
    def _validate_file(self, file_path: Path) -> List[str]:
        """Validate a single template file and return a list of issues."""
        issues: List[str] = []
        try:
            source = file_path.read_text()
        except Exception as exc:  # pragma: no cover - unlikely read errors in tests
            return [f"Failed to read {file_path}: {exc}"]

        # Jinja syntax validation
        try:
            self.env.parse(source)
        except Exception as exc:
            issues.append(f"Jinja syntax error: {exc}")

        # Run custom checks
        for check in self._checks:
            try:
                result = check(file_path, source)
                if result:
                    issues.extend(result)
            except Exception as exc:  # pragma: no cover - custom check failure
                issues.append(f"Check {check.__name__} failed: {exc}")
        return issues

    def _iter_template_files(self) -> Iterable[Path]:
        """Yield all template files recursively under ``templates_dir``."""
        return self.templates_dir.rglob("*.tf.j2")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def run_template_tests(self) -> Dict[str, List[str]]:
        """Run validation on all templates and return issues by template."""
        results: Dict[str, List[str]] = {}
        for template_file in self._iter_template_files():
            issues = self._validate_file(template_file)
            if issues:
                rel = str(template_file.relative_to(self.templates_dir))
                results[rel] = issues
        return results

