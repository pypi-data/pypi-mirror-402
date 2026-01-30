import pytest
from klinkfinance_sdk import KlinkSDK
from klinkfinance_sdk.types.exceptions import KlinkConfigException

def test_create_instance_missing_config():
    with pytest.raises(KlinkConfigException):
        KlinkSDK.create({})

def test_create_instance_invalid_health_check(mocker):
    # Mock the health check to fail or verify it attempts connection
    pass
