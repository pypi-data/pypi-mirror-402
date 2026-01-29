"""
Validation utilities for checking generated Terraform configurations.
"""
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from enum import Enum


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""
    ERROR = "error"      # Must be fixed before import
    WARNING = "warning"  # Should be fixed but not blocking
    INFO = "info"       # Informational, user should be aware


@dataclass
class ValidationIssue:
    """Represents a validation issue found in generated files."""
    severity: ValidationSeverity
    resource_type: str
    resource_name: str
    field: str
    message: str
    file_path: str
    suggested_action: str = ""
    current_value: Any = None


class TerraformValidator:
    """Validates generated Terraform configurations and import files."""
    
    # Patterns that indicate user needs to provide values (case-insensitive)
    # Simple string patterns and regex patterns are handled differently
    USER_INPUT_PATTERNS = [
        "CHANGE_ME",
        "CHANGEME", 
        "REPLACE_ME",
        "TODO",
        "FIXME", 
        "UPDATE_ME",
        "YOUR_",
        "PLACEHOLDER",
        "DUMMY_",
        # Regex patterns for more complex matching
        "ChangeMe\\d*!?",  # ChangeMe123!, ChangeMe!, etc.
        "ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABgQC7Q1234567890.*user@example\\.com",
        "ssh-rsa.*example\\.com",
    ]
    
    # Fields that commonly require user input
    SENSITIVE_FIELDS = [
        "password",
        "secret",
        "key",
        "token",
        "connection_string",
        "credentials"
    ]
    
    def __init__(self, output_dir: Path):
        """Initialize validator with output directory."""
        self.output_dir = Path(output_dir)
        self.issues: List[ValidationIssue] = []
    
    def validate_all(self) -> Tuple[List[ValidationIssue], bool]:
        """
        Validate all generated files in the output directory.
        
        Returns:
            Tuple of (list of issues, whether import can proceed)
        """
        self.issues = []
        
        # Validate Terraform files
        for tf_file in self.output_dir.glob("*.tf"):
            self._validate_terraform_file(tf_file)

        # Validate import JSON files from import/ subdirectory
        import_dir = self.output_dir / "import"
        if import_dir.exists():
            for json_file in import_dir.glob("*_import.json"):
                self._validate_import_file(json_file)
        
        # Check for critical issues that block import
        has_errors = any(issue.severity == ValidationSeverity.ERROR for issue in self.issues)
        
        return self.issues, not has_errors
    
    def _validate_terraform_file(self, file_path: Path) -> None:
        """Validate a single Terraform file."""
        try:
            content = file_path.read_text()
            
            # Check for user input patterns, but only in variable defaults and configuration values
            # Skip resource names, DNS zones, and other legitimate identifiers
            lines = content.split('\n')
            for i, line in enumerate(lines):
                stripped_line = line.strip()
                
                # Only check patterns in variable default values and configuration assignments
                if ('default' in stripped_line and '=' in stripped_line) or \
                   (stripped_line.endswith('=') or '= "' in stripped_line):
                    
                    for pattern in self.USER_INPUT_PATTERNS:
                        match_found = False
                        actual_match = pattern
                        
                        # Check if this is a regex pattern (contains backslashes)
                        if '\\' in pattern:
                            # This is a regex pattern
                            import re
                            try:
                                if re.search(pattern, line, re.IGNORECASE):
                                    match_obj = re.search(pattern, line, re.IGNORECASE)
                                    actual_match = match_obj.group()
                                    match_found = True
                            except re.error:
                                # If regex fails, try simple string matching
                                if pattern.lower() in line.lower():
                                    match_found = True
                        else:
                            # Simple string pattern - case insensitive
                            if pattern.lower() in line.lower():
                                match_found = True
                        
                        if match_found:
                            self._add_placeholder_issue(lines, i, pattern, actual_match, file_path)
            
            # Check for empty required fields
            self._check_empty_fields(content, file_path)
            
            # Check for Azure-specific issues
            self._check_azure_specific_issues(content, file_path)
            
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                resource_type="file",
                resource_name=file_path.name,
                field="",
                message=f"Failed to validate file: {e}",
                file_path=str(file_path)
            ))
    
    def _validate_import_file(self, file_path: Path) -> None:
        """Validate a JSON import file."""
        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            for resource in data:
                # Validate resource ID format
                remote_id = resource.get('remote_id', '')
                if remote_id:
                    self._validate_azure_resource_id(remote_id, resource, file_path)
                
                # Check for missing required data
                if not resource.get('resource_type'):
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        resource_type="import",
                        resource_name=resource.get('resource_name', 'unknown'),
                        field="resource_type",
                        message="Missing resource_type in import definition",
                        file_path=str(file_path)
                    ))
        
        except json.JSONDecodeError as e:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                resource_type="import_file",
                resource_name=file_path.name,
                field="",
                message=f"Invalid JSON: {e}",
                file_path=str(file_path)
            ))
        except Exception as e:
            self.issues.append(ValidationIssue(
                severity=ValidationSeverity.ERROR,
                resource_type="import_file",
                resource_name=file_path.name,
                field="",
                message=f"Failed to validate import file: {e}",
                file_path=str(file_path)
            ))
    
    def _check_empty_fields(self, content: str, file_path: Path) -> None:
        """Check for empty string fields that should have values."""
        # Pattern to find empty string assignments
        empty_pattern = re.compile(r'(\w+)\s*=\s*""')
        
        for match in empty_pattern.finditer(content):
            field_name = match.group(1)
            
            # Check if this is a required field
            if self._is_required_field(field_name):
                # Extract resource context
                lines = content.split('\n')
                line_num = content[:match.start()].count('\n')
                resource_info = self._extract_resource_info(lines, line_num)
                
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    resource_type=resource_info.get('type', 'unknown'),
                    resource_name=resource_info.get('name', 'unknown'),
                    field=field_name,
                    message=f"Required field '{field_name}' is empty",
                    file_path=str(file_path),
                    suggested_action=f"Provide a value for '{field_name}'",
                    current_value=""
                ))
    
    def _check_azure_specific_issues(self, content: str, file_path: Path) -> None:
        """Check for Azure-specific validation issues."""
        # Check for storage account name validation (3-24 chars, lowercase alphanumeric)
        storage_pattern = re.compile(r'storage_account_name\s*=\s*"([^"]*)"')
        for match in storage_pattern.finditer(content):
            value = match.group(1)
            if value and not re.match(r'^[a-z0-9]{3,24}$', value):
                if value not in ["var.function_app_storage_account_name", "${var.function_app_storage_account_name}"]:
                    lines = content.split('\n')
                    line_num = content[:match.start()].count('\n')
                    resource_info = self._extract_resource_info(lines, line_num)
                    
                    self.issues.append(ValidationIssue(
                        severity=ValidationSeverity.ERROR,
                        resource_type=resource_info.get('type', 'unknown'),
                        resource_name=resource_info.get('name', 'unknown'),
                        field="storage_account_name",
                        message=f"Invalid storage account name '{value}' (must be 3-24 lowercase alphanumeric)",
                        file_path=str(file_path),
                        current_value=value
                    ))
        
        # Check for empty tenant_id in key vaults
        if 'azurerm_key_vault' in content:
            tenant_pattern = re.compile(r'tenant_id\s*=\s*""')
            if tenant_pattern.search(content):
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    resource_type="azurerm_key_vault",
                    resource_name="",
                    field="tenant_id",
                    message="Key Vault tenant_id cannot be empty",
                    file_path=str(file_path),
                    suggested_action="Run 'az account show --query tenantId -o tsv' to get tenant ID"
                ))
    
    def _validate_azure_resource_id(self, resource_id: str, resource: Dict, file_path: Path) -> None:
        """Validate Azure resource ID format."""
        # Check for common casing issues in Azure resource IDs
        resource_type = resource.get('resource_type', '')
        
        # Redis cache specific check
        if 'redis' in resource_type.lower():
            if '/Microsoft.Cache/Redis/' in resource_id:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    resource_type=resource_type,
                    resource_name=resource.get('resource_name', ''),
                    field="remote_id",
                    message="Redis resource ID has incorrect casing (should be /redis/ not /Redis/)",
                    file_path=str(file_path),
                    suggested_action="Change '/Microsoft.Cache/Redis/' to '/Microsoft.Cache/redis/'",
                    current_value=resource_id
                ))
        
        # Service plan specific check
        if 'service_plan' in resource_type.lower() or 'app_service_plan' in resource_type.lower():
            if '/serverfarms/' in resource_id.lower() and '/serverFarms/' not in resource_id:
                self.issues.append(ValidationIssue(
                    severity=ValidationSeverity.ERROR,
                    resource_type=resource_type,
                    resource_name=resource.get('resource_name', ''),
                    field="remote_id",
                    message="Service plan ID has incorrect casing (should be /serverFarms/ not /serverfarms/)",
                    file_path=str(file_path),
                    suggested_action="Change '/serverfarms/' to '/serverFarms/'",
                    current_value=resource_id
                ))
    
    def _extract_resource_info(self, lines: List[str], current_line: int) -> Dict[str, str]:
        """Extract resource type and name from terraform file context."""
        # Look backwards for resource declaration
        for i in range(current_line, max(0, current_line - 20), -1):
            line = lines[i]
            match = re.match(r'resource\s+"([^"]+)"\s+"([^"]+)"', line)
            if match:
                return {
                    'type': match.group(1),
                    'name': match.group(2)
                }
        return {}
    
    def _add_placeholder_issue(self, lines: List[str], line_index: int, pattern: str, actual_match: str, file_path: Path) -> None:
        """Add a placeholder validation issue."""
        resource_info = self._extract_resource_info(lines, line_index)
        field = self._extract_field_name(lines[line_index])
        
        # Treat placeholders as warnings to allow import to proceed
        self.issues.append(ValidationIssue(
            severity=ValidationSeverity.WARNING,
            resource_type=resource_info.get('type', 'unknown'),
            resource_name=resource_info.get('name', 'unknown'),
            field=field,
            message=f"Field contains placeholder value '{actual_match}' - should be updated after import",
            file_path=str(file_path),
            suggested_action=f"Update '{field}' with actual value after successful import",
            current_value=actual_match
        ))
    
    def _extract_field_name(self, line: str) -> str:
        """Extract field name from a line."""
        match = re.match(r'\s*(\w+)\s*=', line)
        if match:
            return match.group(1)
        return "unknown"
    
    def _is_required_field(self, field_name: str) -> bool:
        """Check if a field is typically required."""
        required_fields = [
            'tenant_id',
            'subscription_id',
            'client_id',
            'sku_name',
            'location',
            'resource_group_name'
        ]
        return field_name.lower() in [f.lower() for f in required_fields]
    
    def generate_report(self) -> str:
        """Generate a human-readable validation report."""
        if not self.issues:
            return "[OK] No validation issues found. Ready to import!"
        
        report = []
        report.append("=" * 80)
        report.append("TERRAFORM VALIDATION REPORT")
        report.append("=" * 80)
        report.append("")
        
        # Group issues by severity
        errors = [i for i in self.issues if i.severity == ValidationSeverity.ERROR]
        warnings = [i for i in self.issues if i.severity == ValidationSeverity.WARNING]
        info = [i for i in self.issues if i.severity == ValidationSeverity.INFO]
        
        if errors:
            report.append(f"[X] ERRORS ({len(errors)}) - Must be fixed before import:")
            report.append("-" * 40)
            for issue in errors:
                report.append(f"  - {issue.resource_type}.{issue.resource_name}")
                report.append(f"    Field: {issue.field}")
                report.append(f"    Issue: {issue.message}")
                if issue.suggested_action:
                    report.append(f"    Action: {issue.suggested_action}")
                report.append(f"    File: {issue.file_path}")
                report.append("")
        
        if warnings:
            report.append(f"[!] WARNINGS ({len(warnings)}) - Should be addressed:")
            report.append("-" * 40)
            for issue in warnings:
                report.append(f"  - {issue.resource_type}.{issue.resource_name}")
                report.append(f"    Field: {issue.field}")
                report.append(f"    Issue: {issue.message}")
                if issue.suggested_action:
                    report.append(f"    Action: {issue.suggested_action}")
                report.append("")
        
        if info:
            report.append(f"[i] INFO ({len(info)}):")
            report.append("-" * 40)
            for issue in info:
                report.append(f"  - {issue.message}")
                report.append("")
        
        # List files requiring user attention
        files_needing_attention = set()
        user_input_issues = [i for i in self.issues if any(pattern.lower() in i.message.lower() for pattern in ['placeholder', 'changeme', 'todo', 'fixme', 'your_', 'update'])]
        
        if user_input_issues:
            for issue in user_input_issues:
                files_needing_attention.add(issue.file_path)
        
        if files_needing_attention:
            report.append("=" * 80)
            report.append("FILES REQUIRING YOUR ATTENTION:")
            report.append("=" * 80)
            report.append("")
            report.append("The following files contain placeholder values that require your input:")
            report.append("")
            for file_path in sorted(files_needing_attention):
                report.append(f"  • {file_path}")
            report.append("")
            report.append("Please update these files with your actual values and re-run the import.")
            report.append("")
        
        report.append("=" * 80)
        report.append("SUMMARY:")
        report.append(f"  Total Issues: {len(self.issues)}")
        report.append(f"  Errors: {len(errors)}")
        report.append(f"  Warnings: {len(warnings)}")
        report.append(f"  Info: {len(info)}")
        if files_needing_attention:
            report.append(f"  Files needing attention: {len(files_needing_attention)}")
        report.append("")
        
        if errors:
            report.append("[X] Import blocked due to errors. Please fix the issues above and try again.")
        else:
            if files_needing_attention:
                report.append("[!] Import can proceed, but user input required.")
                report.append("    Update placeholder values in the files listed above,")
                report.append("    then re-run the import command.")
            elif warnings:
                # Check if warnings are primarily placeholder issues
                placeholder_warnings = [w for w in warnings if 'placeholder value' in w.message.lower()]
                if placeholder_warnings:
                    report.append("[!] Import can proceed, but placeholder values detected.")
                    report.append("    Resources will be imported successfully, but you should update")
                    report.append("    CHANGEME and placeholder values after import for proper configuration.")
                else:
                    report.append("[OK] Import can proceed. Consider addressing warnings for optimal results.")
            else:
                report.append("[OK] No issues found. Ready to import!")
        
        return "\n".join(report)


def validate_before_import(output_dir: Path) -> bool:
    """
    Validate generated files before import.
    
    Returns:
        True if import can proceed, False otherwise
    """
    validator = TerraformValidator(output_dir)
    issues, can_proceed = validator.validate_all()
    
    # Print the report
    print(validator.generate_report())
    
    # Save report to file
    report_file = output_dir / "validation_report.txt"
    report_file.write_text(validator.generate_report(), encoding='utf-8')
    print(f"\nValidation report saved to: {report_file}")
    
    return can_proceed