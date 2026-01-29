from types import SimpleNamespace
from unittest.mock import patch, Mock
from pathlib import Path

from terraback.cli.azure.dns.dns_records import DnsRecordsScanner, scan_dns_records


@patch('terraback.cli.azure.resource_processor.should_filter_resource')
@patch('terraback.cli.azure.dns.dns_records.DnsManagementClient')
def test_list_dns_records_processes_resources(mock_client, mock_filter):
    zone = SimpleNamespace(
        id='/subscriptions/1/resourceGroups/rg1/providers/Microsoft.Network/dnszones/example.com',
        name='example.com'
    )

    record1 = SimpleNamespace(
        id='/subscriptions/1/resourceGroups/rg1/providers/Microsoft.Network/dnszones/example.com/A/www',
        name='www',
        type='Microsoft.Network/dnszones/A',
        ttl=300,
        a_records=[SimpleNamespace(ipv4_address='1.2.3.4')],
        aaaa_records=None,
        caa_records=None,
        cname_record=None,
        mx_records=None,
        ns_records=None,
        ptr_records=None,
        srv_records=None,
        txt_records=None,
        metadata=None,
        target_resource=None,
    )

    record2 = SimpleNamespace(
        id='/subscriptions/1/resourceGroups/rg1/providers/Microsoft.Network/dnszones/example.com/A/skip',
        name='skip',
        type='Microsoft.Network/dnszones/A',
        ttl=300,
        a_records=[SimpleNamespace(ipv4_address='5.6.7.8')],
        aaaa_records=None,
        caa_records=None,
        cname_record=None,
        mx_records=None,
        ns_records=None,
        ptr_records=None,
        srv_records=None,
        txt_records=None,
        metadata=None,
        target_resource=None,
    )

    mock_client.return_value.zones.list.return_value = [zone]
    mock_client.return_value.record_sets.list_by_dns_zone.return_value = [record1, record2]

    def filter_func(resource_type, resource):
        return resource.get('name') == 'skip_example_com_A'

    mock_filter.side_effect = filter_func

    scanner = DnsRecordsScanner(credentials=Mock(), subscription_id='sub123')
    records = scanner.list_dns_records()

    assert len(records) == 1
    assert records[0]['name'] == 'www_example_com_A'
    assert records[0]['name_sanitized'] == 'www_example_com_a'


@patch('terraback.core.license.check_feature_access', return_value=True)
@patch('terraback.terraform_generator.imports.generate_imports_file')
@patch('terraback.terraform_generator.writer.generate_tf_auto')
@patch('terraback.cli.azure.dns.dns_records.DnsRecordsScanner')
def test_scan_dns_records_generates_imports_per_type(mock_scanner_cls, mock_tf, mock_imports, _):
    """Ensure import files are generated separately for each DNS record type."""
    mock_scanner = Mock()
    mock_scanner.scan.return_value = [
        {'id': '1', 'resource_type': 'azure_dns_a_record'},
        {'id': '2', 'resource_type': 'azure_dns_cname_record'},
        {'id': '3', 'resource_type': 'azure_dns_a_record'},
    ]
    mock_scanner_cls.return_value = mock_scanner

    output_dir = Path('out')
    result = scan_dns_records(output_dir, 'sub123')

    assert len(result) == 3
    assert mock_imports.call_count == 2
    resource_types = {call.args[0] for call in mock_imports.call_args_list}
    assert resource_types == {'azure_dns_a_record', 'azure_dns_cname_record'}
    for call in mock_imports.call_args_list:
        r_type = call.args[0]
        resources = call.args[1]
        assert all(r['resource_type'] == r_type for r in resources)
