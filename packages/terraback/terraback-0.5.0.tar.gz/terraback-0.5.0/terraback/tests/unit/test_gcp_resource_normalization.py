from terraback.terraform_generator.imports import normalize_terraform_resource_type
import pytest


@pytest.mark.parametrize(
    "resource_type,expected",
    [
        ("gcp_cloud_run_service", "google_cloud_run_service"),
        ("gcp_memorystore_redis", "google_redis_instance"),
        ("gcp_memorystore_memcached", "google_memcache_instance"),
        ("gcp_backend_buckets", "google_compute_backend_bucket"),
        ("gcp_api_gateway_api", "google_api_gateway_api"),
        ("gcp_certificate", "google_certificate_manager_certificate"),
        ("gcp_certificate_map", "google_certificate_manager_certificate_map"),
        ("gcp_certificate_manager_certificate", "google_certificate_manager_certificate"),
        ("gcp_certificate_manager_certificate_map", "google_certificate_manager_certificate_map"),
        ("gcp_cloud_function", "google_cloudfunctions_function"),
        ("gcp_cloudfunctions_function", "google_cloudfunctions_function"),
        ("gcp_cloud_tasks_queue", "google_cloud_tasks_queue"),
        ("gcp_container_registry", "google_container_registry"),
        ("gcp_container_registries", "google_container_registry"),
        ("gcp_dns_managed_zones", "google_dns_managed_zone"),
        ("gcp_eventarc_trigger", "google_eventarc_trigger"),
        ("gcp_firestore_database", "google_firestore_database"),
        ("gcp_health_check", "google_compute_health_check"),
        ("gcp_image", "google_compute_image"),
        ("gcp_instance_group", "google_compute_instance_group"),
        ("gcp_instance_template", "google_compute_instance_template"),
        ("gcp_kms_crypto_key", "google_kms_crypto_key"),
        ("gcp_kms_key_ring", "google_kms_key_ring"),
        ("gcp_monitoring_alert_policies", "google_monitoring_alert_policy"),
        ("gcp_router", "google_compute_router"),
        ("gcp_service_account", "google_service_account"),
        ("gcp_service_accounts", "google_service_account"),
        ("gcp_snapshot", "google_compute_snapshot"),
        ("gcp_spanner_instance", "google_spanner_instance"),
        ("gcp_vpn_gateway", "google_compute_vpn_gateway"),
        ("gcp_workflows_workflow", "google_workflows_workflow"),
        ("gcp_workflows", "google_workflows_workflow"),
        ("gcp_bucket_iam_binding", "google_storage_bucket_iam_binding"),
        ("gcp_bigtable_instance", "google_bigtable_instance"),
        ("gcp_binary_authorization_policy", "google_binary_authorization_policy"),
        ("gcp_certificate_authority", "google_privateca_certificate_authority"),
        ("gcp_iam_roles", "google_project_iam_custom_role"),
    ],
)
def test_gcp_resource_normalization(resource_type, expected):
    assert normalize_terraform_resource_type(resource_type, provider="gcp") == expected
