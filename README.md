# ATLAS AI

**A virtual multi-agent operations team for travel agencies**  
**فريق ذكاء اصطناعي افتراضي لإدارة شركات السياحة**

ATLAS AI is a cloud-first prototype for travel-agency operations. The system uses a General Manager agent to route work to specialist crews, while keeping the owner in control of approvals.

## Current delivery status

| Phase | Scope | Status |
|---|---|---|
| 1 | Cloud-first repository, Codespaces, Docker, documentation, CI and Pages setup | Complete |
| 2 | FastAPI, SQLite, Mock LLM, General Manager and first Sales Crew workflows | Implemented |
| 3 | Finance, Marketing, Customer Success, Reporting and expanded approval policies | Planned |
| 4 | Streamlit Control Center connected to the API | Implemented (initial functional UI) |
| 5 | Bilingual static landing page and interactive mock demo | Planned |
| 6 | Expanded tests, security hardening and production deployment guidance | Planned |

## Human-facing Control Center

The Streamlit dashboard is the normal interface for the prototype. Swagger at `/docs` is reserved for technical API inspection.

Start the API in one Codespaces terminal:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Start the interface in a second terminal:

```bash
python -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```

Open forwarded port **8501** from the Codespaces **Ports** panel. The application opens with an Arabic-first dashboard and an English language toggle.

### Dashboard areas

- **Overview:** lead and task KPIs, latest activity, quick actions.
- **Leads:** add and search customer travel requests.
- **Task center:** generate lead-qualification and draft-offer tasks, inspect agent outputs, edit, approve, or reject.
- **AI team:** view the current General Manager and Sales Crew structure.
- **Reports:** weekly lead and task activity.
- **Settings:** prototype connection and agency context.

The dashboard connects to FastAPI through `ATLAS_API_URL` (default: `http://127.0.0.1:8000`) and sends `X-Agency-ID` with each request.

### Run both services with Docker Compose

```bash
docker compose up --build
```

This starts FastAPI on port 8000 and the dashboard on port 8501. Stop with:

```bash
docker compose down
```

No local Docker Desktop or Python installation is required; run these commands inside Codespaces.

## Phase 2 capabilities

- Persist travel leads in SQLite.
- Create and retrieve lead-qualification and draft-offer tasks.
- Route tasks through the General Manager to the Sales Crew.
- Review, edit, approve, or reject pending owner-review tasks.
- Retrieve agent status and a seven-day activity summary.
- Generate deterministic mock outputs without API keys.
- Keep draft offers unpriced and mark supplier availability as unverified.

## Dependencies

- `requirements.txt`: core API, Streamlit, SQLAlchemy, HTTP client and test dependencies.
- `requirements-agents.txt`: optional CrewAI integration. Do not install it until the Codespaces platform has compatible ONNX Runtime and LanceDB wheels.

The Sales Crew intentionally uses deterministic mock agents. CrewAI orchestration is not imported by the running API yet.

## Data and agency isolation

Lead and task records include an `agency_id`. Requests can select a demo agency with the `X-Agency-ID` header; if omitted, the API uses `demo-agency`.

This is a prototype data-partitioning mechanism, **not authentication or a security boundary**. Before real customer use, implement authentication, role-based authorization, tenant isolation tests, audit logs, backups, and a production database.

## Operating and safety boundaries

- No real bookings, supplier availability, inventory, or confirmed prices are connected.
- Offer package tiers are planning structures only; price is `null` and availability is `not_verified`.
- All sales tasks remain `pending_approval` until explicitly approved or rejected by the owner.
- No customer-facing messages or booking actions are sent.
- Never commit `.env`, API keys, tokens, passwords, or real customer information.
- GitHub Pages publishes only static files from `docs/`; it does not host this API or database.
- Codespaces is a development environment, not permanent production hosting.

## Architecture

- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- Streamlit Control Center
- Deterministic Mock LLM adapter
- General Manager + Sales Crew
- Optional future CrewAI integration
- GitHub Actions, GitHub Pages, Docker and Codespaces

---

# العربية

## التعامل مع النظام

واجهة Streamlit هي الواجهة اليومية للتعامل مع ATLAS AI. صفحة Swagger مخصصة لفحص الـ API تقنيًا فقط.

لتشغيل النظام من Codespaces:

**Terminal الأول — الـ API:**

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

**Terminal الثاني — واجهة المستخدم:**

```bash
python -m streamlit run dashboard/app.py --server.address 0.0.0.0 --server.port 8501
```

بعدها افتح تبويب **Ports** واضغط رابط المنفذ **8501**. هتظهر لك واجهة عربية، مع إمكانية التحويل للإنجليزية.

### أقسام الواجهة

- **نظرة عامة:** مؤشرات العملاء والمهام وآخر نشاط.
- **العملاء:** تسجيل طلبات السفر والبحث فيها.
- **مركز المهام:** إرسال المهام للوكلاء ومراجعة النتائج وتعديلها واعتمادها أو رفضها.
- **فريق الذكاء الاصطناعي:** عرض الهيكل الحالي للمدير العام وفريق المبيعات.
- **التقارير:** ملخص نشاط آخر سبعة أيام.
- **الإعدادات:** سياق الوكالة والاتصال التجريبي.

يمكنك تشغيل الواجهة والـ API معًا باستخدام Docker Compose:

```bash
docker compose up --build
```

الواجهة على المنفذ 8501 والـ API على 8000.

## حدود النسخة الحالية

الوكلاء يعملون في وضع Mock. لا يوجد اتصال حقيقي بموردين أو أسعار أو توافر أو حجوزات. كل العروض غير مسعّرة، وكل المهام تنتظر اعتماد المالك. معرّف الوكالة الحالي للتجربة فقط وليس نظام صلاحيات إنتاجيًا.
