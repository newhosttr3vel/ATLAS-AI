# Meyaar AI Platform

**فريق AI افتراضي لإدارة شركات السياحة**  
*A virtual AI team for travel agencies.*

> **Current stage: Phase 1 — Cloud-first project foundation.** This stage establishes the repository, Codespaces development environment, Docker setup, documentation, and CI workflows. Agent execution and business features come in later phases.

## Product principles

- **Owner-in-the-loop:** no customer-facing offer or message is sent without owner approval.
- **Safe by default:** no real API keys, secrets, payments, bookings, or outbound messaging.
- **Mock first:** the prototype starts with deterministic mock behavior and no external LLM key.
- **Cloud-first development:** GitHub Codespaces is the primary development environment. No local Python or Docker installation is required.
- **Separate demo and backend:** GitHub Pages serves only static files from `docs/`; it does not run FastAPI, CrewAI, SQLite, or Streamlit.
- **Future-ready:** SQLite for the prototype, with a migration path to PostgreSQL and multi-agency tenancy.

## Repository structure

```text
ATLAS-AI/
├── .devcontainer/
│   └── devcontainer.json
├── .github/workflows/
│   ├── ci.yml
│   └── deploy-pages.yml
├── backend/
│   ├── agents/
│   ├── crews/
│   ├── services/
│   └── tools/
├── dashboard/
├── docs/                  # Static GitHub Pages demo only
├── tests/
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── requirements.txt
└── README.md
```

## Cloud-first quick start (recommended)

### 1. Create a Codespace

1. Open this repository on GitHub.
2. Select **Code → Codespaces → Create codespace on main**.
3. Wait for the cloud development container to initialize.
4. Open the integrated terminal in the browser.

The `.devcontainer/devcontainer.json` file configures Python 3.11, Docker tooling, and forwarded development ports. You do not need to install Python or Docker Desktop on your personal computer.

### 2. Install project dependencies

The Codespaces container runs the setup command automatically. If you need to repeat it:

```bash
python -m pip install --upgrade pip
pip install -r requirements.txt
cp .env.example .env
```

### 3. Run tests and start the API

```bash
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open the forwarded port 8000 in the Codespaces **Ports** panel:
- Health: `/health`
- API docs: `/docs`

### 4. Run Docker Compose in the cloud

From the Codespaces terminal:

```bash
cp .env.example .env
docker compose up --build
```

The API will be available through forwarded port 8000. Docker runs in the Codespaces cloud environment; it is not installed on your personal computer.

## Optional local development

Local execution is optional, not the primary workflow. If you later choose to work locally, install Python 3.11+ and Docker, then use the same commands above.

## Environment and secrets

`.env.example` contains safe defaults. Copy it to `.env` inside Codespaces. The `.env` file is ignored by Git.

Never commit:
- `.env` or provider credentials
- API keys, tokens, passwords, private keys
- real customer information or booking documents

Future model-provider keys must be injected through environment variables or a secrets manager. GitHub Pages must never receive backend credentials.

## GitHub Pages demo

The `docs/` directory is reserved for a static HTML/CSS/JavaScript demo. It must not call the backend or contain secrets.

To enable deployment:
1. Open **Settings → Pages** in this repository.
2. Set **Build and deployment → Source** to **GitHub Actions**.
3. Push changes to `main`; `deploy-pages.yml` publishes the contents of `docs/`.

GitHub Pages is a static demo only. It cannot host FastAPI, CrewAI, SQLite, or Streamlit.

## Workflows

- `ci.yml`: installs dependencies, runs pytest, and verifies the FastAPI application can be imported.
- `deploy-pages.yml`: publishes only `docs/` to GitHub Pages after changes to the demo or workflow.

## Delivery roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Repository, Codespaces, Docker, docs, CI and Pages workflows | Foundation |
| 2 | FastAPI, SQLite models, Mock LLM, General Manager + Sales Crew | Planned |
| 3 | Finance, Marketing, Customer Success, Reporting, owner approvals | Planned |
| 4 | Streamlit Control Center connected to the API | Planned |
| 5 | Static bilingual landing page and interactive mock demo | Planned |
| 6 | Tests, security hardening, migration and deployment guides | Planned |

## Architecture decisions

### Multi-agency readiness
The prototype will be designed so that agency/tenant scoping can be introduced consistently. Before real SaaS use, add tenant isolation, authentication, role-based access control, audit trails, backups, monitoring, and production-grade PostgreSQL migrations.

### Agent orchestration
CrewAI is the planned orchestration layer. The default prototype path must remain deterministic and mock-driven, so the application can be demonstrated without API keys. Real model providers such as Ollama or hosted APIs are later opt-in adapters.

### Production hosting
Codespaces is for development and testing, not always-on production hosting. GitHub Pages is for the static demo only. A later phase must deploy the API, database, and dashboard to a separately secured runtime.

## Current limitations

This is a foundation scaffold, not yet a functional SaaS. Leads, task routing, CrewAI execution, approvals, reports, and the Streamlit dashboard are implemented in subsequent phases. No customer messages, bookings, payments, or price confirmations are enabled.

## License

MIT — see [LICENSE](LICENSE).

---

# العربية

## طريقة العمل المعتمدة

هنشتغل أونلاين بالكامل من المتصفح باستخدام **GitHub Codespaces**. مش مطلوب تثبيت Python أو Docker على جهازك.

1. افتح المستودع على GitHub.
2. اضغط **Code → Codespaces → Create codespace on main**.
3. افتح Terminal داخل Codespaces.
4. نفّذ:

```bash
pip install -r requirements.txt
cp .env.example .env
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --reload
```

افتح المنفذ 8000 من تبويب **Ports** للوصول إلى الـ API.

## Docker أونلاين

Docker هيشتغل داخل بيئة Codespaces السحابية:

```bash
docker compose up --build
```

مش محتاج تثبيت Docker Desktop على جهازك.

## مهم جدًا

- GitHub هو مكان حفظ الكود والـ Commits.
- Codespaces هو مكان التطوير والتشغيل المؤقت.
- GitHub Pages يعرض Demo ثابت فقط من مجلد `docs/`.
- Codespaces ليس استضافة دائمة للـ Backend.
- لا تضع أي API Key أو بيانات عملاء حقيقية في المستودع.
- كل عرض أو رسالة حساسة تظل خاضعة لموافقة المالك.

**المرحلة الحالية تأسيس فقط.** سنبدأ تنفيذ Backend والوكلاء بعد مراجعة اكتمال المرحلة الأولى.
