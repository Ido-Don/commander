import os.path
import os.path
import shutil

import pytest
from typer.testing import CliRunner

from networkcommander.config import config
from networkcommander.main import app


@pytest.fixture
def runner():
    return CliRunner()


def test_frash_install(runner):
    if os.path.isdir(config["commander_directory"]):
        shutil.rmtree(config["commander_directory"])
    result = runner.invoke(app, ["init"], input="123")
    assert result.exit_code == 0
    assert f"creating a new database in {config['commander_directory']}" in result.stdout
    assert "finished the initialization process, have a great day" in result.stdout


def test_reinitialize(runner):
    if not os.path.isdir(config["commander_directory"]):
        os.mkdir(config["commander_directory"])
        open(config["keepass_db_path"])
    result = runner.invoke(app, ["init"], input="y\n123")
    assert result.exit_code == 0
    assert "commander is already initialized" in result.stdout
    assert f"creating a new database in {config['commander_directory']}" in result.stdout
    assert "finished the initialization process, have a great day" in result.stdout
