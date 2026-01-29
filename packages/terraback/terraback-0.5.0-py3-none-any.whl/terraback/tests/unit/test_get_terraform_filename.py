from terraback.terraform_generator.writer import get_terraform_filename


def test_get_terraform_filename_azure_sql_server():
    assert get_terraform_filename("azure_sql_server") == "mssql_server.tf"


def test_get_terraform_filename_azure_sql_database():
    assert get_terraform_filename("azure_sql_database") == "mssql_database.tf"


def test_get_terraform_filename_azure_sql_elastic_pool():
    assert get_terraform_filename("azure_sql_elastic_pool") == "mssql_elasticpool.tf"


def test_get_terraform_filename_azure_app_service_plan():
    assert get_terraform_filename("azure_app_service_plan") == "service_plan.tf"


def test_get_terraform_filename_azure_virtual_machine():
    assert get_terraform_filename("azure_virtual_machine") == "linux_virtual_machine.tf"
