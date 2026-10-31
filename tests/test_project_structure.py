from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_foundation_files_exist() -> None:
    required = [
        "README.md",
        ".env.example",
        "requirements.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".devcontainer/devcontainer.json",
        "backend/main.py",
        "docs/index.html",
        ".github/workflows/ci.yml",
        ".github/workflows/deploy-pages.yml",
    ]
    assert all((ROOT / path).exists() for path in required)
