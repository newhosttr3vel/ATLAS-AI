# ATLAS AI

**A virtual multi-agent operations team for travel agencies**  
**فريق ذكاء اصطناعي افتراضي لإدارة شركات السياحة**

> **Current delivery stage: Phase 1 — Cloud-first foundation.** This repository currently contains the project foundation only. Working agents, business workflows, approvals, and the operational dashboard are planned for later phases.

## Product principles

- **Owner in the loop:** customer-facing offers and messages require explicit owner approval.
- **Safe by default:** no real bookings, availability confirmations, payments, or outbound customer messages.
- **Mock first:** the prototype must run without paid services or provider API keys.
- **No invented facts:** agents must request missing information and clearly label assumptions or estimates.
- **Cloud-first development:** GitHub Codespaces is the development environment; installing Python or Docker Desktop on your computer is not required.
- **Separate demo and backend:** GitHub Pages serves static files from `docs/` only. It does not run FastAPI, CrewAI, SQLite, or Streamlit.
- **Future-ready:** SQLite is for the prototype; the architecture is intended to support PostgreSQL and multiple travel agencies later.

## Technology

- Python 3.11+
- FastAPI for the API
- CrewAI for the planned agent orchestration
- SQLite for the prototype database
- Streamlit for the planned operations dashboard
- Docker and Docker Compose inside GitHub Codespaces
- GitHub Actions for CI and static Pages deployment
- pytest for automated tests

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
│   ├── tools/
│   └── main.py
├── dashboard/
├── docs/                  # Static GitHub Pages demo only
├── tests/
├── .dockerignore
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── LICENSE
├── requirements.txt
└── README.md
```

## Develop entirely in the browser

### 1. Create the cloud workspace

1. Open [the ATLAS AI repository](https://github.com/newhosttr3vel/ATLAS-AI).
2. Select **Code → Codespaces**.
3. Select **Create codespace on main**.
4. Wait for the development container to finish building.
5. Use the integrated terminal inside the browser.

The Dev Container configuration provides Python 3.11 and Docker tooling through the Docker-in-Docker feature. It installs the Python dependencies, creates a local ignored `.env` file from `.env.example`, and forwards ports 8000 and 8501.

**You do not need to install Docker Desktop, Python, or a code editor on your computer.** A Docker Hub account is also not needed just to build and run this project's containers inside Codespaces.

### 2. Run the foundation API

The environment is prepared automatically. In the Codespaces terminal, run:

```bash
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open the forwarded port **8000** from the Codespaces **Ports** panel:

- Health check: `/health`
- Interactive API documentation: `/docs`

### 3. Run with Docker Compose in the cloud

The Codespaces environment includes Docker and Compose. Run:

```bash
docker compose up --build
```

To stop the services:

```bash
docker compose down
```

The API uses port 8000. SQLite files are stored under `data/`, which is intentionally excluded from Git.

## GitHub Pages

GitHub Pages is reserved for the public static demo. It cannot host the Python API, database, agent runtime, or Streamlit dashboard.

To enable the deployment workflow:

1. Open **Settings → Pages** in this repository.
2. Set **Build and deployment → Source** to **GitHub Actions**.
3. The `deploy-pages.yml` workflow will publish the `docs/` directory when relevant changes reach `main`.

The current `docs/index.html` is only a branded placeholder. The interactive bilingual demo is planned for Phase 5.

## Security and operating boundaries

- Never commit `.env`, API keys, passwords, tokens, or private keys.
- Do not put secrets in the static `docs/` site or GitHub Pages.
- Do not use real customer records or booking documents in this prototype.
- No agent may confirm a booking, guarantee availability, invent a price, or send a customer-facing message without owner approval.
- Codespaces is a development environment, not permanent production hosting.
- Production use will require authentication, tenant isolation, role-based permissions, audit logs, backups, monitoring, and a separately hosted backend.

## Delivery roadmap

| Phase | Scope | Status |
|---|---|---|
| 1 | Repository foundation, Codespaces, Docker, documentation, CI and Pages workflow | Foundation |
| 2 | FastAPI, SQLite models, Mock LLM, General Manager and Sales Crew | Planned |
| 3 | Finance, Marketing, Customer Success, Reporting and owner approvals | Planned |
| 4 | Streamlit Control Center connected to the API | Planned |
| 5 | Bilingual static landing page and interactive mock demo | Planned |
| 6 | Expanded tests, security hardening and future deployment guidance | Planned |

---

# العربية

## ما هو ATLAS AI؟

منصة SaaS قيد التطوير لشركات السياحة، تعتمد على فريق من وكلاء الذكاء الاصطناعي المتخصصين في المبيعات والتسويق والمالية وخدمة العملاء والتقارير، مع وجود مدير عام ينسّق العمل ويرفع النتائج لصاحب الشركة للمراجعة والاعتماد.

**الموجود حاليًا هو مرحلة تأسيس المشروع فقط، وليس نظامًا تشغيليًا مكتملًا.**

## طريقة العمل — أونلاين بالكامل

1. افتح [مستودع ATLAS AI على GitHub](https://github.com/newhosttr3vel/ATLAS-AI).
2. اضغط **Code → Codespaces → Create codespace on main**.
3. انتظر تجهيز بيئة العمل السحابية.
4. افتح Terminal من داخل المتصفح.

بيئة Codespaces مجهزة لتوفير Python 3.11 وأدوات Docker وDocker Compose داخل البيئة السحابية، وتثبيت المكتبات تلقائيًا، وإنشاء ملف `.env` محلي غير مرفوع إلى GitHub.

**مش محتاج تحمّل Docker Desktop أو Python أو أي برنامج على جهازك.** وحساب Docker مش مطلوب لتشغيل الحاويات داخل Codespaces.

## تشغيل المشروع

لتشغيل الاختبارات والـ API من Terminal داخل Codespaces:

```bash
pytest -q
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

بعدها افتح المنفذ **8000** من تبويب **Ports**:

- فحص حالة التطبيق: `/health`
- توثيق الـ API: `/docs`

لتشغيله باستخدام Docker:

```bash
docker compose up --build
```

ولإيقاف الخدمات:

```bash
docker compose down
```

## الفرق بين الأدوات

- **GitHub:** حفظ الكود وإدارة الإصدارات والتعديلات.
- **GitHub Codespaces:** بيئة التطوير والتشغيل السحابية التي نستخدمها من المتصفح.
- **Docker:** تشغيل خدمات المشروع داخل Codespaces، وليس على جهازك.
- **GitHub Pages:** عرض النسخة التجريبية الثابتة فقط من مجلد `docs/`.
- **الاستضافة الإنتاجية:** خطوة مستقبلية منفصلة؛ Codespaces ليس سيرفرًا دائمًا.

## قواعد الأمان

- لا ترفع أي API Key أو كلمة مرور أو Token إلى GitHub.
- لا تستخدم بيانات عملاء حقيقية في النسخة التجريبية.
- لا يتم تأكيد حجز أو سعر أو توافر، ولا إرسال رسالة للعميل، دون تحقق وموافقة المالك.
- أي افتراض أو سعر تقديري يجب توضيحه وعدم تقديمه كحقيقة مؤكدة.

## مراحل التنفيذ

سننفذ المشروع على مراحل مستقلة، ونراجع نتيجة كل مرحلة واختباراتها قبل الانتقال إلى التالية. المرحلة الحالية هي **Phase 1 — Foundation**، وبعد اعتمادها نبدأ Backend والوكلاء في Phase 2.
