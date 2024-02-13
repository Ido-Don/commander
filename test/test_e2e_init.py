import os.path
import shutil
import pytest
from typer.testing import CliRunner
from networkcommander.config import HOME_FOLDER
from networkcommander.main import app


@pytest.fixture
def runner():
    return CliRunner()


def test_frash_install(runner):
    commander_directory = os.path.join(HOME_FOLDER, ".commander")
    if os.path.isdir(commander_directory):
        shutil.rmtree(commander_directory)
    result = runner.invoke(app, ["init"], input="123")
    assert result.exit_code == 0
    assert f"creating a new database in {commander_directory}" in result.stdout
    assert "finished the initialization process, have a great day" in result.stdout
