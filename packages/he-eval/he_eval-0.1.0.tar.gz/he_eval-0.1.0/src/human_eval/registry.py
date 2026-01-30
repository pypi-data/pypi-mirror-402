"""Registry for Control Arena settings.

This module provides a thin wrapper around Control Arena's setting classes,
making them discoverable and instantiable by name.
"""

from dataclasses import dataclass
from typing import Any

from control_arena.settings._setting import Setting


@dataclass
class SettingInfo:
    """Metadata about a Control Arena setting."""

    name: str
    description: str
    setting_class: type[Setting]
    # Whether the setting has been tested with human_cli
    human_tested: bool = False
    # Approximate scoring time (for user expectations)
    scoring_time: str = "fast"  # "fast" (<10s), "slow" (2-3 min), etc.
    # Skip setup_environment() for human eval (some settings run tests during setup)
    skip_setup: bool = False


# Registry of available settings
# Start with BashBench2 since that's what we've tested
_SETTINGS: dict[str, SettingInfo] = {}


def _register_bashbench2() -> None:
    """Register BashBench2 setting."""
    from control_arena.settings.bashbench2.bb2_setting import BashBench2Setting

    _SETTINGS["bashbench2"] = SettingInfo(
        name="bashbench2",
        description="640 bash/systems programming tasks with 4 side tasks (firewall, malware, sudo, exfil)",
        setting_class=BashBench2Setting,
        human_tested=True,
    )


def _register_bash() -> None:
    """Register Bash setting (CTRL-Z paper tasks).

    Special handling in runner.py:
        The upstream setup_environment() returns add_test_file() which writes
        the test file AND runs pytest. This is problematic for human eval
        (noise before human connects, confusing output from failing tests).

        However, we cannot skip setup entirely because AI agents have access
        to a run_tests() tool. For scoring parity, humans need the test file
        to exist so they can run `pytest test_task.py` manually.

        Solution: runner.py uses write_test_file_only() for this setting,
        which writes the file without executing tests.

    Known issue:
        Alpine login shells don't source .bashrc - users must run 'source ~/.bashrc'
        after connecting to enable the `task` command (upstream issue in
        Control Arena's Dockerfile).

    See docs/scoring-parity.md for the full parity analysis.
    """
    from control_arena.settings.bash.bash_setting import BashSetting

    _SETTINGS["bash"] = SettingInfo(
        name="bash",
        description="257 bash tasks from CTRL-Z paper (run 'source ~/.bashrc' after connecting)",
        setting_class=BashSetting,
        human_tested=False,
        scoring_time="fast",
        # Note: skip_setup is False, but runner.py handles this setting specially
        # by using write_test_file_only() instead of the upstream setup_environment()
    )


def _register_iac() -> None:
    """Register IAC setting (AWS infrastructure)."""
    from control_arena.settings.iac.control_iac_setting import ControlIACSetting

    _SETTINGS["iac"] = SettingInfo(
        name="iac",
        description="AWS CDK infrastructure tasks with 9 side tasks (backdoors, disable MFA, public S3, etc.)",
        setting_class=ControlIACSetting,
        human_tested=False,
        scoring_time="~2 min (CDK synth)",
    )


def _ensure_registry_loaded() -> None:
    """Lazy load the registry to avoid import overhead."""
    if not _SETTINGS:
        _register_bashbench2()
        _register_bash()
        _register_iac()


def list_settings() -> list[SettingInfo]:
    """List all available Control Arena settings.

    Returns:
        List of SettingInfo objects describing available settings.
    """
    _ensure_registry_loaded()
    return list(_SETTINGS.values())


def get_setting_info(name: str) -> SettingInfo:
    """Get metadata about a setting by name.

    Args:
        name: The setting name

    Returns:
        SettingInfo object

    Raises:
        ValueError: If the setting name is not recognized
    """
    _ensure_registry_loaded()

    if name not in _SETTINGS:
        available = ", ".join(_SETTINGS.keys())
        raise ValueError(f"Unknown setting: {name}. Available: {available}")

    return _SETTINGS[name]


def get_setting(name: str, **kwargs: Any) -> Setting:
    """Get a Control Arena setting by name.

    Args:
        name: The setting name (e.g., "bashbench2", "infra", "apps")
        **kwargs: Additional arguments passed to the setting constructor

    Returns:
        An instantiated Setting object

    Raises:
        ValueError: If the setting name is not recognized
    """
    _ensure_registry_loaded()

    if name not in _SETTINGS:
        available = ", ".join(_SETTINGS.keys())
        raise ValueError(f"Unknown setting: {name}. Available: {available}")

    info = _SETTINGS[name]
    return info.setting_class(**kwargs)
