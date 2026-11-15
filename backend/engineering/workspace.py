"""Constrained project workspace and command runner."""
from __future__ import annotations
import os
import subprocess
from pathlib import Path
from typing import Any

WORKSPACE_ROOT = Path(os.getenv("ATLAS_WORKSPACE_ROOT", "data/workspaces")).resolve()
MAX_FILE_BYTES = 512_000
ALLOWED_COMMANDS = {
    ("python", "-m", "pytest"), ("python", "-m", "compileall"),
    ("python", "-m", "ruff"), ("npm", "run", "test"),
    ("npm", "run", "build"), ("npm", "run", "lint"),
    ("npm", "run", "typecheck"), ("git", "status"), ("git", "diff"),
}

class WorkspaceError(ValueError):
    pass

class Workspace:
    def __init__(self, agency_id: str, name: str):
        if not agency_id.replace("-", "").isalnum() or not name.replace("-", "").replace("_", "").replace(".", "").isalnum():
            raise WorkspaceError("Invalid workspace identifier.")
        self.root = (WORKSPACE_ROOT / agency_id / name).resolve()
        if not self.root.is_relative_to(WORKSPACE_ROOT):
            raise WorkspaceError("Workspace path escaped the workspace root.")
        self.root.mkdir(parents=True, exist_ok=True)

    def _path(self, relative_path: str) -> Path:
        candidate = (self.root / relative_path).resolve()
        if not candidate.is_relative_to(self.root):
            raise WorkspaceError("Path traversal is not allowed.")
        return candidate

    def list_files(self, limit: int = 200) -> list[str]:
        ignored = {".git", "node_modules", ".venv", "__pycache__", ".next"}
        found = []
        for path in self.root.rglob("*"):
            if any(part in ignored for part in path.parts):
                continue
            if path.is_file():
                found.append(path.relative_to(self.root).as_posix())
                if len(found) >= limit:
                    break
        return sorted(found)

    def read_file(self, path: str) -> str:
        target = self._path(path)
        if not target.is_file():
            raise WorkspaceError("File does not exist.")
        if target.stat().st_size > MAX_FILE_BYTES:
            raise WorkspaceError("File exceeds the 500 KB read limit.")
        return target.read_text(encoding="utf-8")

    def write_file(self, path: str, content: str) -> str:
        if len(content.encode("utf-8")) > MAX_FILE_BYTES:
            raise WorkspaceError("File exceeds the 500 KB write limit.")
        target = self._path(path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return target.relative_to(self.root).as_posix()

    def run_command(self, argv: list[str], timeout: int = 90) -> dict[str, Any]:
        if not argv or not any(tuple(argv[:len(prefix)]) == prefix for prefix in ALLOWED_COMMANDS):
            raise WorkspaceError("Command is not in the ATLAS safe-command allowlist.")
        if any(token in {";", "&&", "||", "|", ">", "<", "$("} for token in argv):
            raise WorkspaceError("Shell operators are not allowed.")
        completed = subprocess.run(
            argv, cwd=self.root, capture_output=True, text=True,
            timeout=min(max(timeout, 1), 120), check=False, shell=False,
            env={**os.environ, "CI": "1", "PYTHONDONTWRITEBYTECODE": "1"},
        )
        return {"exit_code": completed.returncode, "stdout": completed.stdout[-12000:], "stderr": completed.stderr[-12000:]}
