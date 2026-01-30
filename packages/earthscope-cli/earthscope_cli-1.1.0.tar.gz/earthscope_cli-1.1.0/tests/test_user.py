import time

import pytest
from earthscope_sdk.auth.error import NoRefreshTokenError, NoTokensError
from earthscope_sdk.config.models import AccessTokenBody, Tokens
from earthscope_sdk.config.settings import SdkSettings

from earthscope_cli.main import app

from .conftest import runner
from .util import (
    get_m2m_creds,
    get_refresh_token,
    missing_m2m_creds,
    missing_refresh_token,
)


class TestWithoutCreds:
    def test_get_access_token(self):
        result = runner.invoke(app, "user get-access-token".split())
        assert result.exit_code == 1
        assert isinstance(result.exception, NoTokensError)

    def test_get_access_token_body(self):
        result = runner.invoke(app, "user get-access-token-body".split())
        assert result.exit_code == 1
        assert isinstance(result.exception, NoTokensError)

    def test_get_refresh_token(self):
        result = runner.invoke(app, "user get-refresh-token".split())
        assert result.exit_code == 1
        assert isinstance(result.exception, NoTokensError)

    def test_revoke_refresh_token(self):
        result = runner.invoke(app, "user revoke-refresh-token".split())
        assert result.exit_code == 1
        assert isinstance(result.exception, NoTokensError)


# TODO: The override_local_app_dir fixture's scope is function level, so I can't do the setup class as a classmethod or with scope class as fixture
@pytest.fixture()
def m2m_login():
    result = runner.invoke(app, "login", env=get_m2m_creds())
    assert result.exit_code == 0


@pytest.mark.usefixtures("m2m_login")
@pytest.mark.skipif(
    missing_m2m_creds(),
    reason="Missing M2M credentials",
)
class TestWithM2MCreds:
    def test_get_access_token(self, m2m_settings: SdkSettings):
        f = m2m_settings.tokens_file
        creds = Tokens.model_validate_json(f.read_bytes())

        result = runner.invoke(
            app,
            "user get-access-token".split(),
            env=get_m2m_creds(),
        )
        assert result.exit_code == 0
        assert result.stdout.strip() == creds.access_token.get_secret_value()

    def test_get_access_token_body(self, m2m_settings: SdkSettings):
        f = m2m_settings.tokens_file
        creds = Tokens.model_validate_json(f.read_bytes())

        result = runner.invoke(
            app,
            "user get-access-token-body".split(),
            env=get_m2m_creds(),
        )
        assert result.exit_code == 0

        resp_body = AccessTokenBody.model_validate_json(result.stdout)
        assert resp_body == creds.access_token_body, "access token bodies match"

    def test_get_refresh_token(self):
        result = runner.invoke(
            app,
            "user get-refresh-token".split(),
            env=get_m2m_creds(),
        )
        assert result.exit_code == 1
        assert isinstance(result.exception, NoRefreshTokenError)

    def test_refresh_access_token(self, m2m_settings: SdkSettings):
        f = m2m_settings.tokens_file
        before_tokens = Tokens.model_validate_json(f.read_bytes())
        time.sleep(1)  # wait before refreshing so we don't get handed the same token

        result = runner.invoke(
            app,
            "user refresh-access-token".split(),
            env=get_m2m_creds(),
        )
        assert result.exit_code == 0

        after_tokens = Tokens.model_validate_json(f.read_bytes())

        assert (
            before_tokens.access_token.get_secret_value()
            != after_tokens.access_token.get_secret_value()
        )
        assert (
            before_tokens.access_token_body.issued_at
            <= after_tokens.access_token_body.issued_at
        )

    def test_revoke_refresh_token(self):
        result = runner.invoke(
            app,
            "user revoke-refresh-token".split(),
            env=get_m2m_creds(),
        )
        assert result.exit_code == 1
        assert isinstance(result.exception, NoRefreshTokenError)


@pytest.fixture()
def refresh_access_token():
    result = runner.invoke(
        app,
        "user refresh-access-token",
        env=get_refresh_token(),
    )
    assert result.exit_code == 0


@pytest.mark.usefixtures("refresh_access_token")
@pytest.mark.skipif(
    missing_refresh_token(),
    reason="Missing refresh token",
)
class TestWithRefreshToken:
    def test_get_access_token(self, refresh_settings: SdkSettings):
        f = refresh_settings.tokens_file
        creds = Tokens.model_validate_json(f.read_bytes())

        result = runner.invoke(
            app,
            "user get-access-token".split(),
            env=get_refresh_token(),
        )
        assert result.exit_code == 0
        assert result.stdout.strip() == creds.access_token.get_secret_value()

    def test_get_access_token_body(self, refresh_settings: SdkSettings):
        f = refresh_settings.tokens_file
        creds = Tokens.model_validate_json(f.read_bytes())

        result = runner.invoke(
            app,
            "user get-access-token-body".split(),
            env=get_refresh_token(),
        )
        assert result.exit_code == 0

        resp_body = AccessTokenBody.model_validate_json(result.stdout)
        assert resp_body == creds.access_token_body, "access token bodies match"

    def test_refresh_access_token(self, refresh_settings: SdkSettings):
        f = refresh_settings.tokens_file
        before_tokens = Tokens.model_validate_json(f.read_bytes())
        time.sleep(1)  # wait before refreshing so we don't get handed the same token

        result = runner.invoke(
            app,
            "user refresh-access-token".split(),
            env=get_refresh_token(),
        )
        assert result.exit_code == 0

        after_tokens = Tokens.model_validate_json(f.read_bytes())

        assert (
            before_tokens.access_token.get_secret_value()
            != after_tokens.access_token.get_secret_value()
        )
        assert (
            before_tokens.access_token_body.issued_at
            <= after_tokens.access_token_body.issued_at
        )

    def test_get_refresh_token(self):
        result = runner.invoke(
            app,
            "user get-refresh-token".split(),
            env=get_refresh_token(),
        )
        assert result.exit_code == 0
        assert result.stdout.strip() == get_refresh_token()["ES_OAUTH2__REFRESH_TOKEN"]

    @pytest.mark.skip(reason="Revoking the refresh token will break other tests")
    def test_revoke_refresh_token(self):
        pass
