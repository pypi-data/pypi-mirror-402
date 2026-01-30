"""Tests for CLI config module."""

import os
import tempfile
from datetime import datetime, timedelta
from unittest.mock import patch


def test_load_config_missing_file():
    """Test that missing config file returns defaults."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"HE_CLI_CONFIG_DIR": tmpdir}):
            from human_eval.config import load_config

            config = load_config()
            assert config.server.url == ""
            assert config.auth.api_key == ""
            assert not config.is_authenticated()
            assert not config.has_server()


def test_save_and_load_config():
    """Test saving and loading config."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"HE_CLI_CONFIG_DIR": tmpdir}):
            from human_eval.config import (
                Config,
                AuthConfig,
                ServerConfig,
                load_config,
                save_config,
            )

            # Save config
            config = Config(
                server=ServerConfig(url="https://test.example.com"),
                auth=AuthConfig(
                    api_key="sk-test123",
                    expires_at=datetime.now() + timedelta(days=30),
                    user_email="test@example.com",
                    user_name="Test User",
                ),
            )
            save_config(config)

            # Load it back
            loaded = load_config()
            assert loaded.server.url == "https://test.example.com"
            assert loaded.auth.api_key == "sk-test123"
            assert loaded.auth.user_email == "test@example.com"
            assert loaded.auth.user_name == "Test User"


def test_is_authenticated_with_valid_key():
    """Test is_authenticated with valid, non-expired key."""
    from human_eval.config import AuthConfig, Config, ServerConfig

    config = Config(
        server=ServerConfig(url="https://test.example.com"),
        auth=AuthConfig(
            api_key="sk-test123",
            expires_at=datetime.now() + timedelta(days=1),
        ),
    )
    assert config.is_authenticated()


def test_is_authenticated_with_expired_key():
    """Test is_authenticated with expired key."""
    from human_eval.config import AuthConfig, Config, ServerConfig

    config = Config(
        server=ServerConfig(url="https://test.example.com"),
        auth=AuthConfig(
            api_key="sk-test123",
            expires_at=datetime.now() - timedelta(days=1),
        ),
    )
    assert not config.is_authenticated()


def test_is_authenticated_without_key():
    """Test is_authenticated without key."""
    from human_eval.config import AuthConfig, Config, ServerConfig

    config = Config(
        server=ServerConfig(url="https://test.example.com"),
        auth=AuthConfig(),
    )
    assert not config.is_authenticated()


def test_set_server_url():
    """Test set_server_url helper."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"HE_CLI_CONFIG_DIR": tmpdir}):
            from human_eval.config import load_config, set_server_url

            set_server_url("https://api.example.com/")

            config = load_config()
            # Should strip trailing slash
            assert config.server.url == "https://api.example.com"


def test_clear_auth():
    """Test clear_auth helper."""
    with tempfile.TemporaryDirectory() as tmpdir:
        with patch.dict(os.environ, {"HE_CLI_CONFIG_DIR": tmpdir}):
            from human_eval.config import clear_auth, load_config, set_auth

            # Set auth
            set_auth(
                api_key="sk-test",
                user_email="test@example.com",
                user_name="Test",
            )
            assert load_config().auth.api_key == "sk-test"

            # Clear it
            clear_auth()
            config = load_config()
            assert config.auth.api_key == ""
            assert config.auth.user_email == ""
