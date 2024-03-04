import pytest
from typer.testing import CliRunner

from mocks import get_test_device
from networkcommander.main import app
from test_keepass import KEEPASS_PASSWORD


@pytest.fixture
def runner():
    return CliRunner()


def test_add_device_with_cli_arguments(runner):
    devices = [
        get_test_device(),
        get_test_device(),
        get_test_device()
    ]
    result = runner.invoke(app, ["device", "add", *map(str, devices)], input='\n\n' + KEEPASS_PASSWORD + '\n')
    print(result.stdout)
    assert result.exit_code == 0
    assert f"added {len(devices)} to database" in result.stdout
