"""Tests for the setup hooks command."""

import json
import re
import tempfile
from pathlib import Path
from unittest.mock import patch

from typer.testing import CliRunner

from runlayer_cli.commands.setup import Client
from runlayer_cli.config import Config, HostConfig
from runlayer_cli.main import app

runner = CliRunner()


def strip_ansi(text: str) -> str:
    """Strip ANSI escape codes from text."""
    ansi_escape = re.compile(r"\x1b\[[0-9;]*m")
    return ansi_escape.sub("", text)


def test_setup_hooks_help():
    """Test that setup hooks command shows help."""
    result = runner.invoke(app, ["setup", "hooks", "--help"])
    assert result.exit_code == 0
    plain_output = strip_ansi(result.stdout)
    assert "Install or uninstall Runlayer client hooks" in plain_output
    assert "--install" in plain_output
    assert "--uninstall" in plain_output
    assert "--secret" in plain_output
    assert "--host" in plain_output
    assert "--yes" in plain_output
    assert "cursor" in plain_output.lower()


def test_setup_hooks_install_all_clients():
    """Test that setup hooks installs to all clients when --client is not specified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--install",
                    "--yes",
                    "--secret",
                    "test-api-key",
                    "--host",
                    "https://app.runlayer.com",
                ],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Hooks installed" in plain_output

            # Verify hooks were installed
            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert hook_script.exists()


def test_setup_hooks_requires_action():
    """Test that setup hooks command requires --install or --uninstall."""
    result = runner.invoke(
        app,
        ["setup", "hooks", "--client", "cursor"],
    )
    assert result.exit_code != 0
    plain_output = strip_ansi(result.output)
    assert "Must specify either --install or --uninstall" in plain_output


def test_setup_hooks_install_uninstall_mutually_exclusive():
    """Test that --install and --uninstall cannot be used together."""
    result = runner.invoke(
        app,
        [
            "setup",
            "hooks",
            "--client",
            "cursor",
            "--install",
            "--uninstall",
            "--secret",
            "test-secret",
            "--host",
            "http://localhost:3000",
        ],
    )
    assert result.exit_code != 0
    plain_output = strip_ansi(result.output)
    assert "Cannot use both --install and --uninstall" in plain_output


def test_setup_hooks_install_requires_host_when_not_in_config():
    """Test that --install requires --host when not logged in."""
    with patch("runlayer_cli.config.load_config", return_value=Config()):
        result = runner.invoke(
            app,
            [
                "setup",
                "hooks",
                "--client",
                "cursor",
                "--install",
                "--yes",
            ],
        )
        assert result.exit_code != 0
        plain_output = strip_ansi(result.output)
        assert "No host configured" in plain_output


def test_setup_hooks_install_triggers_login_when_no_secret():
    """Test that --install triggers login flow when no secret is available."""
    config = Config(default_host="http://localhost:3000")
    with (
        patch("runlayer_cli.config.load_config", return_value=config),
        patch("runlayer_cli.commands.auth.login") as mock_login,
    ):
        mock_login.side_effect = SystemExit(1)

        result = runner.invoke(
            app,
            [
                "setup",
                "hooks",
                "--client",
                "cursor",
                "--install",
                "--yes",
            ],
        )
        assert result.exit_code != 0
        plain_output = strip_ansi(result.output)
        assert "No credentials found" in plain_output


def test_setup_hooks_invalid_client():
    """Test that setup hooks command rejects invalid client."""
    result = runner.invoke(
        app,
        [
            "setup",
            "hooks",
            "--client",
            "invalid-client",
            "--install",
            "--yes",
            "--secret",
            "test-secret",
            "--host",
            "http://localhost:3000",
        ],
    )
    assert result.exit_code != 0


def test_setup_hooks_install():
    """Test that --install installs hook files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--yes",
                    "--secret",
                    "test-api-key",
                    "--host",
                    "https://app.runlayer.com",
                ],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Hooks installed" in plain_output
            assert "Restart Cursor" in plain_output

            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert hook_script.exists()

            # Verify hook script contains the configured values
            hook_content = hook_script.read_text()
            assert "test-api-key" in hook_content
            assert "https://app.runlayer.com" in hook_content
            assert "__RUNLAYER_API_KEY__" not in hook_content
            assert "__RUNLAYER_API_HOST__" not in hook_content

            # Verify hooks.json was created
            hooks_json = client_dir / "hooks.json"
            assert hooks_json.exists()

            # Verify hooks.json has correct structure with MCP hooks only
            hooks_config = json.loads(hooks_json.read_text())
            assert hooks_config["version"] == 1
            expected_hooks = ["beforeMCPExecution"]
            assert len(hooks_config["hooks"]) == 1
            for hook_name in expected_hooks:
                assert hook_name in hooks_config["hooks"]
                assert (
                    str(hook_script) in hooks_config["hooks"][hook_name][0]["command"]
                )


def test_setup_hooks_install_creates_backup():
    """Test that --install backs up existing files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"
        hooks_dir = client_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create existing files
        existing_hook = hooks_dir / "runlayer-hook.sh"
        existing_hook.write_text("# existing hook")
        existing_json = client_dir / "hooks.json"
        existing_json.write_text('{"version": 0}')

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--yes",
                    "--secret",
                    "test-api-key",
                    "--host",
                    "https://app.runlayer.com",
                ],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Backed up" in plain_output

            # Verify backup files were created
            backup_files = list(hooks_dir.glob("runlayer-hook.backup_*.sh"))
            assert len(backup_files) == 1
            assert backup_files[0].read_text() == "# existing hook"

            json_backups = list(client_dir.glob("hooks.backup_*.json"))
            assert len(json_backups) == 1
            assert json_backups[0].read_text() == '{"version": 0}'


def test_setup_hooks_uninstall():
    """Test that --uninstall removes hook files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"
        hooks_dir = client_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create hook files
        hook_script = hooks_dir / "runlayer-hook.sh"
        hook_script.write_text("#!/bin/bash\necho test")
        hooks_json = client_dir / "hooks.json"
        hooks_json.write_text('{"version": 1}')

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                ["setup", "hooks", "--client", "cursor", "--uninstall", "--yes"],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Removed hook script" in plain_output
            assert "Removed hooks configuration" in plain_output
            assert "Restart Cursor" in plain_output

            # Verify files were removed
            assert not hook_script.exists()
            assert not hooks_json.exists()


def test_setup_hooks_uninstall_no_files():
    """Test --uninstall when no hooks are installed."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"
        client_dir.mkdir(parents=True)

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                ["setup", "hooks", "--client", "cursor", "--uninstall", "--yes"],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "No Runlayer hooks found" in plain_output


def test_setup_hooks_uninstall_all_clients():
    """Test that --uninstall removes hooks from all clients when --client is not specified."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"
        hooks_dir = client_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        # Create hook files
        hook_script = hooks_dir / "runlayer-hook.sh"
        hook_script.write_text("#!/bin/bash\necho test")
        hooks_json = client_dir / "hooks.json"
        hooks_json.write_text('{"version": 1}')

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                ["setup", "hooks", "--uninstall", "--yes"],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Removed hook script" in plain_output
            assert "Removed hooks configuration" in plain_output

            # Verify files were removed
            assert not hook_script.exists()
            assert not hooks_json.exists()


def test_setup_hooks_install_prompts_without_yes():
    """Test that --install prompts for confirmation without --yes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            # Test declining the prompt
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--secret",
                    "test-api-key",
                    "--host",
                    "https://app.runlayer.com",
                ],
                input="n\n",
            )

            plain_output = strip_ansi(result.output)
            assert result.exit_code == 0
            assert "Proceed with installation?" in plain_output
            assert "Aborted" in plain_output

            # Verify no files were created
            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert not hook_script.exists()


def test_setup_hooks_install_confirms_with_prompt():
    """Test that --install proceeds when user confirms."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--secret",
                    "test-api-key",
                    "--host",
                    "https://app.runlayer.com",
                ],
                input="y\n",
            )

            plain_output = strip_ansi(result.output)
            assert result.exit_code == 0
            assert "Hooks installed" in plain_output

            # Verify files were created
            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert hook_script.exists()


def test_setup_hooks_uninstall_prompts_without_yes():
    """Test that --uninstall prompts for confirmation without --yes."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"
        hooks_dir = client_dir / "hooks"
        hooks_dir.mkdir(parents=True)

        hook_script = hooks_dir / "runlayer-hook.sh"
        hook_script.write_text("#!/bin/bash\necho test")

        with patch.dict(
            "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
            {Client.CURSOR: client_dir},
        ):
            result = runner.invoke(
                app,
                ["setup", "hooks", "--client", "cursor", "--uninstall"],
                input="n\n",
            )

            plain_output = strip_ansi(result.output)
            assert result.exit_code == 0
            assert "Proceed with uninstallation?" in plain_output
            assert "Aborted" in plain_output

            # Verify file was NOT removed
            assert hook_script.exists()


def test_setup_hooks_install_uses_credentials_from_config():
    """Test that --install uses credentials from config file."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        config = Config(
            default_host="https://app.runlayer.com",
            hosts={
                "app.runlayer.com": HostConfig(
                    url="https://app.runlayer.com", secret="config-api-key"
                )
            },
        )

        with (
            patch.dict(
                "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
                {Client.CURSOR: client_dir},
            ),
            patch("runlayer_cli.config.load_config", return_value=config),
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--yes",
                ],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Hooks installed" in plain_output

            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert hook_script.exists()
            hook_content = hook_script.read_text()
            assert "config-api-key" in hook_content
            assert "https://app.runlayer.com" in hook_content


def test_setup_hooks_install_cli_args_override_config():
    """Test that CLI args override config file credentials."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        config = Config(
            default_host="https://app.runlayer.com",
            hosts={
                "app.runlayer.com": HostConfig(
                    url="https://app.runlayer.com", secret="config-api-key"
                )
            },
        )

        with (
            patch.dict(
                "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
                {Client.CURSOR: client_dir},
            ),
            patch("runlayer_cli.config.load_config", return_value=config),
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--yes",
                    "--secret",
                    "cli-api-key",
                    "--host",
                    "http://localhost:3000",
                ],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Hooks installed" in plain_output

            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert hook_script.exists()
            hook_content = hook_script.read_text()
            assert "cli-api-key" in hook_content
            assert "http://localhost:3000" in hook_content
            assert "config-api-key" not in hook_content


def test_setup_hooks_install_uses_host_specific_credentials():
    """Test that --install uses credentials for the specific host provided."""
    with tempfile.TemporaryDirectory() as temp_dir:
        client_dir = Path(temp_dir) / ".cursor"

        config = Config(
            default_host="https://app.runlayer.com",
            hosts={
                "app.runlayer.com": HostConfig(
                    url="https://app.runlayer.com", secret="production-key"
                ),
                "localhost:3000": HostConfig(
                    url="http://localhost:3000", secret="local-key"
                ),
            },
        )

        with (
            patch.dict(
                "runlayer_cli.commands.setup.CLIENT_CONFIG_DIRS",
                {Client.CURSOR: client_dir},
            ),
            patch("runlayer_cli.config.load_config", return_value=config),
        ):
            result = runner.invoke(
                app,
                [
                    "setup",
                    "hooks",
                    "--client",
                    "cursor",
                    "--install",
                    "--yes",
                    "--host",
                    "http://localhost:3000",
                ],
            )

            plain_output = strip_ansi(result.stdout)
            assert result.exit_code == 0
            assert "Hooks installed" in plain_output

            hook_script = client_dir / "hooks" / "runlayer-hook.sh"
            assert hook_script.exists()
            hook_content = hook_script.read_text()
            assert "local-key" in hook_content
            assert "http://localhost:3000" in hook_content
            assert "production-key" not in hook_content
