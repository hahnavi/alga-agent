"""Tests for gateway configuration management."""

import os
from unittest.mock import patch

from gateway.config import (
    GatewayConfig,
    HomeChannel,
    Platform,
    PlatformConfig,
    SessionResetPolicy,
    StreamingConfig,
    _apply_env_overrides,
    load_gateway_config,
)


class TestHomeChannelRoundtrip:
    def test_to_dict_from_dict(self):
        hc = HomeChannel(platform=Platform.TELEGRAM, chat_id="999", name="general")
        d = hc.to_dict()
        restored = HomeChannel.from_dict(d)

        assert restored.platform == Platform.TELEGRAM
        assert restored.chat_id == "999"
        assert restored.name == "general"


class TestPlatformConfigRoundtrip:
    def test_to_dict_from_dict(self):
        pc = PlatformConfig(
            enabled=True,
            token="tok_123",
            home_channel=HomeChannel(
                platform=Platform.TELEGRAM,
                chat_id="555",
                name="Home",
            ),
            extra={"foo": "bar"},
        )
        d = pc.to_dict()
        restored = PlatformConfig.from_dict(d)

        assert restored.enabled is True
        assert restored.token == "tok_123"
        assert restored.home_channel.chat_id == "555"
        assert restored.extra == {"foo": "bar"}

    def test_disabled_no_token(self):
        pc = PlatformConfig()
        d = pc.to_dict()
        restored = PlatformConfig.from_dict(d)
        assert restored.enabled is False
        assert restored.token is None

    def test_from_dict_coerces_quoted_false_enabled(self):
        restored = PlatformConfig.from_dict({"enabled": "false"})
        assert restored.enabled is False

    def test_gateway_restart_notification_defaults_true(self):
        assert PlatformConfig().gateway_restart_notification is True
        assert PlatformConfig.from_dict({}).gateway_restart_notification is True

    def test_gateway_restart_notification_roundtrip_false(self):
        pc = PlatformConfig(enabled=True, gateway_restart_notification=False)
        restored = PlatformConfig.from_dict(pc.to_dict())
        assert restored.gateway_restart_notification is False

    def test_gateway_restart_notification_coerces_quoted_false(self):
        restored = PlatformConfig.from_dict({"gateway_restart_notification": "false"})
        assert restored.gateway_restart_notification is False


class TestGetConnectedPlatforms:
    def test_returns_enabled_with_token(self):
        config = GatewayConfig(
            platforms={
                Platform.TELEGRAM: PlatformConfig(enabled=True, token="t"),
            },
        )
        connected = config.get_connected_platforms()
        assert Platform.TELEGRAM in connected

    def test_empty_platforms(self):
        config = GatewayConfig()
        assert config.get_connected_platforms() == []


class TestSessionResetPolicy:
    def test_roundtrip(self):
        policy = SessionResetPolicy(mode="idle", at_hour=6, idle_minutes=120)
        d = policy.to_dict()
        restored = SessionResetPolicy.from_dict(d)
        assert restored.mode == "idle"
        assert restored.at_hour == 6
        assert restored.idle_minutes == 120

    def test_defaults(self):
        policy = SessionResetPolicy()
        assert policy.mode == "both"
        assert policy.at_hour == 4
        assert policy.idle_minutes == 1440

    def test_from_dict_treats_null_values_as_defaults(self):
        restored = SessionResetPolicy.from_dict(
            {"mode": None, "at_hour": None, "idle_minutes": None}
        )
        assert restored.mode == "both"
        assert restored.at_hour == 4
        assert restored.idle_minutes == 1440

    def test_from_dict_coerces_quoted_false_notify(self):
        restored = SessionResetPolicy.from_dict({"notify": "false"})
        assert restored.notify is False


class TestStreamingConfig:
    def test_defaults_to_edit_transport(self):
        restored = StreamingConfig.from_dict({"enabled": "true"})
        assert restored.transport == "edit"

    def test_from_dict_coerces_quoted_false_enabled(self):
        restored = StreamingConfig.from_dict({"enabled": "false"})
        assert restored.enabled is False

    def test_from_dict_malformed_numeric_values_fall_back_to_defaults(self):
        restored = StreamingConfig.from_dict(
            {
                "edit_interval": "oops",
                "buffer_threshold": "oops",
                "fresh_final_after_seconds": "oops",
            }
        )
        assert restored.edit_interval == 0.8
        assert restored.buffer_threshold == 24
        assert restored.fresh_final_after_seconds == 60.0


class TestGatewayConfigRoundtrip:
    def test_full_roundtrip(self):
        config = GatewayConfig(
            platforms={
                Platform.TELEGRAM: PlatformConfig(
                    enabled=True,
                    token="tok_123",
                    home_channel=HomeChannel(Platform.TELEGRAM, "123", "Home"),
                ),
            },
            reset_triggers=["/new"],
            quick_commands={"limits": {"type": "exec", "command": "echo ok"}},
            group_sessions_per_user=False,
            thread_sessions_per_user=True,
        )
        d = config.to_dict()
        restored = GatewayConfig.from_dict(d)

        assert Platform.TELEGRAM in restored.platforms
        assert restored.platforms[Platform.TELEGRAM].token == "tok_123"
        assert restored.reset_triggers == ["/new"]
        assert restored.quick_commands == {"limits": {"type": "exec", "command": "echo ok"}}
        assert restored.group_sessions_per_user is False
        assert restored.thread_sessions_per_user is True

    def test_roundtrip_preserves_unauthorized_dm_behavior(self):
        config = GatewayConfig(
            unauthorized_dm_behavior="ignore",
            platforms={
                Platform.TELEGRAM: PlatformConfig(
                    enabled=True,
                    extra={"unauthorized_dm_behavior": "pair"},
                ),
            },
        )

        restored = GatewayConfig.from_dict(config.to_dict())

        assert restored.unauthorized_dm_behavior == "ignore"
        assert restored.platforms[Platform.TELEGRAM].extra["unauthorized_dm_behavior"] == "pair"

    def test_from_dict_coerces_quoted_false_always_log_local(self):
        restored = GatewayConfig.from_dict({"always_log_local": "false"})
        assert restored.always_log_local is False

    def test_get_notice_delivery_defaults_to_public(self):
        config = GatewayConfig(
            platforms={Platform.TELEGRAM: PlatformConfig(enabled=True, token="***")}
        )

        assert config.get_notice_delivery(Platform.TELEGRAM) == "public"

    def test_get_notice_delivery_honors_platform_override(self):
        config = GatewayConfig(
            platforms={
                Platform.TELEGRAM: PlatformConfig(
                    enabled=True,
                    token="***",
                    extra={"notice_delivery": "private"},
                ),
            }
        )

        assert config.get_notice_delivery(Platform.TELEGRAM) == "private"


class TestLoadGatewayConfig:
    def test_bridges_quick_commands_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "quick_commands:\n"
            "  limits:\n"
            "    type: exec\n"
            "    command: echo ok\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.quick_commands == {"limits": {"type": "exec", "command": "echo ok"}}

    def test_bridges_group_sessions_per_user_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text("group_sessions_per_user: false\n", encoding="utf-8")

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.group_sessions_per_user is False

    def test_bridges_thread_sessions_per_user_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text("thread_sessions_per_user: true\n", encoding="utf-8")

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.thread_sessions_per_user is True

    def test_thread_sessions_per_user_defaults_to_false(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text("{}\n", encoding="utf-8")

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.thread_sessions_per_user is False

    def test_bridges_quoted_false_platform_enabled_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  enabled: \"false\"\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.platforms[Platform.TELEGRAM].enabled is False

    def test_bridges_nested_gateway_platforms_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "gateway:\n"
            "  platforms:\n"
            "    telegram:\n"
            "      enabled: true\n"
            "      token: nested-token\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert Platform.TELEGRAM in config.platforms
        assert config.platforms[Platform.TELEGRAM].enabled is True
        assert config.platforms[Platform.TELEGRAM].token == "nested-token"

    def test_top_level_platforms_override_nested_gateway_platforms(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  token: top-level-token\n"
            "gateway:\n"
            "  platforms:\n"
            "    telegram:\n"
            "      token: nested-token\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.platforms[Platform.TELEGRAM].token == "top-level-token"

    def test_bridges_quoted_false_session_notify_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "gateway:\n"
            "  default_reset_policy:\n"
            "    notify: \"false\"\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.default_reset_policy.notify is False

    def test_bridges_quoted_false_always_log_local_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "gateway:\n"
            "  always_log_local: \"false\"\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.always_log_local is False

    def test_bridges_telegram_channel_prompts_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  channel_prompts:\n"
            '    "-1001234567": Research assistant\n'
            "    789: Creative writing\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.platforms[Platform.TELEGRAM].extra["channel_prompts"] == {
            "-1001234567": "Research assistant",
            "789": "Creative writing",
        }

    def test_invalid_quick_commands_in_config_yaml_are_ignored(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text("quick_commands: not-a-mapping\n", encoding="utf-8")

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.quick_commands == {}

    def test_bridges_unauthorized_dm_behavior_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "unauthorized_dm_behavior: ignore\n"
            "telegram:\n"
            "  unauthorized_dm_behavior: pair\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.unauthorized_dm_behavior == "ignore"
        assert config.platforms[Platform.TELEGRAM].extra["unauthorized_dm_behavior"] == "pair"

    def test_bridges_telegram_disable_link_previews_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  disable_link_previews: true\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert config.platforms[Platform.TELEGRAM].extra["disable_link_previews"] is True

    def test_bridges_telegram_extra_base_url_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  extra:\n"
            "    base_url: https://custom-proxy.example.com/bot\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))

        config = load_gateway_config()

        assert (
            config.platforms[Platform.TELEGRAM].extra["base_url"]
            == "https://custom-proxy.example.com/bot"
        )

    def test_bridges_telegram_proxy_url_from_config_yaml(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  proxy_url: socks5://127.0.0.1:1080\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))
        monkeypatch.delenv("TELEGRAM_PROXY", raising=False)

        load_gateway_config()

        import os
        assert os.environ.get("TELEGRAM_PROXY") == "socks5://127.0.0.1:1080"

    def test_telegram_proxy_env_takes_precedence_over_config(self, tmp_path, monkeypatch):
        alga_home = tmp_path / ".alga"
        alga_home.mkdir()
        config_path = alga_home / "config.yaml"
        config_path.write_text(
            "telegram:\n"
            "  proxy_url: http://from-config:8080\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("ALGA_HOME", str(alga_home))
        monkeypatch.setenv("TELEGRAM_PROXY", "socks5://from-env:1080")

        load_gateway_config()

        import os
        assert os.environ.get("TELEGRAM_PROXY") == "socks5://from-env:1080"


class TestHomeChannelEnvOverrides:
    """Home channel env vars should apply even when the platform was already
    configured via config.yaml (not just when credential env vars create it)."""

    def test_existing_platform_configs_accept_home_channel_env_overrides(self):
        cases = [
            (
                Platform.TELEGRAM,
                PlatformConfig(enabled=True, token="telegram-token"),
                {"TELEGRAM_HOME_CHANNEL": "12345", "TELEGRAM_HOME_CHANNEL_NAME": "Home"},
                ("12345", "Home"),
            ),
        ]

        for platform, platform_config, env, expected in cases:
            config = GatewayConfig(platforms={platform: platform_config})
            with patch.dict(os.environ, env, clear=True):
                _apply_env_overrides(config)

            home = config.platforms[platform].home_channel
            assert home is not None, f"{platform.value}: home_channel should not be None"
            assert (home.chat_id, home.name) == expected, platform.value
