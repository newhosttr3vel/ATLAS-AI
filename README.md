# ATLAS AI

**A virtual multi-agent operations team for travel agencies**  
**فريق ذكاء اصطناعي افتراضي لإدارة شركات السياحة**

ATLAS AI is a cloud-first prototype for travel-agency operations. The system uses a General Manager agent to route work to specialist crews, while keeping the owner in control of approvals.

## Current delivery status

| Phase | Scope | Status |
|---|---|---|
| 1 | Cloud-first repository, Codespaces, Docker, documentation, CI and Pages setup | Complete |
| 2 | FastAPI, SQLite, Mock LLM, General Manager and first Sales Crew workflows | Implemented; validating in CI |
| 3 | Finance, Marketing, Customer Success, Reporting and expanded approval policies | Planned |
| 4 | Streamlit Control Center connected to the API | Planned |
| 5 | Bilingual static landing page and interactive mock demo | Planned |
| 6 | Expanded tests, security hardening and production deployment guidance | Planned |

## Phase 2 capabilities

- Persist travel leads in SQLite.
- Create and retrieve lead-qualification and draft-offer tasks.
- Route tasks through the General Manager to the Sales Crew.
- Include lead qualifier and offer builder specialist agents.
- Review, edit, approve, or reject pending owner-review tasks.
- Retrieve agent status and a seven-day activity summary.
- Generate deterministic mock outputs without API keys.
- Keep draft offers unpriced and mark supplier availability as unverified.

### Current API routes

| Method | Route | Purpose |
|---|---|---|
| GET | `/` | API service information |
| GET | `/health` | Health check |
| POST | `/api/leads` | Create a lead |
| GET | `/api/leads` | List agency leads |
| POST | `/api/tasks` | Route a supported sales task |
| GET | `/api/tasks` | List tasks |
| GET | `/api/tasks/{task_id}` | Retrieve task detail |
| POST | `/api/tasks/{task_id}/approve` | Approve a pending task |
| POST | `/api/tasks/{task_id}/reject` | Reject a pending task |
| POST | `/api/tasks/{task_id}/edit` | Edit a pending result without removing approval |
| GET | `/api/agents` | List prototype agents and activity |
| GET | `/api/reports/weekly` | Seven-day activity summary |

## Develop in the browser with GitHub Codespaces

1. Open [the repository](https://github.com/newhosttr3vel/ATLAS-AI).
2. Select **Code → Codespaces → Create codespace on main**.
3. Open the integrated terminal.
4. Prepare the environment:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

5. Run the tests:

```bash
python -m pytest -q
```

6. Start the API:

```bash
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open port 8000 in the Codespaces **Ports** panel, then visit `/docs` to explore the API.

### Run with Docker in Codespaces

```bash
docker compose up --build
```

Stop the containers with `docker compose down`.

**No local Docker Desktop or Python installation is required.** Codespaces is a development environment, not permanent production hosting.

## Dependencies

- `requirements.txt`: core API, Streamlit, SQLAlchemy and test dependencies.
- `requirements-agents.txt`: optional CrewAI integration. Do not install it until the Codespaces platform has compatible ONNX Runtime and LanceDB wheels.

The current Sales Crew intentionally uses deterministic mock agents. CrewAI orchestration is not imported by the running API yet, so the prototype works without provider credentials or heavyweight vector-store dependencies.

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

## Architecture

- Python 3.11+
- FastAPI
- SQLAlchemy + SQLite
- Pydantic v2
- Deterministic Mock LLM adapter
- General Manager + Sales Crew
- Streamlit dashboard (planned)
- CrewAI adapter (optional future integration)
- GitHub Actions, GitHub Pages, Docker and Codespaces

---

# العربية

## فكرة ATLAS AI

منصة لإدارة عمليات شركات السياحة عن طريق فريق من وكلاء الذكاء الاصطناعي. المدير العام يستقبل المهمة ويوجهها إلى القسم المناسب، والمالك يراجع النتائج ويعتمدها قبل أي إجراء حساس أو تواصل مع العميل.

## ما تم تنفيذه في المرحلة الثانية

- قاعدة بيانات SQLite لحفظ العملاء والمهام.
- إضافة عميل جديد وعرض قائمة العملاء.
- المدير العام يوجه مهام المبيعات إلى الوكلاء المتخصصين.
- وكيل تأهيل العملاء يراجع اكتمال بيانات الرحلة ويحدد المعلومات الناقصة.
- وكيل إعداد العروض ينشئ ثلاثة مستويات تخطيطية: اقتصادي ومتوازن ومميز.
- مراجعة المهمة وتعديل نتيجتها أو اعتمادها أو رفضها.
- عرض الوكلاء وحالة نشاطهم وملخص أسبوعي.
- وضع Mock يعمل بدون API Keys أو خدمات مدفوعة.

## تجربة الـ API

بعد تشغيل السيرفر افتح:

- `/docs` لتجربة الـ API.
- `/health` لفحص التشغيل.
- `/api/agents` لعرض الوكلاء.
- `/api/reports/weekly` لملخص النشاط.

### إنشاء عميل تجريبي

أرسل POST إلى `/api/leads` بالبيانات التالية:

```json
{
  "customer_name": "Demo Customer",
  "destination": "Makkah",
  "travel_start": "2027-01-10",
  "travel_end": "2027-01-15",
  "travelers": 3,
  "budget_amount": 25000,
  "currency_code": "EGP"
}
```

### تشغيل مهمة تأهيل العميل

استخدم قيمة `id` التي رجعت من إنشاء العميل في الطلب التالي إلى `/api/tasks`:

```json
{
  "task_type": "qualify_lead",
  "lead_id": "PASTE_LEAD_ID_HERE"
}
```

يمكنك أيضًا استخدام `build_offer` لإعداد هيكل عرض مبدئي غير مسعّر.

**مهم:** هذه عروض تجريبية لا تحتوي على أسعار فعلية أو تأكيد توافر. كل مهمة مبيعات تتطلب موافقة المالك، ولا يتم إرسال رسائل أو تنفيذ حجوزات.

## تشغيل المشروع من Codespaces

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
python -m pytest -q
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

لتشغيل Docker من داخل Codespaces:

```bash
docker compose up --build
```

لا تحتاج إلى تثبيت Docker Desktop على جهازك.

## تنبيه الأمان

حقل `X-Agency-ID` لعزل بيانات الوكالات في النموذج الأولي فقط، وليس نظام تسجيل دخول أو حماية نهائي. قبل الاستخدام التجاري الحقيقي يجب إضافة تسجيل الدخول والصلاحيات والتدقيق وسلامة عزل بيانات كل وكالة.
