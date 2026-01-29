"""
Comprehensive tests for ImportBlockGenerator.

Tests cover:
- Basic import ID lookup for common AWS resources
- Complex composite IDs (API Gateway, Route53, Step Functions)
- AWS ID extraction from resource names (sg-xxx, vpc-xxx)
- Fallback matching strategies
- Edge cases (missing data, malformed resources)
"""

import pytest
from pathlib import Path
from terraback.utils.stack_generator import ImportBlockGenerator


class TestImportBlockGenerator:
    """Test suite for ImportBlockGenerator functionality."""

    @pytest.fixture
    def generator(self):
        """Create a fresh ImportBlockGenerator instance."""
        return ImportBlockGenerator()

    @pytest.fixture
    def sample_resources(self):
        """Sample scanned resources for testing."""
        return {
            "lambda_function": [
                {
                    "id": "arn:aws:lambda:us-east-1:123456789012:function:my-function",
                    "FunctionName": "my-function",
                    "name_sanitized": "my_function",
                    "Name": "my-function",
                },
                {
                    "id": "arn:aws:lambda:us-east-1:123456789012:function:api-handler",
                    "FunctionName": "api-handler",
                    "name_sanitized": "api_handler",
                    "Name": "api-handler",
                }
            ],
            "s3_bucket": [
                {
                    "id": "my-data-bucket",
                    "Name": "my-data-bucket",
                    "name_sanitized": "my_data_bucket",
                },
                {
                    "id": "logs-bucket-2024",
                    "Name": "logs-bucket-2024",
                    "name_sanitized": "logs_bucket_2024",
                }
            ],
            "dynamodb_table": [
                {
                    "id": "UserTable",
                    "TableName": "UserTable",
                    "name_sanitized": "user_table",
                    "Name": "UserTable",
                }
            ],
            "security_group": [
                {
                    "id": "sg-0f8a39e1b42aa274f",
                    "GroupId": "sg-0f8a39e1b42aa274f",
                    "name_sanitized": "resource_0f8a39e1b42aa274f",
                    "Name": "web-sg",
                }
            ],
            "vpc": [
                {
                    "id": "vpc-2a863150",
                    "VpcId": "vpc-2a863150",
                    "name_sanitized": "vpc_2a863150",
                    "Name": "main-vpc",
                }
            ],
            "subnet": [
                {
                    "id": "subnet-0e5b62425884d7cf5",
                    "SubnetId": "subnet-0e5b62425884d7cf5",
                    "name_sanitized": "resource_subnet_0e5b62425884d7cf5",
                    "Name": "public-subnet-1a",
                }
            ],
            "iam_role": [
                {
                    "id": "lambda-execution-role",
                    "RoleName": "lambda-execution-role",
                    "name_sanitized": "lambda_execution_role",
                    "Name": "lambda-execution-role",
                }
            ],
            "iam_policy": [
                {
                    "id": "arn:aws:iam::123456789012:policy/MyPolicy",
                    "Arn": "arn:aws:iam::123456789012:policy/MyPolicy",
                    "name_sanitized": "my_policy",
                    "Name": "MyPolicy",
                }
            ],
            "route53_zone": [
                {
                    "id": "Z1234567890ABC",
                    "ZoneId": "Z1234567890ABC",
                    "HostedZoneId": "/hostedzone/Z1234567890ABC",
                    "name_sanitized": "example_com",
                    "Name": "example.com.",
                }
            ],
            "api_gateway_rest_api": [
                {
                    "id": "abc123def456",
                    "name_sanitized": "my_api",
                    "Name": "my-api",
                }
            ],
        }

    # -------------------------------------------------------------------------
    # Basic Import ID Lookup Tests
    # -------------------------------------------------------------------------

    def test_build_import_id_lookup_lambda(self, generator, sample_resources):
        """Test lookup table creation for Lambda functions."""
        lookup = generator._build_import_id_lookup(sample_resources, "aws")

        lambda_lookup = lookup.get("aws_lambda_function", {})
        assert lambda_lookup is not None

        # Should find by name_sanitized
        assert lambda_lookup.get("my_function") == "arn:aws:lambda:us-east-1:123456789012:function:my-function"
        assert lambda_lookup.get("api_handler") == "arn:aws:lambda:us-east-1:123456789012:function:api-handler"

        # Should also find by FunctionName
        assert lambda_lookup.get("my-function") == "arn:aws:lambda:us-east-1:123456789012:function:my-function"

    def test_build_import_id_lookup_s3(self, generator, sample_resources):
        """Test lookup table creation for S3 buckets."""
        lookup = generator._build_import_id_lookup(sample_resources, "aws")

        s3_lookup = lookup.get("aws_s3_bucket", {})
        assert s3_lookup.get("my_data_bucket") == "my-data-bucket"
        assert s3_lookup.get("logs_bucket_2024") == "logs-bucket-2024"

    def test_build_import_id_lookup_dynamodb(self, generator, sample_resources):
        """Test lookup table creation for DynamoDB tables."""
        lookup = generator._build_import_id_lookup(sample_resources, "aws")

        dynamodb_lookup = lookup.get("aws_dynamodb_table", {})
        assert dynamodb_lookup.get("user_table") == "UserTable"
        assert dynamodb_lookup.get("UserTable") == "UserTable"

    def test_build_import_id_lookup_iam(self, generator, sample_resources):
        """Test lookup table creation for IAM resources."""
        lookup = generator._build_import_id_lookup(sample_resources, "aws")

        # IAM Role
        role_lookup = lookup.get("aws_iam_role", {})
        assert role_lookup.get("lambda_execution_role") == "lambda-execution-role"

        # IAM Policy (uses ARN)
        policy_lookup = lookup.get("aws_iam_policy", {})
        assert policy_lookup.get("my_policy") == "arn:aws:iam::123456789012:policy/MyPolicy"

    # -------------------------------------------------------------------------
    # AWS ID Extraction Tests
    # -------------------------------------------------------------------------

    def test_extract_id_from_resource_name_security_group(self, generator):
        """Test extraction of security group ID from resource name."""
        # Common patterns
        assert generator._extract_id_from_resource_name("resource_0f8a39e1b42aa274f", "sg-") == "sg-0f8a39e1b42aa274f"
        assert generator._extract_id_from_resource_name("0f8a39e1b42aa274f", "sg-") == "sg-0f8a39e1b42aa274f"

        # Should not extract from non-hex names
        assert generator._extract_id_from_resource_name("web_server_sg", "sg-") == ""

    def test_extract_id_from_resource_name_vpc(self, generator):
        """Test extraction of VPC ID from resource name."""
        assert generator._extract_id_from_resource_name("vpc_2a863150", "vpc-") == "vpc-2a863150"
        assert generator._extract_id_from_resource_name("resource_vpc_2a863150", "vpc-") == "vpc-2a863150"
        assert generator._extract_id_from_resource_name("2a863150", "vpc-") == "vpc-2a863150"

    def test_extract_id_from_resource_name_subnet(self, generator):
        """Test extraction of subnet ID from resource name."""
        assert generator._extract_id_from_resource_name("resource_subnet_0e5b62425884d7cf5", "subnet-") == "subnet-0e5b62425884d7cf5"
        assert generator._extract_id_from_resource_name("subnet_0e5b62425884d7cf5", "subnet-") == "subnet-0e5b62425884d7cf5"

    def test_extract_id_from_resource_name_other_resources(self, generator):
        """Test extraction for other AWS resources with IDs."""
        # Internet Gateway
        assert generator._extract_id_from_resource_name("igw_abc123def456", "igw-") == "igw-abc123def456"

        # Route Table
        assert generator._extract_id_from_resource_name("rtb_12345678", "rtb-") == "rtb-12345678"

        # EBS Volume
        assert generator._extract_id_from_resource_name("vol_0a1b2c3d4e5f", "vol-") == "vol-0a1b2c3d4e5f"

    def test_extract_id_from_resource_name_edge_cases(self, generator):
        """Test edge cases in ID extraction."""
        # Empty string
        assert generator._extract_id_from_resource_name("", "sg-") == ""

        # Too short (less than 8 hex chars)
        assert generator._extract_id_from_resource_name("resource_abc", "sg-") == ""

        # Too long (more than 17 hex chars)
        assert generator._extract_id_from_resource_name("resource_0123456789abcdef01234", "sg-") == ""

        # Contains non-hex characters
        assert generator._extract_id_from_resource_name("resource_0g8a39e1b42aa274f", "sg-") == ""

    # -------------------------------------------------------------------------
    # HCL Resource Extraction Tests
    # -------------------------------------------------------------------------

    def test_extract_resources_basic(self, generator):
        """Test extraction of resources from HCL content."""
        hcl_content = '''
resource "aws_lambda_function" "my_function" {
  function_name = "my-function"
  runtime       = "python3.9"
}

resource "aws_s3_bucket" "data_bucket" {
  bucket = "my-data-bucket"
}
'''
        resources = generator._extract_resources(hcl_content)

        assert len(resources) == 2
        assert resources[0][:3] == ("aws_lambda_function", "my_function", "my_function")
        assert resources[1][:3] == ("aws_s3_bucket", "data_bucket", "data_bucket")

    def test_extract_resources_with_aws_ids(self, generator):
        """Test extraction of resources that have AWS IDs in their names."""
        hcl_content = '''
resource "aws_security_group" "resource_0f8a39e1b42aa274f" {
  name = "web-sg"
}

resource "aws_vpc" "vpc_2a863150" {
  cidr_block = "10.0.0.0/16"
}
'''
        resources = generator._extract_resources(hcl_content)

        assert len(resources) == 2
        # Should extract AWS ID from resource name
        assert resources[0][:3] == ("aws_security_group", "resource_0f8a39e1b42aa274f", "sg-0f8a39e1b42aa274f")
        assert resources[1][:3] == ("aws_vpc", "vpc_2a863150", "vpc-2a863150")

    def test_extract_resources_nested_blocks(self, generator):
        """Test extraction with nested blocks in HCL."""
        hcl_content = '''
resource "aws_lambda_function" "processor" {
  function_name = "data-processor"

  environment {
    variables = {
      ENV = "prod"
    }
  }

  vpc_config {
    subnet_ids = ["subnet-123"]
  }
}
'''
        resources = generator._extract_resources(hcl_content)

        assert len(resources) == 1
        assert resources[0][0] == "aws_lambda_function"
        assert resources[0][1] == "processor"

    def test_extract_resources_multiple_resources_same_type(self, generator):
        """Test extraction of multiple resources of the same type."""
        hcl_content = '''
resource "aws_s3_bucket" "logs" {
  bucket = "logs-bucket"
}

resource "aws_s3_bucket" "data" {
  bucket = "data-bucket"
}

resource "aws_s3_bucket" "backups" {
  bucket = "backup-bucket"
}
'''
        resources = generator._extract_resources(hcl_content)

        assert len(resources) == 3
        assert resources[0][:3] == ("aws_s3_bucket", "logs", "logs")
        assert resources[1][:3] == ("aws_s3_bucket", "data", "data")
        assert resources[2][:3] == ("aws_s3_bucket", "backups", "backups")

    # -------------------------------------------------------------------------
    # Import ID Finding Tests
    # -------------------------------------------------------------------------

    def test_find_import_id_exact_match(self, generator, sample_resources):
        """Test finding import ID with exact match."""
        lookup = generator._build_import_id_lookup(sample_resources, "aws")

        import_id = generator._find_import_id(
            "aws_lambda_function",
            "my_function",
            lookup,
            "aws"
        )

        assert import_id == "arn:aws:lambda:us-east-1:123456789012:function:my-function"

    def test_find_import_id_case_insensitive(self, generator, sample_resources):
        """Test finding import ID with case-insensitive matching."""
        lookup = generator._build_import_id_lookup(sample_resources, "aws")

        # Lookup stores both original and lowercase
        import_id = generator._find_import_id(
            "aws_dynamodb_table",
            "usertable",
            lookup,
            "aws"
        )

        assert import_id == "UserTable"

    def test_find_import_id_direct_id_resource_types(self, generator):
        """Test resources where identifier IS the import ID."""
        lookup = {}

        # VPC - AWS ID is the import ID
        vpc_id = generator._find_import_id("aws_vpc", "vpc-2a863150", lookup, "aws")
        assert vpc_id == "vpc-2a863150"

        # Security Group
        sg_id = generator._find_import_id("aws_security_group", "sg-0f8a39e1b42aa274f", lookup, "aws")
        assert sg_id == "sg-0f8a39e1b42aa274f"

        # Subnet
        subnet_id = generator._find_import_id("aws_subnet", "subnet-0e5b62425884d7cf5", lookup, "aws")
        assert subnet_id == "subnet-0e5b62425884d7cf5"

    def test_find_import_id_arn_resources(self, generator):
        """Test resources that use ARNs as import IDs."""
        lookup = {}

        # SNS Topic
        topic_arn = "arn:aws:sns:us-east-1:123456789012:my-topic"
        import_id = generator._find_import_id("aws_sns_topic", topic_arn, lookup, "aws")
        assert import_id == topic_arn

        # Step Functions State Machine
        sm_arn = "arn:aws:states:us-east-1:123456789012:stateMachine:my-state-machine"
        import_id = generator._find_import_id("aws_sfn_state_machine", sm_arn, lookup, "aws")
        assert import_id == sm_arn

    def test_find_import_id_not_found(self, generator):
        """Test when import ID cannot be found."""
        lookup = {"aws_lambda_function": {}}

        import_id = generator._find_import_id(
            "aws_lambda_function",
            "nonexistent_function",
            lookup,
            "aws"
        )

        assert import_id == ""

    def test_find_import_id_empty_identifier(self, generator):
        """Test handling of empty identifier."""
        lookup = {"aws_lambda_function": {"test": "arn:aws:lambda:us-east-1:123456789012:function:test"}}

        import_id = generator._find_import_id(
            "aws_lambda_function",
            "",
            lookup,
            "aws"
        )

        assert import_id == ""

    # -------------------------------------------------------------------------
    # Full Import Generation Tests
    # -------------------------------------------------------------------------

    def test_generate_imports_from_modules_basic(self, generator, tmp_path, sample_resources):
        """Test full import generation from module files."""
        # Create module structure
        modules_dir = tmp_path / "modules" / "lambda"
        modules_dir.mkdir(parents=True)

        # Write a module file with Lambda function
        (modules_dir / "function.tf").write_text('''
resource "aws_lambda_function" "my_function" {
  function_name = "my-function"
  runtime       = "python3.9"
}
''')

        module_mapping = {
            "lambda_function": ("lambda", "function.tf")
        }

        imports = generator.generate_imports_from_modules(
            tmp_path,
            sample_resources,
            module_mapping,
            "aws"
        )

        assert "import {" in imports
        assert 'to = module.lambda.aws_lambda_function.my_function' in imports
        assert 'id = "arn:aws:lambda:us-east-1:123456789012:function:my-function"' in imports

    def test_generate_imports_from_modules_multiple_resources(self, generator, tmp_path, sample_resources):
        """Test import generation for multiple resources."""
        # Create module structure
        modules_dir = tmp_path / "modules" / "storage"
        modules_dir.mkdir(parents=True)

        # Write module file with S3 buckets
        (modules_dir / "buckets.tf").write_text('''
resource "aws_s3_bucket" "my_data_bucket" {
  bucket = "my-data-bucket"
}

resource "aws_s3_bucket" "logs_bucket_2024" {
  bucket = "logs-bucket-2024"
}
''')

        module_mapping = {
            "s3_bucket": ("storage", "buckets.tf")
        }

        imports = generator.generate_imports_from_modules(
            tmp_path,
            sample_resources,
            module_mapping,
            "aws"
        )

        # Should have 2 import blocks
        assert imports.count("import {") == 2
        assert "module.storage.aws_s3_bucket.my_data_bucket" in imports
        assert "module.storage.aws_s3_bucket.logs_bucket_2024" in imports

    def test_generate_imports_from_modules_vpc_resources(self, generator, tmp_path, sample_resources):
        """Test import generation for VPC resources with AWS IDs."""
        modules_dir = tmp_path / "modules" / "networking"
        modules_dir.mkdir(parents=True)

        (modules_dir / "vpc.tf").write_text('''
resource "aws_vpc" "vpc_2a863150" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_security_group" "resource_0f8a39e1b42aa274f" {
  name = "web-sg"
}
''')

        module_mapping = {
            "vpc": ("networking", "vpc.tf"),
            "security_group": ("networking", "vpc.tf"),
        }

        imports = generator.generate_imports_from_modules(
            tmp_path,
            sample_resources,
            module_mapping,
            "aws"
        )

        # VPC import
        assert 'to = module.networking.aws_vpc.vpc_2a863150' in imports
        assert 'id = "vpc-2a863150"' in imports

        # Security Group import
        assert 'to = module.networking.aws_security_group.resource_0f8a39e1b42aa274f' in imports
        assert 'id = "sg-0f8a39e1b42aa274f"' in imports

    def test_generate_imports_skips_metadata_files(self, generator, tmp_path, sample_resources):
        """Test that variables.tf, outputs.tf, locals.tf are skipped."""
        modules_dir = tmp_path / "modules" / "lambda"
        modules_dir.mkdir(parents=True)

        # Create metadata files that should be skipped
        (modules_dir / "variables.tf").write_text('variable "test" {}')
        (modules_dir / "outputs.tf").write_text('output "test" { value = "test" }')
        (modules_dir / "locals.tf").write_text('locals { test = "test" }')

        # Create actual resource file
        (modules_dir / "function.tf").write_text('''
resource "aws_lambda_function" "my_function" {
  function_name = "my-function"
}
''')

        module_mapping = {"lambda_function": ("lambda", "function.tf")}

        imports = generator.generate_imports_from_modules(
            tmp_path,
            sample_resources,
            module_mapping,
            "aws"
        )

        # Should only have 1 import block (from function.tf)
        assert imports.count("import {") == 1
        assert "module.lambda.aws_lambda_function.my_function" in imports

    def test_generate_imports_no_modules_dir(self, generator, tmp_path, sample_resources):
        """Test handling when modules directory doesn't exist."""
        module_mapping = {}

        imports = generator.generate_imports_from_modules(
            tmp_path,
            sample_resources,
            module_mapping,
            "aws"
        )

        # Should return header only
        assert "# Terraform import blocks" in imports
        assert "import {" not in imports

    # -------------------------------------------------------------------------
    # Edge Cases and Error Handling
    # -------------------------------------------------------------------------

    def test_build_import_id_lookup_missing_id(self, generator):
        """Test handling resources with missing IDs."""
        resources = {
            "lambda_function": [
                {
                    "FunctionName": "my-function",
                    "name_sanitized": "my_function",
                    # Missing 'id' field
                }
            ]
        }

        lookup = generator._build_import_id_lookup(resources, "aws")

        # Should still create lookup, but won't have import ID
        assert "aws_lambda_function" in lookup

    def test_build_import_id_lookup_empty_resources(self, generator):
        """Test handling empty resource lists."""
        resources = {
            "lambda_function": []
        }

        lookup = generator._build_import_id_lookup(resources, "aws")

        # Should handle empty list gracefully
        assert isinstance(lookup, dict)

    def test_extract_resources_malformed_hcl(self, generator):
        """Test extraction from malformed HCL."""
        # Missing closing brace
        malformed_hcl = '''
resource "aws_lambda_function" "test" {
  function_name = "test"
'''

        # Should not crash, may return partial results
        resources = generator._extract_resources(malformed_hcl)
        assert isinstance(resources, list)

    def test_extract_resources_empty_content(self, generator):
        """Test extraction from empty content."""
        resources = generator._extract_resources("")
        assert resources == []

    def test_get_resource_id_aws_multiple_fallbacks(self, generator):
        """Test resource ID extraction with multiple fallback keys."""
        # Resource with multiple possible ID keys
        resource = {
            "Name": "my-bucket",
            "BucketName": "actual-bucket-name",
            "id": "final-id"
        }

        resource_id = generator._get_resource_id(resource, "aws_s3_bucket", "aws")

        # Should prefer 'Name' first (from keys_to_try for S3)
        assert resource_id == "my-bucket"

    def test_get_terraform_resource_type_aws(self, generator):
        """Test Terraform resource type conversion for AWS."""
        assert generator._get_terraform_resource_type("lambda_function", "aws") == "aws_lambda_function"
        assert generator._get_terraform_resource_type("aws_lambda_function", "aws") == "aws_lambda_function"

    def test_get_terraform_resource_type_azure(self, generator):
        """Test Terraform resource type conversion for Azure."""
        assert generator._get_terraform_resource_type("azure_virtual_network", "azure") == "azurerm_virtual_network"
        assert generator._get_terraform_resource_type("azurerm_virtual_network", "azure") == "azurerm_virtual_network"

    def test_get_terraform_resource_type_gcp(self, generator):
        """Test Terraform resource type conversion for GCP."""
        assert generator._get_terraform_resource_type("compute_instance", "gcp") == "google_compute_instance"
        assert generator._get_terraform_resource_type("google_compute_instance", "gcp") == "google_compute_instance"

    # -------------------------------------------------------------------------
    # Integration-style Tests
    # -------------------------------------------------------------------------

    def test_end_to_end_lambda_import(self, generator, tmp_path):
        """End-to-end test: scan data to import block for Lambda."""
        # Setup scanned resources
        resources = {
            "lambda_function": [
                {
                    "id": "arn:aws:lambda:us-east-1:123456789012:function:my-function",
                    "FunctionName": "my-function",
                    "name_sanitized": "my_function",
                }
            ]
        }

        # Setup module structure
        modules_dir = tmp_path / "modules" / "lambda"
        modules_dir.mkdir(parents=True)
        (modules_dir / "function.tf").write_text('''
resource "aws_lambda_function" "my_function" {
  function_name = "my-function"
  runtime       = "python3.9"
  handler       = "index.handler"
}
''')

        module_mapping = {"lambda_function": ("lambda", "function.tf")}

        # Generate imports
        imports = generator.generate_imports_from_modules(
            tmp_path, resources, module_mapping, "aws"
        )

        # Validate output
        assert "# Terraform import blocks" in imports
        assert "# Terraform 1.5+ required" in imports
        assert "import {" in imports
        assert 'to = module.lambda.aws_lambda_function.my_function' in imports
        assert 'id = "arn:aws:lambda:us-east-1:123456789012:function:my-function"' in imports

    def test_end_to_end_vpc_networking(self, generator, tmp_path):
        """End-to-end test: VPC and networking resources."""
        resources = {
            "vpc": [
                {"id": "vpc-123abc", "VpcId": "vpc-123abc", "name_sanitized": "vpc_123abc"}
            ],
            "subnet": [
                {"id": "subnet-456def", "SubnetId": "subnet-456def", "name_sanitized": "subnet_456def"}
            ],
            "security_group": [
                {"id": "sg-789ghi", "GroupId": "sg-789ghi", "name_sanitized": "sg_789ghi"}
            ]
        }

        modules_dir = tmp_path / "modules" / "networking"
        modules_dir.mkdir(parents=True)
        (modules_dir / "vpc.tf").write_text('''
resource "aws_vpc" "vpc_123abc" {
  cidr_block = "10.0.0.0/16"
}

resource "aws_subnet" "subnet_456def" {
  vpc_id     = aws_vpc.vpc_123abc.id
  cidr_block = "10.0.1.0/24"
}

resource "aws_security_group" "sg_789ghi" {
  vpc_id = aws_vpc.vpc_123abc.id
}
''')

        module_mapping = {
            "vpc": ("networking", "vpc.tf"),
            "subnet": ("networking", "vpc.tf"),
            "security_group": ("networking", "vpc.tf"),
        }

        imports = generator.generate_imports_from_modules(
            tmp_path, resources, module_mapping, "aws"
        )

        # All three resources should have import blocks
        assert imports.count("import {") == 3
        assert "module.networking.aws_vpc.vpc_123abc" in imports
        assert "module.networking.aws_subnet.subnet_456def" in imports
        assert "module.networking.aws_security_group.sg_789ghi" in imports
