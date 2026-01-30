"""Tests for CLI commands."""

from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from basyx_client.cli.main import app
from basyx_client.pagination import PaginatedResult

runner = CliRunner()


class MockShell:
    """Mock AAS shell object."""

    def __init__(self, id: str, id_short: str):
        self.id = id
        self.id_short = id_short
        self.asset_information = type(
            "MockAssetInfo",
            (),
            {"global_asset_id": f"urn:asset:{id_short}"},
        )()


class MockSubmodel:
    """Mock Submodel object."""

    def __init__(self, id: str, id_short: str):
        self.id = id
        self.id_short = id_short
        self.semantic_id = None
        self.submodel_element = []


class MockProperty:
    """Mock Property element."""

    def __init__(self, id_short: str, value: str, value_type: str = "xs:string"):
        self.id_short = id_short
        self.value = value
        self.value_type = value_type


@pytest.fixture
def mock_client():
    """Create a mock AASClient."""
    with patch("basyx_client.cli.config.AASClient") as mock:
        client = MagicMock()
        mock.return_value.__enter__ = MagicMock(return_value=client)
        mock.return_value.__exit__ = MagicMock(return_value=False)
        yield client


class TestCLIBasic:
    """Test basic CLI functionality."""

    def test_version(self):
        """Test --version flag."""
        result = runner.invoke(app, ["--version"])
        assert result.exit_code == 0
        assert "basyx-client" in result.stdout

    def test_help(self):
        """Test --help flag."""
        result = runner.invoke(app, ["--help"])
        assert result.exit_code == 0
        assert "shells" in result.stdout
        assert "submodels" in result.stdout
        assert "elements" in result.stdout

    def test_shells_help(self):
        """Test shells subcommand help."""
        result = runner.invoke(app, ["shells", "--help"])
        assert result.exit_code == 0
        assert "list" in result.stdout
        assert "get" in result.stdout
        assert "create" in result.stdout
        assert "delete" in result.stdout


class TestShellsCommands:
    """Test shells commands."""

    def test_shells_list(self, mock_client):
        """Test basyx shells list."""
        mock_shells = [
            MockShell("urn:aas:1", "Shell1"),
            MockShell("urn:aas:2", "Shell2"),
        ]
        mock_client.shells.list.return_value = PaginatedResult(
            items=mock_shells,
            cursor=None,
            has_more=False,
        )

        result = runner.invoke(app, ["--url", "http://test:8081", "shells", "list"])
        assert result.exit_code == 0

    def test_shells_list_json(self, mock_client):
        """Test basyx shells list --format json."""
        mock_shells = [MockShell("urn:aas:1", "Shell1")]
        mock_client.shells.list.return_value = PaginatedResult(
            items=mock_shells,
            cursor=None,
            has_more=False,
        )

        result = runner.invoke(
            app,
            ["--format", "json", "--url", "http://test:8081", "shells", "list"],
        )
        assert result.exit_code == 0

    def test_shells_get(self, mock_client):
        """Test basyx shells get."""
        mock_client.shells.get.return_value = MockShell("urn:aas:1", "Shell1")

        result = runner.invoke(app, ["--url", "http://test:8081", "shells", "get", "urn:aas:1"])
        assert result.exit_code == 0


class TestSubmodelsCommands:
    """Test submodels commands."""

    def test_submodels_list(self, mock_client):
        """Test basyx submodels list."""
        mock_sms = [
            MockSubmodel("urn:sm:1", "Submodel1"),
            MockSubmodel("urn:sm:2", "Submodel2"),
        ]
        mock_client.submodels.list.return_value = PaginatedResult(
            items=mock_sms,
            cursor=None,
            has_more=False,
        )

        result = runner.invoke(app, ["--url", "http://test:8081", "submodels", "list"])
        assert result.exit_code == 0

    def test_submodels_get(self, mock_client):
        """Test basyx submodels get."""
        mock_sm = MockSubmodel("urn:sm:1", "Submodel1")
        mock_client.submodels.get.return_value = mock_sm

        result = runner.invoke(app, ["--url", "http://test:8081", "submodels", "get", "urn:sm:1"])
        assert result.exit_code == 0


class TestElementsCommands:
    """Test elements commands."""

    def test_elements_list(self, mock_client):
        """Test basyx elements list."""
        mock_elements = [
            MockProperty("Temp", "25.0", "xs:double"),
            MockProperty("Status", "OK", "xs:string"),
        ]
        mock_client.submodels.elements.list.return_value = PaginatedResult(
            items=mock_elements,
            cursor=None,
            has_more=False,
        )

        result = runner.invoke(app, ["--url", "http://test:8081", "elements", "list", "urn:sm:1"])
        assert result.exit_code == 0

    def test_elements_get_value(self, mock_client):
        """Test basyx elements get-value."""
        mock_client.submodels.elements.get_value.return_value = 25.5

        result = runner.invoke(
            app,
            ["--url", "http://test:8081", "elements", "get-value", "urn:sm:1", "Temperature"],
        )
        assert result.exit_code == 0

    def test_elements_set_value(self, mock_client):
        """Test basyx elements set-value."""
        result = runner.invoke(
            app,
            [
                "--url",
                "http://test:8081",
                "elements",
                "set-value",
                "urn:sm:1",
                "Temperature",
                "30.0",
            ],
        )
        assert result.exit_code == 0
        mock_client.submodels.elements.set_value.assert_called_once()


class TestConfigCommands:
    """Test config commands."""

    def test_config_show(self):
        """Test basyx config show."""
        result = runner.invoke(app, ["config", "show"])
        assert result.exit_code == 0

    def test_config_profiles(self):
        """Test basyx config profiles."""
        result = runner.invoke(app, ["config", "profiles"])
        assert result.exit_code == 0


class TestOutputFormats:
    """Test output format options."""

    def test_format_table(self, mock_client):
        """Test table output format."""
        mock_client.shells.list.return_value = PaginatedResult(
            items=[MockShell("urn:aas:1", "Shell1")],
            cursor=None,
            has_more=False,
        )

        result = runner.invoke(
            app,
            ["--format", "table", "--url", "http://test:8081", "shells", "list"],
        )
        assert result.exit_code == 0

    def test_format_yaml(self, mock_client):
        """Test YAML output format."""
        mock_client.shells.list.return_value = PaginatedResult(
            items=[MockShell("urn:aas:1", "Shell1")],
            cursor=None,
            has_more=False,
        )

        result = runner.invoke(
            app,
            ["--format", "yaml", "--url", "http://test:8081", "shells", "list"],
        )
        assert result.exit_code == 0


class TestErrorHandling:
    """Test error handling."""

    def test_connection_error(self, mock_client):
        """Test handling of connection errors."""
        from basyx_client.exceptions import ConnectionError

        mock_client.shells.list.side_effect = ConnectionError("Connection refused")

        result = runner.invoke(app, ["--url", "http://test:8081", "shells", "list"])
        assert result.exit_code == 1
        assert "Failed" in result.stdout or "Connection" in result.stdout

    def test_not_found_error(self, mock_client):
        """Test handling of not found errors."""
        from basyx_client.exceptions import ResourceNotFoundError

        mock_client.shells.get.side_effect = ResourceNotFoundError("Not found")

        result = runner.invoke(app, ["--url", "http://test:8081", "shells", "get", "nonexistent"])
        assert result.exit_code == 1
