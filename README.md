# ATLAS AI

**A virtual multi-agent operations team for travel agencies**  
**فريق ذكاء اصطناعي افتراضي لإدارة شركات السياحة**

ATLAS AI is a cloud-first prototype for travel-agency operations. The system uses a General Manager agent to route work to specialist crews, while keeping the owner in control of approvals.

## Current delivery status

| Phase | Scope | Status |
|---|---|---|
| 1 | Cloud-first repository, Codespaces, Docker, documentation, CI and Pages setup | Complete |
| 2 | FastAPI, SQLite, Mock LLM, General Manager and first Sales Crew workflows | Implemented |
| 3 | Initial Finance, Marketing, Customer Success workflows and expanded approval policies | Implemented (initial workflows) |
| 4 | Bilingual Streamlit Control Center, guided task workflows and operational reports | Implemented (enhanced prototype) |
| 5 | Weekly narrative report writer, agency registry metadata and audit foundation | Implemented (prototype groundwork) |
| 6 | Agency registration, signed sessions, RBAC, team accounts and secure tenant binding | Implemented (security foundation) |

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
- **Task center:** create sales, finance, marketing, support, and complaint tasks; inspect outputs, edit, approve, or reject.
- **AI team:** view department managers and specialist agents across Sales, Finance, Marketing, Customer Success, and Reporting.
- **Reports:** seven-day lead pipeline, task status, task-type and department activity, approval rate, average task processing time, CSV export, and an owner-reviewable narrative report.
- **Settings:** prototype connection and agency context.

The dashboard connects to FastAPI through `ATLAS_API_URL` (default: `http://127.0.0.1:8000`). Signed-in users send a bearer token bound to their agency membership; the old `X-Agency-ID` selector is available only in development mode.

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

## Initial Phase 3 department workflows

- Finance: prepare a cost worksheet and an internal invoice shell. Supplier costs, totals, taxes, selling prices, and amounts due remain empty until verified source data and financial review are supplied.
- Marketing: draft Arabic and English travel content using recorded lead facts; no publishing, unverified discounts, supplier claims, or availability statements.
- Customer Success: draft internal customer replies and classify complaint notes for human review; no customer messages are sent.
- Reporting: the weekly reporting endpoint summarizes recorded leads and task statuses; it does not invent external performance data.
- Every department task requires owner approval. All added agents currently use deterministic mock logic, not a connected LLM.

## Reporting and SaaS groundwork

- The Report Writer creates a seven-day narrative from the selected agency's stored lead and task metrics. Every generated report is a task awaiting owner approval.
- Workspace registry metadata stores an agency name, slug, status, prototype plan, default currency, and timezone.
- Operational events for lead creation, task creation, edits, approvals, rejections, and report generation are recorded in an agency-scoped audit table.
- The agency ID header still selects a prototype workspace only. It is not authentication, membership, or authorization. Do not expose this prototype API to real customers or sensitive production data.
- The registry and audit log are groundwork only. Secure SaaS onboarding, user accounts, agency memberships, role-based permissions, signed sessions, tenant-bound authentication, and production database migrations remain in the next security phase.

## Dependencies

- `requirements.txt`: core API, Streamlit, SQLAlchemy, HTTP client and test dependencies.
- `requirements-agents.txt`: optional CrewAI integration. Do not install it until the Codespaces platform has compatible ONNX Runtime and LanceDB wheels.

The Sales Crew intentionally uses deterministic mock agents. CrewAI orchestration is not imported by the running API yet.

## Data and agency isolation

Lead and task records include an `agency_id`. Requests can select a demo agency with the `X-Agency-ID` header; if omitted, the API uses `demo-agency`.

Production-mode requests now resolve their agency from a verified bearer session and active membership. Development retains the old header-only test path. Complete production deployment hardening and the remaining controls listed above before onboarding real customers.

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
- **التقارير:** مسار العملاء وحالة المهام ونشاط الأقسام ونسبة الاعتماد ومتوسط زمن التنفيذ مع تصدير CSV.
- **الإعدادات:** سياق الوكالة والاتصال التجريبي.

يمكنك تشغيل الواجهة والـ API معًا باستخدام Docker Compose:

```bash
docker compose up --build
```

الواجهة على المنفذ 8501 والـ API على 8000.

## حدود النسخة الحالية

الوكلاء يعملون في وضع Mock. لا يوجد اتصال حقيقي بموردين أو أسعار أو توافر أو حجوزات. كل العروض غير مسعّرة، وكل المهام تنتظر اعتماد المالك. في وضع الإنتاج يتم ربط الطلب بجلسة دخول موقعة وعضوية نشطة، أما وضع التطوير فيحتفظ بمسار التجربة القديم.


## Authentication setup

For production, set `APP_ENV=production` and configure `ATLAS_AUTH_SECRET` with a unique cryptographically random value of at least 32 characters. Never commit the secret. Example generation inside Codespaces:

```bash
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into the Codespaces secret/environment configuration for the API and dashboard. Do not use the development fallback secret in production. The Streamlit screen supports agency registration and sign-in; the development-only demo path is hidden in production.
