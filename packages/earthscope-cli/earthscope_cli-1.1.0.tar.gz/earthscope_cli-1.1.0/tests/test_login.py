import pytest
from earthscope_sdk.config.models import Tokens
from earthscope_sdk.config.settings import SdkSettings

from earthscope_cli.main import app

from .util import get_m2m_creds, is_pipeline, missing_m2m_creds
from .conftest import runner


class TestLogout:
    def test_user_logout(self, device_flow_settings: SdkSettings):
        f = device_flow_settings.tokens_file

        # Create empty file to test logout deletes it
        device_flow_settings.profile_dir.mkdir(parents=True, exist_ok=True)
        f.touch()
        assert f.exists()

        result = runner.invoke(app, "logout")

        assert result.exit_code == 0
        assert not f.exists(), "credentials.json deleted"


class TestLogin:
    @pytest.mark.skipif(
        is_pipeline(),
        reason="No user input in pipeline",
    )
    def test_user_login_device_code_flow(self, device_flow_settings: SdkSettings):
        f = device_flow_settings.tokens_file
        assert not f.exists()

        result = runner.invoke(app, "login")
        assert result.exit_code == 0
        assert f.exists(), "credentials.json created"

        creds = Tokens.model_validate_json(f.read_bytes())
        assert creds.access_token is not None
        assert creds.refresh_token is not None
        assert creds.id_token is None

    @pytest.mark.skipif(
        missing_m2m_creds(),
        reason="Missing M2M credentials",
    )
    def test_user_login_client_credentials_flow(self, m2m_settings: SdkSettings):
        f = m2m_settings.tokens_file
        assert not f.exists()

        result = runner.invoke(
            app,
            "login",
            env=get_m2m_creds(),
        )
        assert result.exit_code == 0
        assert f.exists(), "credentials.json created"

        creds = Tokens.model_validate_json(f.read_bytes())
        assert creds.access_token is not None
        assert creds.refresh_token is None, "no refresh token for m2m"
        assert creds.id_token is None, "no ID token for m2m"
