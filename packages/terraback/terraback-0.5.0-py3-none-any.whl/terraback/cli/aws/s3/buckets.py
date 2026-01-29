from pathlib import Path
from terraback.cli.aws.session import get_boto_session
from terraback.terraform_generator.writer import generate_tf
from terraback.terraform_generator.imports import generate_imports_file
from terraback.utils.importer import ImportManager
from terraback.cli.aws.resource_processor import process_resources

def scan_buckets(output_dir: Path, profile: str = "", region: str = "us-east-1"):
    """
    Scans for S3 buckets and their configurations, then generates Terraform code.
    If region is specified, only scans buckets in that region.
    """
    boto_session = get_boto_session(profile, region)
    s3_client = boto_session.client("s3")
    
    # Get the initial list of all buckets
    all_buckets_meta = s3_client.list_buckets()["Buckets"]
    
    detailed_buckets = []
    total_buckets = len(all_buckets_meta)
    region_filtered_count = 0
    
    print(f"Found {total_buckets} S3 buckets total")
    if region and region != "all":
        print(f"Filtering for region: {region}")

    for bucket in all_buckets_meta:
        bucket_name = bucket["Name"]
        
        # Check bucket location if region filtering is enabled
        if region and region != "all":
            try:
                location_response = s3_client.get_bucket_location(Bucket=bucket_name)
                bucket_region = location_response.get('LocationConstraint')
                # us-east-1 returns None for LocationConstraint
                if bucket_region is None:
                    bucket_region = 'us-east-1'
                
                if bucket_region != region:
                    region_filtered_count += 1
                    continue  # Skip buckets not in the target region
                    
            except Exception as e:
                print(f"  - Could not get location for bucket '{bucket_name}': {e}")
                continue  # Skip buckets we can't check location for
        
        bucket_details = {
            "Name": bucket_name
        } # Start with the name - sanitized version will be added by process_resources

        try:
            # First, verify the bucket still exists by getting its location
            # This will fail with NoSuchBucket if the bucket was deleted
            s3_client.get_bucket_location(Bucket=bucket_name)
            
            # Get bucket versioning configuration
            versioning = s3_client.get_bucket_versioning(Bucket=bucket_name)
            if versioning.get('Status'):
                bucket_details['Versioning'] = versioning
            
            # Get public access block configuration
            try:
                pab = s3_client.get_public_access_block(Bucket=bucket_name)
                bucket_details['PublicAccessBlock'] = pab['PublicAccessBlockConfiguration']
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchPublicAccessBlockConfiguration':
                    raise e
            
            # Get bucket tags
            try:
                tagging = s3_client.get_bucket_tagging(Bucket=bucket_name)
                if 'TagSet' in tagging:
                    bucket_details['Tags'] = {tag['Key']: tag['Value'] for tag in tagging['TagSet']}
            except s3_client.exceptions.ClientError as e:
                if e.response['Error']['Code'] != 'NoSuchTagSet':
                    raise e
            
            detailed_buckets.append(bucket_details)
        except Exception as e:
            # Handle permission errors and non-existent buckets gracefully
            error_code = getattr(e, 'response', {}).get('Error', {}).get('Code', 'Unknown')
            if error_code == 'NoSuchBucket':
                print(f"  - Skipping bucket '{bucket_name}': bucket no longer exists")
            else:
                print(f"  - Could not get details for bucket '{bucket_name}': {e}")

    # Process resources to ensure proper naming
    detailed_buckets = process_resources(detailed_buckets, 'buckets')

    output_file = output_dir / "s3_bucket.tf"
    generate_tf(detailed_buckets, "aws_s3_bucket", output_file) # Use a specific template key
    
    if region and region != "all" and region_filtered_count > 0:
        print(f"Filtered out {region_filtered_count} buckets from other regions")
    
    print(f"Generated Terraform for {len(detailed_buckets)} S3 Buckets in {region} -> {output_file}")
    generate_imports_file("s3_bucket", detailed_buckets, remote_resource_id_key="Name", output_dir=output_dir, provider="aws")
    
    # Generate import entries for S3 bucket sub-resources
    versioning_resources = []
    public_access_resources = []
    
    for bucket in detailed_buckets:
        bucket_name = bucket['Name']
        bucket_name_sanitized = bucket['name_sanitized']  # Use the standardized name from process_resources
        
        # Create import entry for versioning if enabled
        if bucket.get('Versioning') and bucket['Versioning'].get('Status') == 'Enabled':
            versioning_resources.append({
                'Name': bucket_name,
                'name_sanitized': bucket_name_sanitized,
                **bucket.get('Versioning', {})
            })
        
        # Create import entry for public access block if present
        if bucket.get('PublicAccessBlock'):
            public_access_resources.append({
                'Name': bucket_name,
                'name_sanitized': bucket_name_sanitized,
                **bucket.get('PublicAccessBlock', {})
            })

    # Generate Terraform files and import definitions for sub-resources
    sub_resources = [
        (
            "s3_bucket_versioning",
            versioning_resources,
            "aws_s3_bucket_versioning",
            "s3_bucket_versioning.tf",
            "S3 bucket versioning configurations",
        ),
        (
            "s3_bucket_public_access_block",
            public_access_resources,
            "aws_s3_bucket_public_access_block",
            "s3_bucket_public_access_block.tf",
            "S3 bucket public access blocks",
        ),
    ]

    for import_name, resources, resource_type, filename, description in sub_resources:
        if not resources:
            continue

        tf_file = output_dir / filename
        generate_tf(resources, resource_type, tf_file)
        generate_imports_file(
            import_name,
            resources,
            remote_resource_id_key="Name",
            output_dir=output_dir,
            provider="aws",
        )
        print(
            f"Generated Terraform for {len(resources)} {description} -> {tf_file}"
        )
        print(f"Generated import entries for {len(resources)} {description}")

def list_buckets(output_dir: Path):
    """Lists all S3 bucket resources previously generated."""
    ImportManager(output_dir, "s3_bucket").list_all()

def import_bucket(bucket_name: str, output_dir: Path):
    """Runs terraform import for a specific S3 bucket by name."""
    ImportManager(output_dir, "s3_bucket").find_and_import(bucket_name)
