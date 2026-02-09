from app.storage import build_storage_client


def test_build_storage_msp_prefix():
    client = build_storage_client(
        tenant_storage={"use_msp_storage": True},
        default_bucket="msp-bucket",
        default_region="us-east-1",
        default_endpoint="https://s3.example.com",
        default_access_key="AKIA",
        default_secret="SECRET",
        tenant_prefix="tenant-123",
        tenant_type="customer",
    )
    assert client.config.bucket == "msp-bucket"
    assert client.config.prefix == "tenants/tenant-123"


def test_build_storage_byo():
    client = build_storage_client(
        tenant_storage={
            "bucket": "custom",
            "region": "us-west-2",
            "endpoint": "https://s3.custom.com",
            "access_key": "X",
            "secret_key": "Y",
        },
        default_bucket="msp-bucket",
        default_region="us-east-1",
        default_endpoint="https://s3.example.com",
        default_access_key="AKIA",
        default_secret="SECRET",
        tenant_prefix="tenant-123",
        tenant_type="customer",
    )
    assert client.config.bucket == "custom"
    assert client.config.prefix == "tenant-123"


def test_build_storage_msp_internal_prefix():
    client = build_storage_client(
        tenant_storage={"use_msp_storage": True},
        default_bucket="msp-bucket",
        default_region="us-east-1",
        default_endpoint=None,
        default_access_key="AKIA",
        default_secret="SECRET",
        tenant_prefix="msp-tenant",
        tenant_type="internal_msp",
    )
    assert client.config.prefix == "msp/msp-tenant"
