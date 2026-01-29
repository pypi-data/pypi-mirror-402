import pytest
from types import SimpleNamespace
from unittest.mock import patch

from terraback.cli.azure.compute.disks import get_disk_data


@patch('terraback.cli.azure.resource_processor.should_filter_resource')
@patch('terraback.cli.azure.compute.disks.ComputeManagementClient')
@patch('terraback.cli.azure.compute.disks.get_cached_azure_session')
def test_get_disk_data_processes_resources(mock_session, mock_client, mock_filter):
    mock_session.return_value = {}

    disk1 = SimpleNamespace(
        name='disk one',
        id='/subscriptions/1/resourceGroups/rg1/providers/Microsoft.Compute/disks/disk-one',
        location='eastus',
        tags=None,
        sku=None,
        creation_data=None,
        disk_size_gb=10,
        os_type=None,
        hyper_v_generation=None,
        zones=None,
        disk_iops_read_write=None,
        disk_m_bps_read_write=None,
        tier=None,
        disk_access_id=None,
        network_access_policy=None,
        bursting_enabled=None,
        encryption=None,
        security_profile=None,
        disk_state='Unattached',
        provisioning_state='Succeeded',
        encryption_settings_collection=None,
    )

    disk2 = SimpleNamespace(
        name='skip disk',
        id='/subscriptions/1/resourceGroups/rg1/providers/Microsoft.Compute/disks/skip-disk',
        location='eastus',
        tags=None,
        sku=None,
        creation_data=None,
        disk_size_gb=10,
        os_type=None,
        hyper_v_generation=None,
        zones=None,
        disk_iops_read_write=None,
        disk_m_bps_read_write=None,
        tier=None,
        disk_access_id=None,
        network_access_policy=None,
        bursting_enabled=None,
        encryption=None,
        security_profile=None,
        disk_state='Unattached',
        provisioning_state='Succeeded',
        encryption_settings_collection=None,
    )

    mock_client.return_value.disks.list.return_value = [disk1, disk2]

    def filter_func(resource_type, resource):
        return resource.get('name') == 'skip disk'

    mock_filter.side_effect = filter_func

    disks = get_disk_data('sub123')

    assert len(disks) == 1
    assert disks[0]['name'] == 'disk one'
    assert disks[0]['name_sanitized'] == 'disk_one'
