"""Simple template renderer for Terraform files.

Uses the main AutoDiscoveryTemplateLoader for consistent template resolution
across all scanning methods.
"""
from pathlib import Path
from typing import List, Dict, Any

from terraback.utils.logging import get_logger

logger = get_logger(__name__)


class SimpleRenderer:
    """Simple template renderer using the main template loader.

    This ensures consistent template discovery regardless of subdirectory structure.
    """

    def __init__(self, output_dir: Path = None):
        """Initialize with output directory for version detection."""
        from terraback.terraform_generator.writer import get_template_loader
        self.loader = get_template_loader(output_dir=output_dir)
        self.output_dir = output_dir

    def render_resources(self, resources: List[Dict[str, Any]], resource_type: str, output_dir: Path) -> Path:
        """Render resources to a Terraform file using the main template loader."""
        if not resources:
            return None

        # Deduplicate names
        self._deduplicate_names(resources)

        # Use the main template loader for rendering
        try:
            output = self.loader.render_template(resource_type, resources, provider='aws')
        except FileNotFoundError as e:
            logger.warning(f"No template found for {resource_type}: {e}")
            return None

        if not output.strip():
            logger.warning(f"Empty output for {resource_type}")
            return None

        # Write file (strip provider prefix for filename)
        filename = resource_type
        if filename.startswith('aws_'):
            filename = filename[4:]
        output_file = output_dir / f"{filename}.tf"
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(output)
        logger.info(f"Wrote {len(resources)} {resource_type} resources to {output_file}")

        return output_file

    def _deduplicate_names(self, resources: List[Dict[str, Any]]):
        """Ensure unique resource names."""
        seen = {}

        for resource in resources:
            name = resource.get('name_sanitized', 'unnamed')

            if name in seen:
                seen[name] += 1
                resource['name_sanitized'] = f"{name}_{seen[name]}"
            else:
                seen[name] = 1


def render_all(results: Dict[str, List[Dict]], template_dir: Path, output_dir: Path):
    """Render all scan results to Terraform files.

    Args:
        results: Dict mapping resource keys to lists of resource dicts
        template_dir: Ignored (kept for backward compatibility)
        output_dir: Directory to write Terraform files to
    """
    renderer = SimpleRenderer(output_dir=output_dir)

    for resource_type, resources in results.items():
        if resources:
            # Extract terraform type from first resource
            tf_type = resources[0].get('terraform_type', resource_type)
            renderer.render_resources(resources, tf_type, output_dir)