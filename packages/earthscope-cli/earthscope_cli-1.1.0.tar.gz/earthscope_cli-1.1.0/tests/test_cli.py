from unittest.mock import MagicMock

import pytest
from earthscope_sdk import __version__ as sdk_version
from earthscope_sdk.config.settings import SdkSettings

from earthscope_cli import __version__ as cli_version
from earthscope_cli.main import app
from tests.conftest import runner


class TestCli:
    def test_version(self):
        result = runner.invoke(app, "--version")
        assert result.exit_code == 0
        assert (
            result.stdout.strip()
            == f"earthscope-cli/{cli_version} earthscope-sdk/{sdk_version}"
        )


class TestCliCleanup:
    def test_sdk_context_manager(self, monkeypatch: pytest.MonkeyPatch):
        """Verify the CLI uses the SDK as a context manager."""
        mock = MagicMock()

        monkeypatch.setattr("earthscope_sdk.EarthScopeClient.__enter__", mock.__enter__)
        monkeypatch.setattr("earthscope_sdk.EarthScopeClient.__exit__", mock.__exit__)

        result = runner.invoke(app, ["debug", "get-settings"])
        assert result.exit_code == 0

        assert SdkSettings.model_validate_json(result.output)

        mock.__enter__.assert_called_once()
        mock.__exit__.assert_called_once()

    def test_sdk_closed_on_error(self, monkeypatch: pytest.MonkeyPatch):
        """Verify the SDK is closed even when an exception is raised."""
        mock_instance = MagicMock()
        mock_instance.ctx.settings.model_dump_json.side_effect = ValueError(
            "Test error"
        )

        mock_class = MagicMock(return_value=mock_instance)
        monkeypatch.setattr("earthscope_sdk.EarthScopeClient", mock_class)

        result = runner.invoke(app, ["debug", "get-settings"])
        assert result.exit_code == 1
        assert result.exception is not None
        assert result.exception.args[0] == "Test error"

        mock_instance.__enter__.assert_called_once()
        mock_instance.__exit__.assert_called_once()
