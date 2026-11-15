"""Security and safety tests for the engineering workspace."""
import pytest
from backend.engineering.workspace import Workspace, WorkspaceError

def test_workspace_write_and_read_are_confined(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.engineering.workspace.WORKSPACE_ROOT", tmp_path.resolve())
    workspace = Workspace("agency-one", "demo")
    assert workspace.write_file("src/main.py", "print('hello')") == "src/main.py"
    assert workspace.read_file("src/main.py") == "print('hello')"
    assert "src/main.py" in workspace.list_files()

def test_workspace_rejects_path_traversal(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.engineering.workspace.WORKSPACE_ROOT", tmp_path.resolve())
    workspace = Workspace("agency-one", "demo")
    with pytest.raises(WorkspaceError):
        workspace.write_file("../outside.txt", "nope")

def test_workspace_rejects_shell_operators(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.engineering.workspace.WORKSPACE_ROOT", tmp_path.resolve())
    workspace = Workspace("agency-one", "demo")
    with pytest.raises(WorkspaceError):
        workspace.run_command(["python", "-m", "pytest", "&&", "echo", "unsafe"])

def test_workspace_rejects_unlisted_commands(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.engineering.workspace.WORKSPACE_ROOT", tmp_path.resolve())
    workspace = Workspace("agency-one", "demo")
    with pytest.raises(WorkspaceError):
        workspace.run_command(["bash", "-c", "rm -rf ."])


def test_workspace_blocks_secret_files(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.engineering.workspace.WORKSPACE_ROOT", tmp_path.resolve())
    workspace = Workspace("agency-one", "demo")
    with pytest.raises(WorkspaceError):
        workspace.read_file(".env")

def test_workspace_commands_are_disabled_by_default(tmp_path, monkeypatch):
    monkeypatch.setattr("backend.engineering.workspace.WORKSPACE_ROOT", tmp_path.resolve())
    monkeypatch.delenv("ATLAS_ENABLE_WORKSPACE_COMMANDS", raising=False)
    workspace = Workspace("agency-one", "demo")
    with pytest.raises(WorkspaceError):
        workspace.run_command(["python", "-m", "pytest"])
