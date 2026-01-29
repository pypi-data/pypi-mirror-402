# terraback/terraform_generator/writer.py

import json
import os
from pathlib import Path
from jinja2 import Environment, FileSystemLoader
from functools import lru_cache
import re
import time
from jinja2.exceptions import TemplateNotFound
import importlib.resources
from typing import Optional, List, Any, Dict
from terraback.utils.cross_scan_registry import get_item_dependencies, get_all_items
from terraback.terraform_generator.imports import normalize_terraform_resource_type
from terraback.utils.logging import get_logger

logger = get_logger(__name__)

# Import all filters from the updated filters module
from .filters import (
    ALL_FILTERS,
    has_value,
    validate_arn,
    validate_cidr,
    terraform_bool,
    safe_int,
    terraform_name,
    generate_resource_name,
    escape_quotes,
    strip_empty_lines
)

# Precompiled regular expressions for faster validation
EMPTY_ASSIGNMENT_RE = re.compile(r"^\s*\w+\s*=\s*$")
EMPTY_RESOURCE_NAME_RE = re.compile(r"(resource\s+\"[^\"]+\"\s+)\"\"")
PYTHON_BOOL_RE = re.compile(r"\b(True|False)\b")
MISSING_QUOTES_RE = re.compile(r"=\s*([a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*\.[a-zA-Z_][a-zA-Z0-9_]*)")
EXCESSIVE_EMPTY_LINES_RE = re.compile(r"\n\s*\n\s*\n+")

def _make_joiner(separator):
    """Create a joiner function for comma-separated lists in templates."""
    class Joiner:
        def __init__(self, sep):
            self.sep = sep
            self.first = True
        
        def __call__(self):
            if self.first:
                self.first = False
                return ""
            return self.sep
    
    return Joiner(separator)


def format_alias_target(alias_target: dict) -> str:
    """Return a formatted alias block for a Route53 record."""
    if not alias_target or not isinstance(alias_target, dict):
        return ""

    name = alias_target.get("DNSName")
    zone_id = alias_target.get("HostedZoneId")
    eval_th = alias_target.get("EvaluateTargetHealth")

    lines = ["alias {"]
    if name:
        lines.append(f"  name                   = \"{name}\"")
    if zone_id:
        lines.append(f"  zone_id                = \"{zone_id}\"")
    if eval_th is not None:
        lines.append(
            f"  evaluate_target_health = {terraform_bool(eval_th)}"
        )
    lines.append("}")
    return "\n".join(lines)


class TemplateMetrics:
    """Collect rendering duration and count statistics for templates."""

    def __init__(self) -> None:
        self.render_counts: dict[str, int] = {}
        self.render_durations: dict[str, float] = {}

    def record(self, template: str, duration: float) -> None:
        self.render_counts[template] = self.render_counts.get(template, 0) + 1
        self.render_durations[template] = self.render_durations.get(template, 0.0) + duration

    def summary(self) -> str:
        lines = ["Template Performance Summary:"]
        for name in sorted(self.render_counts):
            count = self.render_counts[name]
            total = self.render_durations.get(name, 0.0)
            lines.append(f"- {name}: {count} render(s) in {total:.3f}s")
        total_renders = sum(self.render_counts.values())
        total_time = sum(self.render_durations.values())
        lines.append(f"Total: {total_renders} render(s) in {total_time:.3f}s")
        return "\n".join(lines)

    def print_summary(self) -> None:
        print(self.summary())


_template_metrics: Optional[TemplateMetrics] = None


def enable_template_metrics() -> TemplateMetrics:
    """Create and enable metrics collection for template rendering."""
    global _template_metrics
    if _template_metrics is None:
        _template_metrics = TemplateMetrics()
    return _template_metrics


def get_template_metrics() -> Optional[TemplateMetrics]:
    """Return the active metrics collector if enabled."""
    return _template_metrics


def print_metrics_summary() -> None:
    """Print a summary of collected template rendering metrics."""
    if _template_metrics is not None:
        _template_metrics.print_summary()

class AutoDiscoveryTemplateLoader:
    """
    Automatically discovers and loads Jinja2 templates from the package's
    'templates' directory. Enhanced with better error handling and template validation.
    """
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AutoDiscoveryTemplateLoader, cls).__new__(cls)
            cls._instance.initialized = False
        return cls._instance

    def __init__(self, template_dir_override: Optional[Path] = None, output_dir: Optional[Path] = None):
        if self.initialized:
            # Update output directory if provided
            if output_dir:
                self.output_dir = output_dir
                self.update_version_filters(output_dir)
            return
        
        self.template_dir = template_dir_override or self._find_main_templates_dir()
        self.output_dir = output_dir or Path.cwd()

        if not self.template_dir or not self.template_dir.exists():
            raise FileNotFoundError(f"Could not find the 'templates' directory. Looked for: {self.template_dir}")

        self.env = Environment(
            loader=FileSystemLoader(self.template_dir),
            trim_blocks=False,
            lstrip_blocks=False,
        )
        # Cache compiled templates keyed by provider/resource type
        self.compiled_template_cache: dict[str, Any] = {}
        self.register_custom_filters()
        self.register_custom_tests()
        self.register_global_functions()
        self.initialized = True

    def _find_main_templates_dir(self) -> Path:
        """Reliably find the 'templates' directory within the installed terraback package."""
        try:
            return Path(str(importlib.resources.files('terraback').joinpath('templates')))
        except (ModuleNotFoundError, AttributeError):
            return Path(__file__).resolve().parent.parent / "templates"

    def register_custom_filters(self):
        """Register all custom Jinja2 filters using the enhanced filter system."""
        # Register all filters from the centralized dictionary
        for filter_name, filter_func in ALL_FILTERS.items():
            self.env.filters[filter_name] = filter_func
        
        # Additional template-specific filters
        self.env.filters['joiner'] = lambda sep=',': _make_joiner(sep)
        
        # Ensure backward compatibility with any existing filter names
        self.env.filters['tf_resource_name'] = ALL_FILTERS['tf_resource_name']
        self.env.filters['strip_id_prefix'] = ALL_FILTERS['strip_id_prefix']
        self.env.filters['terraform_sanitize_name'] = ALL_FILTERS['terraform_sanitize_name']
        
        # Add common aliases for compatibility
        self.env.filters['to_json'] = ALL_FILTERS['tojson']  # Alias for templates using to_json
        
        # Add version-aware filters if available
        try:
            from terraback.terraform_generator.version_filters import create_version_aware_filters
            # Use the output directory configured for this loader
            version_filters = create_version_aware_filters(self.output_dir)
            for filter_name, filter_func in version_filters.items():
                self.env.filters[filter_name] = filter_func
        except ImportError:
            # Version filters not available, continue without them
            pass

    def update_version_filters(self, output_dir: Path):
        """Update version-aware filters based on new output directory."""
        try:
            from terraback.terraform_generator.version_filters import create_version_aware_filters
            version_filters = create_version_aware_filters(output_dir)
            for filter_name, filter_func in version_filters.items():
                self.env.filters[filter_name] = filter_func
        except ImportError:
            pass
    
    def register_custom_tests(self):
        """Register custom Jinja2 tests for better template logic."""
        self.env.tests['defined'] = lambda x: x is not None
        self.env.tests['none'] = lambda x: x is None
        self.env.tests['empty'] = lambda x: not has_value(x)
        self.env.tests['has_value'] = has_value
        self.env.tests['string'] = lambda x: isinstance(x, str)
        self.env.tests['list'] = lambda x: isinstance(x, list)
        self.env.tests['dict'] = lambda x: isinstance(x, dict)
        self.env.tests['boolean'] = lambda x: isinstance(x, bool)
        self.env.tests['number'] = lambda x: isinstance(x, (int, float))
        self.env.tests['valid_arn'] = validate_arn
        self.env.tests['valid_cidr'] = lambda x: validate_cidr(x) != "0.0.0.0/0"
        
        # Additional useful tests
        self.env.tests['aws_resource_id'] = lambda x: isinstance(x, str) and any(x.startswith(p) for p in ['i-', 'vol-', 'sg-', 'vpc-', 'subnet-'])
        self.env.tests['positive'] = lambda x: isinstance(x, (int, float)) and x > 0
        self.env.tests['valid_port'] = lambda x: isinstance(x, int) and 1 <= x <= 65535

    def register_global_functions(self):
        """Register global functions available in all templates."""
        self.env.globals['range'] = range
        self.env.globals['len'] = len
        self.env.globals['min'] = min
        self.env.globals['max'] = max
        self.env.globals['sum'] = sum
        self.env.globals['sorted'] = sorted
        self.env.globals['enumerate'] = enumerate
        self.env.globals['zip'] = zip
        
        # Custom global functions
        self.env.globals['joiner'] = lambda sep=',': _make_joiner(sep)
        
        # Template helper functions
        self.env.globals['debug_value'] = lambda x: f"DEBUG: {type(x).__name__} = {repr(x)}"
        self.env.globals['format_multiline'] = lambda text, indent=2: '\n'.join(' ' * indent + line for line in str(text).split('\n'))

    @lru_cache(maxsize=None)
    def get_template_path(self, resource_type: str, provider: str) -> str:
        """
        Recursively search the provider's template directory to find the
        correct template file, regardless of the subdirectory structure.
        Prefers standard templates, then v2 templates when available.
        Import templates are skipped to ensure resource definitions are generated.
        """
        provider_dir = self.template_dir / provider
        if not provider_dir.is_dir():
            raise FileNotFoundError(f"Provider directory not found: {provider_dir}")

        # First, try to find standard template
        template_name = f"{resource_type}.tf.j2"
        found_templates = list(provider_dir.rglob(template_name))

        # Second, try v2 template if standard not found
        if not found_templates:
            template_v2_name = f"{resource_type}_v2.tf.j2"
            found_templates = list(provider_dir.rglob(template_v2_name))
            if found_templates:
                template_name = template_v2_name

        # Third, try with provider prefix (e.g. aws_iam_policies)
        if not found_templates:
            prefixed_name = f"{provider}_{resource_type}.tf.j2"
            found_templates = list(provider_dir.rglob(prefixed_name))
            if found_templates:
                template_name = prefixed_name

        # Fourth, try with provider prefix and v2
        if not found_templates:
            prefixed_v2_name = f"{provider}_{resource_type}_v2.tf.j2"
            found_templates = list(provider_dir.rglob(prefixed_v2_name))
            if found_templates:
                template_name = prefixed_v2_name

        # If no template found, try without provider prefix (e.g. aws_)
        if not found_templates and "_" in resource_type:
            alt_resource_type = resource_type.split("_", 1)[1]
            template_name = f"{alt_resource_type}.tf.j2"
            found_templates = list(provider_dir.rglob(template_name))

            # Also try v2 for alt resource type
            if not found_templates:
                template_name = f"{alt_resource_type}_v2.tf.j2"
                found_templates = list(provider_dir.rglob(template_name))

        if not found_templates:
            raise FileNotFoundError(
                f"Template '{template_name}' not found anywhere inside '{provider_dir}'"
            )

        relative_path = found_templates[0].relative_to(self.template_dir)
        return str(relative_path).replace('\\', '/')

    def validate_template_output(self, output: str, resource_type: str) -> str:
        """Validate and clean template output to prevent syntax errors."""
        if not output.strip():
            return ""
        
        lines = output.split('\n')
        cleaned_lines = []
        
        for line in lines:
            stripped = line.strip()

            # Skip lines that would cause syntax errors
            if stripped.endswith('=') or EMPTY_ASSIGNMENT_RE.match(stripped):
                continue  # Skip empty assignments

            # Fix resource names that are empty
            if EMPTY_RESOURCE_NAME_RE.match(stripped):
                line = EMPTY_RESOURCE_NAME_RE.sub(
                    rf'\1"default_{resource_type}"',
                    line,
                )

            # Fix Python-style booleans that might have slipped through
            line = PYTHON_BOOL_RE.sub(lambda m: m.group().lower(), line)

            # Fix missing quotes around resource references
            line = MISSING_QUOTES_RE.sub(r'= \1', line)

            # Split multiple assignments on the same line
            line = re.sub(
                r'(\S[^=]*?=\s*[^=]+?)(?:\s{2,}|,\s*)([A-Za-z_][A-Za-z0-9_]*\s*=)',
                lambda m: f"{m.group(1)}\n  {m.group(2)}",
                line,
            )
            
            cleaned_lines.append(line)
        
        # Ensure proper spacing between resources
        output = '\n'.join(cleaned_lines)
        output = EXCESSIVE_EMPTY_LINES_RE.sub('\n\n', output)  # Remove excessive empty lines
        
        # Apply final cleanup
        output = strip_empty_lines(output)
        
        return output

    def preprocess_resources(self, resources: list, resource_type: str) -> list:
        """Preprocess resources to ensure they have all required fields for templates."""
        processed_resources = []
        used_names = set()
        
        for i, resource in enumerate(resources):
            if isinstance(resource, dict):
                # Create a copy to avoid modifying original data
                processed_resource = dict(resource)
                
                # For import data, flatten resource_data to root level for template compatibility
                if 'resource_data' in processed_resource and isinstance(processed_resource['resource_data'], dict):
                    # Flatten resource_data fields to root level for template access
                    resource_data = processed_resource['resource_data']
                    for key, value in resource_data.items():
                        # Only add if key doesn't already exist at root level
                        if key not in processed_resource:
                            processed_resource[key] = value
                
                # Ensure each resource has a sanitized name for Terraform
                if 'name_sanitized' not in processed_resource:
                    processed_resource['name_sanitized'] = generate_resource_name(processed_resource, resource_type)
                
                # Ensure name_sanitized is never empty
                if not processed_resource['name_sanitized'] or processed_resource['name_sanitized'] == 'unnamed_resource':
                    processed_resource['name_sanitized'] = f"{resource_type}_{i}"
                
                # Ensure name_sanitized is terraform-safe
                processed_resource['name_sanitized'] = terraform_name(processed_resource['name_sanitized'])

                # Deduplicate names per resource type
                base_name = processed_resource['name_sanitized']
                unique_name = base_name
                suffix = 2
                while unique_name in used_names:
                    unique_name = f"{base_name}_{suffix}"
                    suffix += 1
                used_names.add(unique_name)
                processed_resource['name_sanitized'] = unique_name
                
                # Add helper fields for common template patterns
                self._add_helper_fields(processed_resource, resource_type)
                
                processed_resources.append(processed_resource)
            else:
                processed_resources.append(resource)
        
        return processed_resources

    def _add_helper_fields(self, resource: dict, resource_type: str):
        """Add helper fields that templates commonly need."""
        # Add boolean helper for common AWS resource states
        if 'State' in resource:
            resource['is_active'] = resource['State'] in ['running', 'available', 'active', 'enabled']
        
        # Add formatted tags if tags exist
        if resource.get('Tags') and isinstance(resource['Tags'], list):
            resource['tags_formatted'] = {tag['Key']: tag['Value'] for tag in resource['Tags']}
        elif resource.get('tags') and isinstance(resource['tags'], dict):
            resource['tags_formatted'] = resource['tags']
        
        # Add region extraction from ARNs
        for field_name, field_value in list(resource.items()):
            if isinstance(field_value, str) and field_value.startswith('arn:aws:'):
                arn_parts = field_value.split(':')
                if len(arn_parts) >= 4:
                    resource[f'{field_name}_region'] = arn_parts[3]
                    resource[f'{field_name}_account'] = arn_parts[4] if len(arn_parts) >= 5 else ''

        # Add shorthand for common ID extractions
        for field_name, field_value in list(resource.items()):
            if isinstance(field_value, str) and any(field_value.startswith(prefix) for prefix in ['i-', 'vol-', 'sg-', 'vpc-', 'subnet-']):
                resource[f'{field_name}_short'] = terraform_name(field_value)

        # Route53 alias helper
        if resource_type == 'route53_record' and isinstance(resource.get('AliasTarget'), dict):
            resource['alias_config'] = format_alias_target(resource['AliasTarget'])

    def _extract_item_id(self, resource: dict) -> Optional[str]:
        """Attempt to extract a unique identifier from a resource dict."""
        for key in ['id', 'Id', 'resource_id', 'ResourceId']:
            if key in resource and resource[key]:
                return str(resource[key])
        for key, value in resource.items():
            if key.lower().endswith('id') and isinstance(value, str) and value:
                return str(value)
        return None

    def render_template(self, resource_type: str, resources: list, provider: str = 'aws'):
        """Render template with resources and validate output."""
        if not resources:
            return ""
        
        try:
            template_key = f"{provider}:{resource_type}"
            template = self.compiled_template_cache.get(template_key)
            if template is None:
                template_path = self.get_template_path(resource_type, provider)
                template = self.env.get_template(template_path)
                self.compiled_template_cache[template_key] = template
            
            # Preprocess resources to ensure they have valid names and helper fields
            processed_resources = self.preprocess_resources(resources, resource_type)

            # Inject dependency information if available
            for res in processed_resources:
                item_id = self._extract_item_id(res)
                if not item_id:
                    continue
                deps = get_item_dependencies(resource_type, item_id)
                if deps:
                    dep_refs = []
                    for d_type, d_id in deps:
                        tf_type = normalize_terraform_resource_type(d_type, provider)
                        dep_name = terraform_name(generate_resource_name({'id': d_id}, d_type))
                        dep_refs.append(f"{tf_type}.{dep_name}")
                    if dep_refs:
                        res['depends_on'] = dep_refs
            
            # Get cross-scan data for resource references
            all_resources = {}
            if provider == 'azure':
                # Get all Azure resource types for cross-resource references
                resource_types = [
                    'azure_storage_account', 'azure_key_vault', 'azure_mssql_server',
                    'azure_redis_cache', 'azure_application_gateway', 'azure_user_assigned_identity'
                ]
                for res_type in resource_types:
                    resources_of_type = get_all_items(res_type)
                    if resources_of_type:
                        all_resources[res_type] = resources_of_type
            
            # Render the template with enhanced context
            template_context = {
                'resources': processed_resources,
                'resource_type': resource_type,
                'provider': provider,
                'resource_count': len(processed_resources),
                'storage_accounts': all_resources.get('azure_storage_account', {}),  # Backward compatibility
                'all_resources': all_resources
            }
            
            start_time = time.perf_counter()
            output = template.render(**template_context)
            duration = time.perf_counter() - start_time
            if _template_metrics is not None:
                _template_metrics.record(resource_type, duration)
            
            # Validate and clean the output
            output = self.validate_template_output(output, resource_type)
            
            # Apply post-processing optimizations for import compatibility
            output = self._optimize_for_import(output, resource_type, provider, processed_resources)
            
            return output
            
        except Exception as e:
            print(f"Error rendering template for {resource_type}: {e}")
            raise

    def _optimize_for_import(self, output: str, resource_type: str, provider: str, resources: List = None) -> str:
        """Apply post-processing optimizations to make templates more import-friendly."""
        
        if provider == 'gcp':
            return self._optimize_gcp_for_import(output, resource_type, resources or [])
        elif provider != 'azure':
            return output
        
        # Check Terraform version to determine import strategy
        try:
            from terraback.utils.terraform_import import check_terraform_version
            supports_bulk_import, version = check_terraform_version()
        except Exception as e:
            supports_bulk_import = False
        
        # Always ensure import blocks for Azure resources to prevent "to add" issues
        # This ensures consistency regardless of Terraform version
        output = self._ensure_import_blocks(output, resource_type, resources or [])
        
        # Remove aggressive lifecycle rules that cause import conflicts
        output = re.sub(r'\s*prevent_destroy = true\s*', '', output)
        
        # Clean up empty lifecycle blocks
        output = re.sub(r'lifecycle \{\s*\}', '', output)
        
        # Add import-friendly lifecycle rules for common drift patterns
        import_optimizations = {
            'azurerm_virtual_network': [
                'ignore_changes = [subnet]'
            ],
            'azurerm_storage_account': [
                'ignore_changes = [primary_access_key, secondary_access_key]'  
            ],
            'azurerm_application_gateway': [
                'ignore_changes = [ssl_certificate]'
            ]
        }
        
        # Apply resource-specific optimizations
        for resource_pattern, optimizations in import_optimizations.items():
            if resource_pattern in resource_type:
                for optimization in optimizations:
                    # Add ignore_changes to existing lifecycle blocks
                    lifecycle_pattern = r'lifecycle \{([^}]*)\}'
                    def add_ignore_changes(match):
                        existing_content = match.group(1).strip()
                        if existing_content and not existing_content.endswith('\n'):
                            existing_content += '\n'
                        return f'lifecycle {{\n{existing_content}    {optimization}\n  }}'
                    
                    output = re.sub(lifecycle_pattern, add_ignore_changes, output)
        
        return output

    def _optimize_gcp_for_import(self, output: str, resource_type: str, resources: List = None) -> str:
        """Apply GCP-specific optimizations to make templates import-friendly."""
        
        # Import the computed field filter
        try:
            from .filters import is_gcp_computed_field
        except ImportError:
            # Fallback list if filter not available
            def is_gcp_computed_field(field):
                computed_fields = [
                    'self_link', 'url', 'creation_timestamp', 'time_created', 'updated',
                    'fingerprint', 'id', 'project', 'zone', 'region', 'etag'
                ]
                return field.lower().strip().strip('"').strip("'") in computed_fields
        
        # Pattern to find ignore_changes blocks
        ignore_changes_pattern = r'ignore_changes\s*=\s*\[([^\]]+)\]'
        
        def clean_ignore_changes(match):
            content = match.group(1)
            lines = [line.strip() for line in content.split(',')]
            
            # Filter out computed-only fields and empty/comment lines
            cleaned_lines = []
            for line in lines:
                line = line.strip()
                if not line or line.startswith('#'):
                    cleaned_lines.append(line)
                    continue
                
                # Extract field name (remove quotes and whitespace)
                field_name = line.strip().strip(',').strip('"').strip("'")
                if not is_gcp_computed_field(field_name):
                    cleaned_lines.append(line)
            
            # If no fields remain except comments, remove the ignore_changes block entirely
            non_comment_lines = [line for line in cleaned_lines if line and not line.startswith('#')]
            if not non_comment_lines:
                return ''
            
            return f'ignore_changes = [{", ".join(cleaned_lines)}]'
        
        output = re.sub(ignore_changes_pattern, clean_ignore_changes, output, flags=re.DOTALL)
        
        # Clean up empty lifecycle blocks
        output = re.sub(r'lifecycle\s*\{\s*\}', '', output)
        
        # Apply resource-specific optimizations for common GCP import drift issues
        # Only include fields that are NOT computed-only
        gcp_optimizations = {
            'google_storage_bucket': [
                # Only ignore configurable nested blocks that often drift during imports
                'versioning', 'cors', 'lifecycle_rule', 'labels'
            ],
            'google_compute_instance': [
                # Instance metadata often changes after creation (but is configurable)
                'metadata'
            ],
            'google_compute_firewall': [
                # These can be modified outside terraform
                'target_tags', 'source_tags'
            ],
            'google_compute_subnetwork': [
                # Secondary ranges often managed separately  
                'secondary_ip_range'
            ],
            'google_compute_network': [
                # Network routing config might be managed externally
                'routing_mode'
            ]
        }
        
        # Find the resource type from the output and apply optimizations
        for resource_pattern, ignore_fields in gcp_optimizations.items():
            if resource_pattern in output:
                # Only add ignore_changes if there are actual fields to ignore
                # and if there isn't already a lifecycle block
                if ignore_fields and 'lifecycle {' not in output:
                    ignore_block = f"""
  lifecycle {{
    ignore_changes = [
      {', '.join(ignore_fields)}
    ]
    prevent_destroy = true
  }}"""
                    # Insert before the closing brace of the resource
                    output = re.sub(r'(\n})', ignore_block + r'\1', output)
        
        return output

    def _ensure_import_blocks(self, output: str, resource_type: str, resources: List) -> str:
        """Automatically inject import blocks if they're missing from the template output.
        
        This ensures all Azure resources get import blocks for proper bulk import functionality,
        regardless of whether the template manually includes them.
        """
        try:
            if not resources:
                return output
            
            # Check if output already contains import blocks
            if 'import {' in output:
                return output  # Import blocks already present, no need to inject
            
            # Generate import blocks for all resources
            import_blocks = []
            for resource in resources:
                resource_id = resource.get('id') or resource.get('remote_id')
                resource_name = resource.get('name_sanitized') or resource.get('name', 'unknown')
                
                if resource_id and resource_name:
                    # Generate import block
                    # Convert azure_ internal types to azurerm_ Terraform types
                    if resource_type.startswith('azure_'):
                        # Direct mapping for Azure resources
                        tf_resource_type = resource_type.replace('azure_', 'azurerm_')
                        
                        # Handle special cases that need different mappings
                        special_mappings = {
                            'azurerm_virtual_machine': 'azurerm_linux_virtual_machine',
                            'azurerm_function_app': 'azurerm_linux_function_app',
                            'azurerm_web_app': 'azurerm_linux_web_app',
                            'azurerm_app_service_plan': 'azurerm_service_plan',
                            'azurerm_sql_server': 'azurerm_mssql_server',
                            'azurerm_sql_database': 'azurerm_mssql_database',
                            'azurerm_sql_elastic_pool': 'azurerm_mssql_elasticpool'
                        }
                        tf_resource_type = special_mappings.get(tf_resource_type, tf_resource_type)
                    else:
                        tf_resource_type = resource_type
                    
                    resource_display_name = tf_resource_type.replace('_', ' ').replace('azurerm ', '').title()
                    
                    import_block = f"""# Import existing {resource_display_name}: {resource.get('name', resource_name)}
import {{
  to = {tf_resource_type}.{resource_name}
  id = "{resource_id}"
}}
"""
                    import_blocks.append(import_block)
            
            # Prepend import blocks to the template output
            if import_blocks:
                import_section = '\n'.join(import_blocks) + '\n'
                output = import_section + output
            
            return output
        except Exception as e:
            print(f"Warning: Import block injection failed for {resource_type}: {e}")
            return output  # Return original output if injection fails

    def get_available_templates(self, provider: str = 'aws') -> List[str]:
        """Get list of available templates for a provider."""
        provider_dir = self.template_dir / provider
        if not provider_dir.exists():
            return []
        
        templates = []
        for template_file in provider_dir.rglob("*.tf.j2"):
            # Extract resource type from filename
            resource_type = template_file.stem  # Remove .tf.j2 extension
            templates.append(resource_type)
        
        return sorted(templates)

    def validate_template_syntax(self, resource_type: str, provider: str = 'aws') -> List[str]:
        """Validate template syntax without rendering."""
        errors = []
        try:
            template_path = self.get_template_path(resource_type, provider)
            # Load the template source directly from the loader
            try:
                source, _, _ = self.env.loader.get_source(self.env, template_path)
            except Exception as e:
                errors.append(f"Failed to load template {template_path}: {e}")
                return errors

            # Try to parse the template source
            self.env.parse(source)
            
        except Exception as e:
            errors.append(f"Template syntax error in {resource_type}: {e}")
        
        return errors


# Global Functions

_loader = None

def get_template_loader(output_dir: Optional[Path] = None):
    """Get the global template loader instance."""
    global _loader
    if _loader is None:
        _loader = AutoDiscoveryTemplateLoader(output_dir=output_dir)
    elif output_dir:
        # Update output directory if provided
        _loader.output_dir = output_dir
        _loader.update_version_filters(output_dir)
    return _loader

def reset_template_loader():
    """Reset the global template loader instance (useful for testing)."""
    global _loader
    _loader = None

def generate_provider_config(output_dir: Path, provider: str = 'aws', subscription_id: str = None, project_id: str = None, force_update: bool = False) -> None:
    """Generate provider configuration file if it doesn't exist, or update it if force_update is True."""
    provider_file = output_dir / "provider.tf"
    
    # Skip if provider.tf already exists and we're not forcing an update
    if provider_file.exists() and not force_update:
        return
    
    # For Azure, try to get subscription ID from environment or session if not provided
    if provider == 'azure' and not subscription_id:
        import os
        subscription_id = os.environ.get('AZURE_SUBSCRIPTION_ID')
        if not subscription_id:
            try:
                from terraback.cli.azure.session import get_default_subscription_id
                subscription_id = get_default_subscription_id()
            except Exception as e:
                logger.debug(f"Could not determine default subscription ID: {e}")
    
    # For GCP, try to get project ID from environment or session if not provided
    if provider == 'gcp' and not project_id:
        import os
        project_id = os.environ.get('GOOGLE_CLOUD_PROJECT')
        if not project_id:
            try:
                from terraback.cli.gcp.session import get_default_project_id
                project_id = get_default_project_id()
            except Exception as e:
                logger.debug(f"Could not determine default project ID: {e}")
    
    # Provider configurations
    provider_configs = {
        'aws': '''terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  # Configuration options
  # region = "us-east-1"  # Uncomment and set your preferred region
}

# Data sources used by various resources
data "aws_region" "current" {}
data "aws_caller_identity" "current" {}
''',
        'azure': f'''terraform {{
  required_providers {{
    azurerm = {{
      source  = "hashicorp/azurerm"
      version = "~> 4.0"
    }}
  }}
}}

provider "azurerm" {{
  features {{}}
  {f'subscription_id = "{subscription_id}"' if subscription_id else '# subscription_id = "YOUR_SUBSCRIPTION_ID"'}
}}
''',
        'gcp': f'''terraform {{
  required_providers {{
    google = {{
      source  = "hashicorp/google"
      version = "~> 6.0"
    }}
  }}
}}

provider "google" {{
  # Configuration options
  {f'project = "{project_id}"' if project_id else '# project = "YOUR_PROJECT_ID"'}
  # region  = "us-central1"
}}
'''
    }
    
    provider_config = provider_configs.get(provider, '')
    if provider_config:
        with open(provider_file, 'w', encoding='utf-8') as f:
            f.write(provider_config)
            if not provider_config.endswith('\n'):
                f.write('\n')
        print(f"Generated: {provider_file}")

def get_terraform_filename(resource_type: str) -> str:
    """Derive a standard Terraform filename from a resource type.

    The resource type is first normalised via
    :func:`normalize_terraform_resource_type` and then any provider prefix is
    stripped before appending ``.tf``. This ensures that short aliases like
    ``azure_sql_server`` map to filenames such as ``mssql_server.tf``.

    Examples:
    - aws_acm_certificate -> acm_certificate.tf
    - azure_app_service_plan -> service_plan.tf
    - azurerm_linux_virtual_machine -> linux_virtual_machine.tf
    """

    normalized = normalize_terraform_resource_type(resource_type)
    for prefix in ("aws_", "azurerm_", "azure_", "google_", "gcp_"):
        if normalized.startswith(prefix):
            return normalized[len(prefix):] + ".tf"
    return normalized + ".tf"

def generate_tf_auto(resources: List, resource_type: str, output_dir: Path, provider: str = None, **kwargs):
    """Generate Terraform file with automatic filename based on resource type.
    
    Uses AWS naming convention: strips provider prefix from resource_type.
    - azure_container_registry -> container_registry.tf
    - aws_s3_bucket -> s3_bucket.tf
    """
    if not resources:
        print(f"Skipping {resource_type} - no resources found")
        return
        
    filename = get_terraform_filename(resource_type)
    output_path = output_dir / filename
    return generate_tf(resources, resource_type, output_path, provider, **kwargs)

def generate_tf(resources: List, resource_type: str, output_path: Path, provider: str = None, **kwargs):
    """Generate Terraform file using the enhanced template loader.
    
    Auto-detects provider based on resource_type if not specified:
    - azure_* -> azure
    - google_* or gcp_* -> gcp
    - aws_* or default -> aws
    """
    if not resources:
        print(f"Skipping {resource_type} - no resources found")
        return
    
    # Auto-detect provider if not specified
    if provider is None:
        if resource_type.startswith('azure_'):
            provider = 'azure'
        elif resource_type.startswith('google_') or resource_type.startswith('gcp_'):
            provider = 'gcp'
        else:
            provider = 'aws'  # Default to AWS for backward compatibility
    
    try:
        # Pass output directory to loader for version detection
        loader = get_template_loader(output_dir=output_path.parent if output_path else None)

        tf_output = loader.render_template(resource_type, resources, provider)

        if not tf_output.strip():
            print(f"Warning: No output generated for {resource_type}")
            return

        # Ensure output directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Write the output (ensure trailing newline)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(tf_output)
            if not tf_output.endswith('\n'):
                f.write('\n')

        print(f"Generated: {output_path}")
        
        # Generate provider configuration if it doesn't exist
        subscription_id = kwargs.get('subscription_id')
        project_id = kwargs.get('project_id')
        generate_provider_config(output_path.parent, provider, subscription_id, project_id)
        
        # Validate the generated file
        validation_errors = validate_terraform_syntax(output_path)
        if validation_errors:
            print(f"Warning: Validation issues in {output_path}:")
            for error in validation_errors[:5]:  # Show first 5 errors
                print(f"  - {error}")
        
    except Exception as e:
        print(f"Error generating {resource_type}: {e}")
        raise

def validate_terraform_syntax(file_path: Path) -> List[str]:
    """Basic validation of generated Terraform files."""
    errors = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        lines = content.split('\n')
        brace_count = 0
        in_string = False
        escape_next = False
        
        for i, line in enumerate(lines, 1):
            stripped = line.strip()
            
            # Skip empty lines and comments
            if not stripped or stripped.startswith('#'):
                continue
            
            # Check for common syntax errors
            if stripped.endswith('=') or re.match(r'^\s*\w+\s*=\s*$', stripped):
                errors.append(f"Line {i}: Empty assignment - {stripped}")
            
            if re.match(r'resource\s+"[^"]+"\s+""', stripped):
                errors.append(f"Line {i}: Empty resource name")
            
            # Check for Python-style booleans
            if re.search(r'\b(True|False)\b', stripped):
                errors.append(f"Line {i}: Python-style boolean found (use lowercase)")
            
            # Track brace balance (simplified)
            for char in line:
                if escape_next:
                    escape_next = False
                    continue
                
                if char == '\\':
                    escape_next = True
                    continue
                
                if char == '"' and not escape_next:
                    in_string = not in_string
                    continue
                
                if not in_string:
                    if char == '{':
                        brace_count += 1
                    elif char == '}':
                        brace_count -= 1
        
        # Check overall brace balance
        if brace_count != 0:
            errors.append(f"Unbalanced braces: {brace_count} unclosed")
    
    except Exception as e:
        errors.append(f"Failed to validate file: {e}")
    
    return errors

def list_available_templates(provider: str = 'aws') -> List[str]:
    """List all available templates for a provider."""
    try:
        loader = get_template_loader()
        return loader.get_available_templates(provider)
    except Exception as e:
        print(f"Error listing templates: {e}")
        return []

def validate_all_templates(provider: str = 'aws') -> dict:
    """Validate syntax of all templates for a provider."""
    try:
        loader = get_template_loader()
        templates = loader.get_available_templates(provider)
        
        results = {}
        for template in templates:
            errors = loader.validate_template_syntax(template, provider)
            results[template] = errors
        
        return results
    except Exception as e:
        print(f"Error validating templates: {e}")
        return {}

# Template debugging utilities
def debug_template_render(resource_type: str, resources: List, provider: str = 'aws') -> str:
    """Render template with debug information."""
    try:
        loader = get_template_loader()
        
        # Add debug information to resources
        debug_resources = []
        for i, resource in enumerate(resources):
            if isinstance(resource, dict):
                debug_resource = dict(resource)
                debug_resource['_debug_index'] = i
                debug_resource['_debug_type'] = resource_type
                debug_resources.append(debug_resource)
            else:
                debug_resources.append(resource)
        
        output = loader.render_template(resource_type, debug_resources, provider)
        
        # Add debug header
        debug_header = f"""# DEBUG RENDER: {resource_type}
# Provider: {provider}
# Resources: {len(resources)}
# Generated: {Path.cwd()}

"""
        
        return debug_header + output
        
    except Exception as e:
        return f"# ERROR: Failed to render {resource_type}: {e}\n"


def write_terraform_file(output_dir: Path, resource: Dict[str, Any], 
                        resource_type: str, provider: str = None) -> None:
    """
    Wrapper function for backward compatibility with Azure modules.
    Converts single resource to list and calls generate_tf.
    
    Args:
        output_dir: Output directory for terraform files
        resource: Single resource dictionary
        resource_type: Type of resource (e.g., 'azure_virtual_machine')
        provider: Cloud provider (auto-detected if not specified)
    """
    from pathlib import Path
    
    if not resource:
        print(f"Skipping {resource_type} - no resource provided")
        return
    
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # Auto-detect provider if not specified
    if provider is None:
        if resource_type.startswith('azure_') or resource_type.startswith('azurerm_'):
            provider = 'azure'
        elif resource_type.startswith('google_') or resource_type.startswith('gcp_'):
            provider = 'gcp'
        else:
            provider = 'aws'
    
    # Generate appropriate filename
    filename = f"{resource_type}.tf"
    output_file = output_dir / filename
    
    # Call generate_tf with a list containing the single resource
    generate_tf([resource], resource_type, output_file, provider=provider)


# Export commonly used functions
__all__ = [
    'get_template_loader',
    'reset_template_loader',
    'generate_tf',
    'generate_provider_config',
    'validate_terraform_syntax',
    'list_available_templates',
    'validate_all_templates',
    'debug_template_render',
    'AutoDiscoveryTemplateLoader',
    'enable_template_metrics',
    'get_template_metrics',
    'print_metrics_summary',
    'TemplateMetrics'
]
