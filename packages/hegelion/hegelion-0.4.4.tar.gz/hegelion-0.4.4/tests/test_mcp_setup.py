import json
from pathlib import Path

import pytest

from hegelion.scripts import mcp_setup


def test_generate_config_includes_servers(tmp_path):
    cfg = mcp_setup.generate_config("/bin/python", tmp_path, is_installed=False)
    servers = cfg["mcpServers"]
    assert "hegelion" in servers
    assert "hegelion-backend" not in servers
    assert servers["hegelion"]["args"] == ["-m", "hegelion.mcp.server"]


def test_generate_config_sets_pythonpath_when_source(tmp_path):
    cfg = mcp_setup.generate_config("/bin/python", tmp_path, is_installed=False)
    env = cfg["mcpServers"]["hegelion"]["env"]
    assert env["PYTHONPATH"] == str(tmp_path)


def test_generate_config_omits_env_when_installed(tmp_path):
    cfg = mcp_setup.generate_config("/bin/python", tmp_path, is_installed=True)
    assert "env" not in cfg["mcpServers"]["hegelion"]


def test_write_config_merges(tmp_path):
    target = tmp_path / "mcp.json"
    snippet = {"hegelion": {"command": "python", "args": ["-m", "h"]}}
    mcp_setup._write_config(target, snippet)
    payload = json.loads(target.read_text())
    assert payload["mcpServers"]["hegelion"]["command"] == "python"

    # Merge existing content
    snippet2 = {"other": {"command": "node", "args": ["srv"]}}
    mcp_setup._write_config(target, snippet2)
    payload = json.loads(target.read_text())
    assert set(payload["mcpServers"].keys()) == {"hegelion", "other"}


def test_is_installed_in_site_packages_detects_site(monkeypatch: pytest.MonkeyPatch, tmp_path):
    fake_site = tmp_path / "site-packages"
    fake_site.mkdir()
    fake_pkg = fake_site / "hegelion"
    fake_pkg.mkdir()
    fake_init = fake_pkg / "__init__.py"
    fake_init.write_text("", encoding="utf-8")

    monkeypatch.setattr(mcp_setup.site, "getsitepackages", lambda: [str(fake_site)])
    monkeypatch.setattr(mcp_setup.site, "getusersitepackages", lambda: str(fake_site))
    monkeypatch.setattr(mcp_setup.hegelion, "__file__", str(fake_init))

    assert mcp_setup.is_installed_in_site_packages() is True


def test_print_setup_instructions_mentions_py_path(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
):
    monkeypatch.setattr(mcp_setup, "get_python_path", lambda: "/bin/python")
    monkeypatch.setattr(mcp_setup, "is_installed_in_site_packages", lambda: False)
    monkeypatch.setattr(mcp_setup, "get_project_root", lambda: tmp_path)

    mcp_setup.print_setup_instructions()

    captured = capsys.readouterr()
    assert "hegelion" in captured.out
    assert "Added PYTHONPATH" in captured.out


def test_print_setup_instructions_shows_windows_paths(
    monkeypatch: pytest.MonkeyPatch, capsys, tmp_path
):
    """Test that Windows config paths are displayed in instructions."""
    monkeypatch.setattr(mcp_setup, "get_python_path", lambda: "/bin/python")
    monkeypatch.setattr(mcp_setup, "is_installed_in_site_packages", lambda: True)
    monkeypatch.setattr(mcp_setup, "get_project_root", lambda: tmp_path)

    mcp_setup.print_setup_instructions()

    captured = capsys.readouterr()
    assert "Windows Claude Desktop" in captured.out
    assert "%APPDATA%" in captured.out
    assert "Cursor (Windows)" in captured.out


def test_resolve_host_path_vscode():
    assert mcp_setup.resolve_host_path("vscode", platform="darwin") == Path(".vscode/mcp.json")


def test_resolve_host_path_cursor_windows():
    env = {"APPDATA": "C:\\Users\\Test\\AppData\\Roaming"}
    expected = Path(env["APPDATA"]) / "Cursor" / "User" / "globalStorage" / "mcp.json"
    assert mcp_setup.resolve_host_path("cursor", platform="win32", env=env) == expected


def test_resolve_host_path_claude_desktop_darwin():
    expected = Path("~/Library/Application Support/Claude/claude_desktop_config.json")
    assert mcp_setup.resolve_host_path("claude", platform="darwin") == expected
