from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def test_required_phase_two_and_dashboard_files_exist() -> None:
    required = [
        "README.md",
        ".env.example",
        "requirements.txt",
        "requirements-agents.txt",
        "Dockerfile",
        "docker-compose.yml",
        ".devcontainer/devcontainer.json",
        "backend/main.py",
        "backend/database.py",
        "backend/models.py",
        "backend/schemas.py",
        "backend/agents/general_manager.py",
        "backend/agents/lead_qualifier.py",
        "backend/agents/offer_builder.py",
        "backend/crews/sales.py",
        "backend/services/mock_llm.py",
        "dashboard/app.py",
        "dashboard/README.md",
        ".streamlit/config.toml",
        "docs/index.html",
        ".github/workflows/ci.yml",
        ".github/workflows/deploy-pages.yml",
        "tests/conftest.py",
    ]
    assert all((ROOT / path).exists() for path in required)
