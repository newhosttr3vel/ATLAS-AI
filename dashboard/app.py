"""ATLAS AI Control Center — Streamlit UI connected to the FastAPI backend."""

from __future__ import annotations

import json
import os
from datetime import date, timedelta
from typing import Any

import pandas as pd
import requests
import streamlit as st


st.set_page_config(
    page_title="ATLAS AI | Control Center",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

API_URL = os.getenv("ATLAS_API_URL", "http://127.0.0.1:8000").rstrip("/")
REQUEST_TIMEOUT = 8


class APIError(RuntimeError):
    """Readable API error raised for HTTP and connection failures."""


def api_request(
    method: str,
    path: str,
    *,
    agency_id: str,
    payload: dict[str, Any] | None = None,
) -> Any:
    headers = {"X-Agency-ID": agency_id, "Accept": "application/json"}
    try:
        response = requests.request(
            method,
            f"{API_URL}{path}",
            headers=headers,
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
    except requests.RequestException as exc:
        raise APIError(
            "تعذر الاتصال بخدمة ATLAS AI. تأكد أن الـ API يعمل على المنفذ 8000."
        ) from exc

    if not response.ok:
        try:
            detail = response.json().get("detail", response.text)
        except ValueError:
            detail = response.text
        if isinstance(detail, list):
            detail = " — ".join(str(item.get("msg", item)) for item in detail)
        raise APIError(f"طلب API فشل ({response.status_code}): {detail}")

    if not response.content:
        return None
    return response.json()


TEXT = {
    "ar": {
        "nav": "مساحة العمل",
        "overview": "نظرة عامة",
        "leads": "العملاء المحتملون",
        "tasks": "مركز المهام",
        "team": "فريق الذكاء الاصطناعي",
        "reports": "التقارير",
        "settings": "الإعدادات",
        "agency": "معرّف الوكالة",
        "language": "اللغة",
        "connected": "الخدمة متصلة",
        "disconnected": "الخدمة غير متصلة",
        "mock": "وضع المحاكاة",
        "heading_overview": "مركز القيادة",
        "sub_overview": "صورة واضحة لعمليات وكالتك، ومهام الفريق، وما يحتاج إلى اعتمادك.",
        "heading_leads": "إدارة العملاء",
        "sub_leads": "اجمع طلبات السفر في مكان واحد وحوّلها إلى مهام قابلة للمتابعة.",
        "heading_tasks": "مراجعة واعتماد الأعمال",
        "sub_tasks": "راجع نتائج الوكلاء، عدّلها، ثم اعتمدها أو ارفضها.",
        "heading_team": "فريق ATLAS AI",
        "sub_team": "هيكل الفريق الحالي ومسؤولية كل وكيل وحجم المهام المسندة إليه.",
        "heading_reports": "تقارير الأداء",
        "sub_reports": "ملخص نشاط الوكالة خلال آخر سبعة أيام.",
        "heading_settings": "إعدادات مساحة العمل",
        "sub_settings": "إعدادات الاتصال وسياق وكالة الاختبار.",
        "total_leads": "إجمالي العملاء",
        "pending_tasks": "بانتظار اعتمادك",
        "approved_tasks": "مهام معتمدة",
        "total_tasks": "إجمالي المهام",
        "recent_leads": "أحدث العملاء",
        "recent_tasks": "آخر نشاط للفريق",
        "quick_actions": "إجراءات سريعة",
        "add_lead": "إضافة عميل",
        "create_task": "إنشاء مهمة",
        "view_all": "عرض الكل",
        "customer_name": "اسم العميل",
        "email": "البريد الإلكتروني",
        "phone": "رقم الهاتف",
        "destination": "الوجهة",
        "start_date": "تاريخ السفر",
        "end_date": "تاريخ العودة",
        "travelers": "عدد المسافرين",
        "budget": "الميزانية التقديرية",
        "currency": "العملة",
        "notes": "ملاحظات",
        "save_lead": "حفظ العميل",
        "search": "ابحث بالاسم أو الوجهة",
        "all_statuses": "كل الحالات",
        "new": "جديد",
        "needs_information": "يحتاج معلومات",
        "qualified": "مؤهل",
        "pending_approval": "بانتظار الاعتماد",
        "approved": "معتمد",
        "rejected": "مرفوض",
        "lead_status": "حالة العميل",
        "no_leads": "لا يوجد عملاء بعد. أضف أول عميل للبدء.",
        "no_tasks": "لا توجد مهام في هذا العرض.",
        "task_type": "نوع المهمة",
        "qualify_lead": "تأهيل العميل",
        "build_offer": "إعداد مسودة عرض",
        "select_lead": "اختر العميل",
        "instructions": "تعليمات إضافية للفريق",
        "submit_task": "إرسال المهمة للفريق",
        "approve": "اعتماد النتيجة",
        "reject": "رفض النتيجة",
        "decision_notes": "ملاحظات المراجعة",
        "confidence": "مستوى الثقة",
        "assigned_to": "الوكيل المسؤول",
        "result": "نتيجة الوكيل",
        "assumptions": "الافتراضات",
        "risks": "المخاطر والتنبيهات",
        "next_action": "الخطوة التالية",
        "edit_json": "تعديل نتيجة الوكيل (متقدم)",
        "save_edit": "حفظ التعديل للمراجعة",
        "agent_count": "عدد الوكلاء",
        "leads_week": "عملاء جدد خلال 7 أيام",
        "tasks_week": "مهام خلال 7 أيام",
        "pending": "قيد المراجعة",
        "activity": "توزيع حالات المهام",
        "no_data": "لا توجد بيانات كافية للرسم حتى الآن.",
        "not_auth": "هذا النموذج الأولي يستخدم معرّف وكالة للتجربة فقط، وليس نظام تسجيل دخول أو صلاحيات إنتاجي.",
        "api_address": "عنوان خدمة API",
        "runtime": "بيئة التشغيل",
        "refresh": "تحديث البيانات",
        "create_success": "تم حفظ العميل بنجاح.",
        "task_success": "تم إرسال المهمة إلى الفريق وأصبحت بانتظار اعتمادك.",
        "approve_success": "تم اعتماد المهمة.",
        "reject_success": "تم رفض المهمة.",
        "edit_success": "تم حفظ التعديل، وما زالت المهمة بانتظار الاعتماد.",
        "invalid_json": "صيغة JSON غير صحيحة. راجع النص وحاول مرة أخرى.",
        "empty_required": "أكمل اسم العميل والبيانات المطلوبة.",
        "offer_warning": "الباقات هياكل تخطيطية فقط؛ لا توجد أسعار أو توافر مؤكد.",
        "no_live": "الوكلاء يعملون حاليًا في وضع المحاكاة ولا يتصلون بموردين أو عملاء.",
        "status": "الحالة",
        "date": "تاريخ الإضافة",
        "package": "المستوى",
        "price": "السعر",
        "availability": "التوافر",
        "not_verified": "غير متحقق",
        "not_provided": "غير محدد",
        "data_completeness": "اكتمال البيانات",
        "qualification": "قرار التأهيل",
        "ready_for_offer": "جاهز مبدئيًا لإعداد مسودة عرض",
        "needs_more_info": "يحتاج استكمال بيانات أساسية",
        "critical_missing": "بيانات أساسية ناقصة",
        "recommended_missing": "بيانات إضافية يُنصح باستكمالها",
        "follow_up_questions": "أسئلة المتابعة المقترحة",
        "lead_snapshot": "ملخص بيانات الطلب",
        "contact_method": "وسيلة التواصل",
        "duration_nights": "مدة الرحلة (ليالٍ)",
        "budget_per_traveler": "الميزانية التقديرية للفرد",
        "preferences": "التفضيلات والمتطلبات",
        "not_recorded": "غير مسجل",
        "no_critical_gaps": "لا توجد بيانات أساسية ناقصة.",
        "no_recommended_gaps": "البيانات الإضافية مكتملة.",
        "generate_report": "إنشاء التقرير الأسبوعي الذكي",
        "report_generated": "تم إنشاء مسودة التقرير وأصبحت بانتظار مراجعتك.",
        "report_summary": "الملخص التنفيذي",
        "report_highlights": "أهم المؤشرات",
        "report_actions": "التوصيات والخطوات التالية",
        "report_limitations": "حدود التقرير",
        "report_status": "حالة التقرير",
        "workspace_profile": "ملف الوكالة",
        "workspace_plan": "الخطة الحالية",
        "workspace_currency": "العملة الافتراضية",
        "workspace_timezone": "المنطقة الزمنية",
        "audit_history": "سجل النشاط والتغييرات",
        "audit_action": "الإجراء",
        "audit_entity": "العنصر",
        "audit_actor": "المنفذ",
        "audit_time": "التاريخ",
        "prototype_security_warning": "بيئة تجريبية: معرّف الوكالة ليس تسجيل دخول ولا يوفر صلاحيات أو عزلًا أمنيًا إنتاجيًا.",
        "no_reports_yet": "لم يتم إنشاء تقرير سردي بعد.",

        "sales": "المبيعات",
        "decided_tasks": "المهام التي تم البت فيها",
        "approval_rate": "نسبة الاعتماد",
        "avg_duration": "متوسط زمن التنفيذ",
        "lead_pipeline": "مسار العملاء",
        "task_performance": "أداء المهام",
        "department_activity": "نشاط الأقسام",
        "task_mix": "توزيع أنواع المهام",
        "report_period": "الفترة المغطاة",
        "export_report": "تصدير ملخص التقرير",
        "no_decisions": "لا توجد قرارات اعتماد أو رفض خلال الفترة.",
        "no_tasks_period": "لا توجد مهام مسجلة خلال الفترة.",
        "new_leads": "عملاء جدد",
        "info_leads": "يحتاجون معلومات",
        "qualified_leads": "عملاء مؤهلون",
        "quick_qualification": "تأهيل عميل",
        "quick_offer": "إعداد عرض",
        "quick_marketing": "محتوى تسويقي",
        "tasks_help_title": "اختصارات العمل",
        "qualify_lead_help": "مراجعة اكتمال بيانات العميل وتحديد الأسئلة الناقصة.",
        "build_offer_help": "إعداد هيكل عرض مبدئي دون أسعار أو توافر غير مؤكد.",
        "prepare_cost_sheet_help": "تجهيز ورقة تكاليف فارغة لحين إدخال عروض الموردين الفعلية.",
        "draft_invoice_help": "تجهيز هيكل فاتورة داخلي دون رقم رسمي أو مبلغ مستحق.",
        "draft_marketing_content_help": "كتابة مسودة محتوى عربي وإنجليزي من البيانات المسجلة فقط.",
        "draft_customer_reply_help": "صياغة رد داخلي مقترح؛ لن يتم إرساله للعميل.",
        "classify_complaint_help": "تصنيف أولي للشكوى وتحديد ما يحتاج مراجعة بشرية.",

        "prepare_cost_sheet": "إعداد ورقة تكاليف",
        "draft_invoice": "إعداد مسودة فاتورة",
        "draft_marketing_content": "إنشاء محتوى تسويقي",
        "draft_customer_reply": "صياغة رد للعميل",
        "classify_complaint": "تصنيف شكوى",
        "finance": "المالية",
        "marketing": "التسويق",
        "customer_success": "خدمة العملاء",
        "reporting": "التقارير",
        "copy_ar": "المحتوى العربي",
        "copy_en": "المحتوى الإنجليزي",
        "costing_inputs": "بيانات التكلفة المطلوبة",
        "missing_before_issuance": "متطلبات استكمال الفاتورة",
        "recommended_steps": "خطوات المعالجة المقترحة",
    },
    "en": {
        "nav": "WORKSPACE",
        "overview": "Overview",
        "leads": "Leads",
        "tasks": "Task center",
        "team": "AI team",
        "reports": "Reports",
        "settings": "Settings",
        "agency": "Agency ID",
        "language": "Language",
        "connected": "API connected",
        "disconnected": "API disconnected",
        "mock": "Mock mode",
        "heading_overview": "Command center",
        "sub_overview": "A clear view of your agency operations, team activity, and work awaiting your approval.",
        "heading_leads": "Lead management",
        "sub_leads": "Capture travel requests in one place and turn them into trackable work.",
        "heading_tasks": "Review & approvals",
        "sub_tasks": "Review agent outputs, edit them, then approve or reject.",
        "heading_team": "ATLAS AI team",
        "sub_team": "Explore the current team structure, responsibilities, and workload.",
        "heading_reports": "Performance reports",
        "sub_reports": "A summary of your agency activity over the last seven days.",
        "heading_settings": "Workspace settings",
        "sub_settings": "Configure API connection and demo agency context.",
        "sub_settings": "Configure this prototype workspace.",
        "total_leads": "Total leads",
        "pending_tasks": "Awaiting approval",
        "approved_tasks": "Approved tasks",
        "total_tasks": "Total tasks",
        "recent_leads": "Recent leads",
        "recent_tasks": "Latest team activity",
        "quick_actions": "Quick actions",
        "add_lead": "Add a lead",
        "create_task": "Create a task",
        "view_all": "View all",
        "customer_name": "Customer name",
        "email": "Email",
        "phone": "Phone",
        "destination": "Destination",
        "start_date": "Travel start",
        "end_date": "Travel end",
        "travelers": "Travelers",
        "budget": "Estimated budget",
        "currency": "Currency",
        "notes": "Notes",
        "save_lead": "Save lead",
        "search": "Search by name or destination",
        "all_statuses": "All statuses",
        "new": "New",
        "needs_information": "Needs information",
        "qualified": "Qualified",
        "pending_approval": "Pending approval",
        "approved": "Approved",
        "rejected": "Rejected",
        "lead_status": "Lead status",
        "no_leads": "No leads yet. Add your first lead to get started.",
        "no_tasks": "No tasks in this view.",
        "task_type": "Task type",
        "qualify_lead": "Qualify lead",
        "build_offer": "Build offer draft",
        "select_lead": "Select lead",
        "instructions": "Additional team instructions",
        "submit_task": "Send task to team",
        "approve": "Approve result",
        "reject": "Reject result",
        "decision_notes": "Review notes",
        "confidence": "Confidence",
        "assigned_to": "Assigned agent",
        "result": "Agent result",
        "assumptions": "Assumptions",
        "risks": "Risks & warnings",
        "next_action": "Next action",
        "edit_json": "Edit agent output (advanced)",
        "save_edit": "Save edit for review",
        "agent_count": "Agents",
        "leads_week": "New leads · 7 days",
        "tasks_week": "Tasks · 7 days",
        "pending": "Under review",
        "activity": "Task status distribution",
        "no_data": "Not enough activity to chart yet.",
        "not_auth": "This prototype uses an agency ID for testing only; it is not production authentication or access control.",
        "api_address": "API service URL",
        "runtime": "Runtime",
        "refresh": "Refresh data",
        "create_success": "Lead saved successfully.",
        "task_success": "Task sent to the team and is awaiting your approval.",
        "approve_success": "Task approved.",
        "reject_success": "Task rejected.",
        "edit_success": "Edit saved; task remains pending approval.",
        "invalid_json": "Invalid JSON. Review the content and try again.",
        "empty_required": "Complete the customer name and required details.",
        "offer_warning": "Packages are planning structures only; no price or availability is confirmed.",
        "no_live": "Agents currently run in mock mode and do not contact suppliers or customers.",
        "status": "Status",
        "date": "Created",
        "package": "Tier",
        "price": "Price",
        "availability": "Availability",
        "not_verified": "Not verified",
        "not_provided": "Not provided",
        "prepare_cost_sheet": "Prepare cost worksheet",
        "draft_invoice": "Draft invoice",
        "draft_marketing_content": "Draft marketing content",
        "draft_customer_reply": "Draft customer reply",
        "classify_complaint": "Classify complaint",
        "finance": "Finance",
        "marketing": "Marketing",
        "customer_success": "Customer Success",
        "reporting": "Reporting",
        "copy_ar": "Arabic copy",
        "copy_en": "English copy",
        "costing_inputs": "Required costing inputs",
        "missing_before_issuance": "Required before invoice issuance",
        "recommended_steps": "Recommended handling steps",
        "data_completeness": "Data completeness",
        "qualification": "Qualification decision",
        "ready_for_offer": "Ready for an initial offer draft",
        "needs_more_info": "More essential information is needed",
        "critical_missing": "Missing essential information",
        "recommended_missing": "Additional details recommended",
        "follow_up_questions": "Suggested follow-up questions",
        "lead_snapshot": "Lead snapshot",
        "contact_method": "Contact method",
        "duration_nights": "Trip duration (nights)",
        "budget_per_traveler": "Estimated budget per traveler",
        "preferences": "Preferences and requirements",
        "not_recorded": "Not recorded",
        "no_critical_gaps": "No essential information is missing.",
        "no_recommended_gaps": "Recommended details are complete.",
        "generate_report": "Generate weekly management report",
        "report_generated": "Report draft created and is awaiting your review.",
        "report_summary": "Executive summary",
        "report_highlights": "Key highlights",
        "report_actions": "Recommendations and next steps",
        "report_limitations": "Report limitations",
        "report_status": "Report status",
        "workspace_profile": "Agency workspace",
        "workspace_plan": "Current plan",
        "workspace_currency": "Default currency",
        "workspace_timezone": "Timezone",
        "audit_history": "Activity and change log",
        "audit_action": "Action",
        "audit_entity": "Record",
        "audit_actor": "Actor",
        "audit_time": "Date",
        "prototype_security_warning": "Prototype environment: agency ID is not a login and does not provide production-grade authorization or tenant security.",
        "no_reports_yet": "No narrative report has been generated yet.",

        "sales": "Sales",
        "decided_tasks": "Tasks with a decision",
        "approval_rate": "Approval rate",
        "avg_duration": "Average processing time",
        "lead_pipeline": "Lead pipeline",
        "task_performance": "Task performance",
        "department_activity": "Department activity",
        "task_mix": "Task type mix",
        "report_period": "Reporting period",
        "export_report": "Export report summary",
        "no_decisions": "No approval or rejection decisions during this period.",
        "no_tasks_period": "No tasks recorded during this period.",
        "new_leads": "New leads",
        "info_leads": "Need information",
        "qualified_leads": "Qualified",
        "quick_qualification": "Qualify a lead",
        "quick_offer": "Build an offer",
        "quick_marketing": "Draft marketing content",
        "tasks_help_title": "Task guide",
        "qualify_lead_help": "Check lead completeness and identify missing follow-up questions.",
        "build_offer_help": "Create an initial offer structure without unverified prices or availability.",
        "prepare_cost_sheet_help": "Prepare an empty costing worksheet until real supplier quotes are entered.",
        "draft_invoice_help": "Prepare an internal invoice shell without an official number or amount due.",
        "draft_marketing_content_help": "Draft Arabic and English content using recorded facts only.",
        "draft_customer_reply_help": "Prepare an internal reply draft; nothing will be sent to the customer.",
        "classify_complaint_help": "Create a preliminary complaint classification for human review.",

    },
}

def t(key: str) -> str:
    return TEXT[st.session_state.language].get(key, key)


def api_get(path: str, agency_id: str, default: Any) -> Any:
    try:
        return api_request("GET", path, agency_id=agency_id)
    except APIError as exc:
        st.warning(str(exc))
        return default


def status_text(value: str) -> str:
    return t(value) if value in TEXT["en"] else value


def header(title: str, subtitle: str) -> None:
    direction = "rtl" if st.session_state.language == "ar" else "ltr"
    st.markdown(
        f"""
        <div class="page-heading" dir="{direction}">
          <div class="eyebrow">ATLAS AI <span> / </span> CONTROL CENTER</div>
          <h1>{title}</h1>
          <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def metric_card(label: str, value: Any, icon: str, accent: str = "") -> None:
    st.markdown(
        f"""
        <div class="metric-card {accent}">
          <div class="metric-top"><span>{label}</span><span class="metric-icon">{icon}</span></div>
          <div class="metric-value">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def show_error(message: str) -> None:
    st.error(message)


def render_lead_form(agency_id: str) -> None:
    with st.expander("＋  " + t("add_lead"), expanded=False):
        with st.form("new_lead_form", clear_on_submit=True):
            c1, c2 = st.columns(2)
            with c1:
                name = st.text_input(t("customer_name") + " *")
                phone = st.text_input(t("phone"))
                destination = st.text_input(t("destination"))
                start = st.date_input(t("start_date"), value=date.today() + timedelta(days=30))
            with c2:
                email = st.text_input(t("email"))
                travelers = st.number_input(t("travelers"), min_value=1, max_value=100, value=2)
                budget = st.number_input(t("budget"), min_value=0.0, value=0.0, step=500.0)
                currency = st.selectbox(t("currency"), ["EGP", "SAR", "USD", "AED", "KWD"])
                end = st.date_input(t("end_date"), value=date.today() + timedelta(days=35))
            notes = st.text_area(t("notes"), height=80)
            submitted = st.form_submit_button(t("save_lead"), type="primary", use_container_width=True)
            if submitted:
                if not name.strip():
                    st.error(t("empty_required"))
                elif end < start:
                    st.error("تاريخ العودة يجب أن يكون في نفس يوم السفر أو بعده." if st.session_state.language == "ar" else "Return date must be on or after departure.")
                else:
                    payload = {
                        "customer_name": name.strip(),
                        "email": email.strip() or None,
                        "phone": phone.strip() or None,
                        "destination": destination.strip() or None,
                        "travel_start": start.isoformat(),
                        "travel_end": end.isoformat(),
                        "travelers": int(travelers),
                        "budget_amount": float(budget) if budget > 0 else None,
                        "currency_code": currency,
                        "notes": notes.strip() or None,
                    }
                    try:
                        api_request("POST", "/api/leads", agency_id=agency_id, payload=payload)
                        st.success(t("create_success"))
                        st.rerun()
                    except APIError as exc:
                        show_error(str(exc))


def render_overview(agency_id: str, api_ok: bool) -> None:
    header(t("heading_overview"), t("sub_overview"))
    leads = api_get("/api/leads?limit=100", agency_id, [])
    tasks = api_get("/api/tasks?limit=100", agency_id, [])
    agents = api_get("/api/agents", agency_id, [])
    pending = [task for task in tasks if task.get("status") == "pending_approval"]
    approved = [task for task in tasks if task.get("status") == "approved"]

    cards = st.columns(4)
    values = [
        (t("total_leads"), len(leads), "◈", ""),
        (t("pending_tasks"), len(pending), "◷", "metric-warm"),
        (t("approved_tasks"), len(approved), "✓", "metric-cool"),
        (t("agent_count"), len(agents), "✳", ""),
    ]
    for col, (label, value, icon, accent) in zip(cards, values):
        with col:
            metric_card(label, value, icon, accent)

    st.markdown("<div class='section-gap'></div>", unsafe_allow_html=True)
    left, right = st.columns([1.12, 0.88], gap="large")
    with left:
        st.markdown(f"### {t('recent_tasks')}")
        if not tasks:
            st.info(t("no_tasks"))
        else:
            for task in tasks[:5]:
                label = task.get("title") or task.get("task_type", "Task")
                status = status_text(task.get("status", ""))
                agent = task.get("assigned_agent_id", "")
                st.markdown(
                    f"""
                    <div class="list-row">
                      <div><strong>{label}</strong><small>{agent}</small></div>
                      <span class="status-pill status-{task.get('status','new')}">{status}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    with right:
        st.markdown(f"### {t('recent_leads')}")
        if not leads:
            st.info(t("no_leads"))
        else:
            for lead in leads[:5]:
                st.markdown(
                    f"""
                    <div class="list-row">
                      <div><strong>{lead.get('customer_name','—')}</strong><small>{lead.get('destination') or '—'} · {lead.get('travelers',1)} pax</small></div>
                      <span class="subtle">{lead.get('currency_code','EGP')}</span>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )

    st.markdown(f"### {t('quick_actions')}")
    q1, q2, q3 = st.columns(3)
    with q1:
        if st.button("＋  " + t("add_lead"), use_container_width=True, key="quick_add_lead"):
            st.session_state.page = "leads"
            st.rerun()
    with q2:
        if st.button("◷  " + t("create_task"), use_container_width=True, key="quick_task"):
            st.session_state.page = "tasks"
            st.rerun()
    with q3:
        if st.button("✓  " + t("pending_tasks"), use_container_width=True, key="quick_approval"):
            st.session_state.page = "tasks"
            st.session_state.task_filter = "pending_approval"
            st.rerun()
    if not api_ok:
        st.warning(t("disconnected"))


def render_leads(agency_id: str) -> None:
    header(t("heading_leads"), t("sub_leads"))
    render_lead_form(agency_id)
    leads = api_get("/api/leads?limit=500", agency_id, [])
    search = st.text_input(t("search"), placeholder=t("search"))
    statuses = ["all", "new", "needs_information", "qualified"]
    status_options = [t("all_statuses")] + [status_text(s) for s in statuses[1:]]
    selected_status = st.selectbox(t("lead_status"), status_options)
    filtered = leads
    if search:
        needle = search.strip().casefold()
        filtered = [
            lead for lead in filtered
            if needle in (lead.get("customer_name") or "").casefold()
            or needle in (lead.get("destination") or "").casefold()
        ]
    if selected_status != t("all_statuses"):
        wanted = next((s for s in statuses[1:] if status_text(s) == selected_status), selected_status)
        filtered = [lead for lead in filtered if lead.get("status") == wanted]

    st.caption(f"{len(filtered)} / {len(leads)}")
    if not filtered:
        st.info(t("no_leads"))
        return

    table = []
    for lead in filtered:
        table.append({
            t("customer_name"): lead.get("customer_name"),
            t("destination"): lead.get("destination") or "—",
            t("travelers"): lead.get("travelers"),
            t("budget"): (
                f"{lead.get('budget_amount'):,.0f} {lead.get('currency_code')}"
                if lead.get("budget_amount") is not None else "—"
            ),
            t("lead_status"): status_text(lead.get("status", "")),
            "ID": lead.get("id"),
        })
    st.dataframe(pd.DataFrame(table), use_container_width=True, hide_index=True)


def render_tasks(agency_id: str) -> None:
    header(t("heading_tasks"), t("sub_tasks"))
    leads = api_get("/api/leads?limit=500", agency_id, [])
    if leads:
        with st.expander("＋  " + t("create_task"), expanded=False):
            lead_map = {f"{lead['customer_name']} — {lead.get('destination') or 'بدون وجهة'}": lead["id"] for lead in leads}
            with st.form("new_task_form"):
                chosen_lead = st.selectbox(t("select_lead"), list(lead_map.keys()))
                task_type = st.selectbox(
                    t("task_type"),
                    [
                        "qualify_lead",
                        "build_offer",
                        "prepare_cost_sheet",
                        "draft_invoice",
                        "draft_marketing_content",
                        "draft_customer_reply",
                        "classify_complaint",
                    ],
                    format_func=lambda value: t(value),
                )
                st.caption(t(f"{task_type}_help"))
                instructions = st.text_area(t("instructions"), height=80)
                submit = st.form_submit_button(t("submit_task"), type="primary", use_container_width=True)
                if submit:
                    try:
                        api_request(
                            "POST",
                            "/api/tasks",
                            agency_id=agency_id,
                            payload={
                                "task_type": task_type,
                                "lead_id": lead_map[chosen_lead],
                                "instructions": instructions.strip() or None,
                            },
                        )
                        st.success(t("task_success"))
                        st.rerun()
                    except APIError as exc:
                        show_error(str(exc))
    else:
        st.info(t("no_leads"))

    tasks = api_get("/api/tasks?limit=200", agency_id, [])
    filter_values = ["all", "pending_approval", "approved", "rejected"]
    chosen_filter = st.selectbox(
        t("status"),
        filter_values,
        index=1 if st.session_state.get("task_filter") == "pending_approval" else 0,
        format_func=lambda value: t("all_statuses") if value == "all" else status_text(value),
        key="task_filter_select",
    )
    st.session_state.task_filter = chosen_filter
    if chosen_filter != "all":
        tasks = [task for task in tasks if task.get("status") == chosen_filter]

    if not tasks:
        st.info(t("no_tasks"))
        return

    for task in tasks:
        task_status = task.get("status", "")
        title = task.get("title") or task.get("task_type", "Task")
        with st.expander(f"{title}   ·   {status_text(task_status)}", expanded=task_status == "pending_approval"):
            c1, c2, c3 = st.columns(3)
            response = task.get("result") or {}
            result = response.get("result", {})
            c1.metric(t("assigned_to"), task.get("assigned_agent_id", "—"))
            if task.get("task_type") == "qualify_lead" and isinstance(result, dict) and "completeness_score" in result:
                c2.metric(t("data_completeness"), f"{result.get('completeness_score', 0)}%")
            elif response.get("confidence_calibrated") is False:
                c2.metric(t("confidence"), "—")
            else:
                c2.metric(t("confidence"), f"{task.get('confidence', 0):.0%}")
            c3.metric(t("status"), status_text(task_status))
            st.markdown(f"**{t('result')}**")
            if isinstance(result, dict):
                if result.get("summary"):
                    st.write(result["summary"])

                if task.get("task_type") == "qualify_lead":
                    qualification_status = result.get("qualification_status")
                    if qualification_status == "qualified":
                        st.success(t("ready_for_offer"))
                    else:
                        st.warning(t("needs_more_info"))

                    field_labels = {
                        "destination": t("destination"),
                        "travel_start": t("start_date"),
                        "travel_end": t("end_date"),
                        "travelers": t("travelers"),
                        "contact_method": t("contact_method"),
                        "budget_amount": t("budget"),
                        "preferences": t("preferences"),
                    }
                    critical = result.get("critical_missing_fields", result.get("missing_fields", []))
                    recommended = result.get("recommended_missing_fields", [])
                    if critical:
                        st.error(t("critical_missing") + ": " + "، ".join(field_labels.get(key, key) for key in critical))
                    else:
                        st.success(t("no_critical_gaps"))
                    if recommended:
                        st.warning(t("recommended_missing") + ": " + "، ".join(field_labels.get(key, key) for key in recommended))
                    else:
                        st.caption(t("no_recommended_gaps"))

                    snapshot = result.get("lead_snapshot") or {}
                    snapshot_labels = {
                        "customer_name": t("customer_name"),
                        "destination": t("destination"),
                        "travel_start": t("start_date"),
                        "travel_end": t("end_date"),
                        "duration_nights": t("duration_nights"),
                        "travelers": t("travelers"),
                        "contact_method": t("contact_method"),
                        "budget": t("budget"),
                        "budget_per_traveler": t("budget_per_traveler"),
                        "preferences": t("preferences"),
                    }
                    snapshot_rows = [
                        {"البيان" if st.session_state.language == "ar" else "Detail": snapshot_labels.get(key, key),
                         "القيمة" if st.session_state.language == "ar" else "Value": value if value not in (None, "") else t("not_recorded")}
                        for key, value in snapshot.items()
                        if key in snapshot_labels
                    ]
                    if snapshot_rows:
                        st.markdown(f"**{t('lead_snapshot')}**")
                        st.dataframe(pd.DataFrame(snapshot_rows), use_container_width=True, hide_index=True)

                    questions = result.get("recommended_questions", [])
                    if questions:
                        with st.expander(t("follow_up_questions")):
                            for index, question in enumerate(questions, start=1):
                                st.write(f"{index}. {question}")

                if result.get("packages"):
                    st.warning(t("offer_warning"))
                    st.dataframe(pd.DataFrame(result["packages"]), use_container_width=True, hide_index=True)

                if result.get("line_items"):
                    st.markdown(f"**{t('costing_inputs')}**")
                    st.dataframe(pd.DataFrame(result["line_items"]), use_container_width=True, hide_index=True)
                    if result.get("customer_budget"):
                        st.caption(
                            f"{t('budget')}: {result['customer_budget']['amount']:,.2f} "
                            f"{result['customer_budget']['currency']} — {result['customer_budget']['meaning']}"
                        )
                    st.caption("لم يتم حساب أي إجمالي لعدم توافر عروض الموردين." if st.session_state.language == "ar" else "No totals were calculated because supplier quotes are missing.")

                for key in ("copy_ar", "copy_en", "reply_ar", "reply_en"):
                    if result.get(key):
                        label = t(key) if key in {"copy_ar", "copy_en"} else ("مسودة الرد بالعربية" if st.session_state.language == "ar" and key == "reply_ar" else "English reply draft" if key == "reply_en" else "مسودة الرد بالعربية")
                        st.text_area(label, value=result[key], height=130, disabled=True, key=f"{key}_{task['id']}")

                if result.get("missing_before_issuance"):
                    st.warning(t("missing_before_issuance"))
                    for item in result["missing_before_issuance"]:
                        st.write("• " + str(item))

                if result.get("required_inputs"):
                    st.markdown(f"**{t('costing_inputs')}**")
                    for item in result["required_inputs"]:
                        st.write("• " + str(item))

                if result.get("recommended_steps"):
                    st.markdown(f"**{t('recommended_steps')}**")
                    if result.get("priority"):
                        st.metric(
                            "الأولوية" if st.session_state.language == "ar" else "Priority",
                            result["priority"],
                        )
                    for item in result["recommended_steps"]:
                        st.write("• " + str(item))

                if result.get("fact_check"):
                    st.caption(" | ".join(str(item) for item in result["fact_check"]))

                with st.popover(t("result")):
                    st.json(result)
            else:
                st.write(result)

            details = st.columns(2)
            with details[0]:
                st.markdown(f"**{t('assumptions')}**")
                for item in response.get("assumptions", []):
                    st.write("• " + str(item))
            with details[1]:
                st.markdown(f"**{t('risks')}**")
                for item in response.get("risks", []):
                    st.write("• " + str(item))
            st.info(f"{t('next_action')}: {response.get('next_action', '—')}")

            if task_status == "pending_approval":
                notes = st.text_input(t("decision_notes"), key=f"notes_{task['id']}")
                approve_col, reject_col = st.columns(2)
                with approve_col:
                    if st.button(t("approve"), type="primary", key=f"approve_{task['id']}", use_container_width=True):
                        try:
                            api_request(
                                "POST", f"/api/tasks/{task['id']}/approve",
                                agency_id=agency_id, payload={"notes": notes or None},
                            )
                            st.success(t("approve_success"))
                            st.rerun()
                        except APIError as exc:
                            show_error(str(exc))
                with reject_col:
                    if st.button(t("reject"), key=f"reject_{task['id']}", use_container_width=True):
                        try:
                            api_request(
                                "POST", f"/api/tasks/{task['id']}/reject",
                                agency_id=agency_id, payload={"reason": notes or "Rejected by owner"},
                            )
                            st.success(t("reject_success"))
                            st.rerun()
                        except APIError as exc:
                            show_error(str(exc))

                with st.popover(t("edit_json")):
                    raw = st.text_area(
                        "JSON",
                        value=json.dumps(response, ensure_ascii=False, indent=2),
                        height=260,
                        key=f"edit_json_{task['id']}",
                    )
                    if st.button(t("save_edit"), key=f"save_edit_{task['id']}"):
                        try:
                            edited = json.loads(raw)
                            api_request(
                                "POST", f"/api/tasks/{task['id']}/edit",
                                agency_id=agency_id,
                                payload={"result": edited, "notes": notes or "Edited by owner"},
                            )
                            st.success(t("edit_success"))
                            st.rerun()
                        except json.JSONDecodeError:
                            st.error(t("invalid_json"))
                        except APIError as exc:
                            show_error(str(exc))


def render_team(agency_id: str) -> None:
    header(t("heading_team"), t("sub_team"))
    agents = api_get("/api/agents", agency_id, [])
    if not agents:
        st.info(t("no_data"))
        return

    general_manager = next((item for item in agents if item["agent_id"] == "general_manager"), None)
    if general_manager:
        st.markdown(
            f"""
            <div class="org-card org-top">
              <div class="org-avatar">✦</div><div><strong>{general_manager['name']}</strong>
              <small>{general_manager['role']}</small></div><span class="org-tag">LEAD</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

    department_order = ["Sales", "Finance", "Marketing", "Customer Success", "Reporting"]
    department_labels = {
        "Sales": t("sales"),
        "Finance": t("finance"),
        "Marketing": t("marketing"),
        "Customer Success": t("customer_success"),
        "Reporting": t("reporting"),
    }
    for department in department_order:
        members = [item for item in agents if item.get("department") == department]
        if not members:
            continue
        st.markdown("<div class='org-connector'></div>", unsafe_allow_html=True)
        st.markdown(f"### {department_labels[department]}")
        cols = st.columns(2)
        for index, agent in enumerate(members):
            with cols[index % 2]:
                is_manager = agent.get("is_manager", False)
                st.markdown(
                    f"""
                    <div class="org-card" style="min-height:112px;margin-bottom:12px;">
                      <div class="org-avatar">{"◈" if is_manager else "✧"}</div>
                      <div><strong>{agent['name']}</strong>
                      <small>{agent['role']}</small>
                      <div class="agent-meta">{agent.get('assigned_tasks_count',0)} {t('total_tasks')}</div></div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
    st.markdown(f"### {t('no_live')}")
    st.caption(t("not_auth"))


def render_reports(agency_id: str) -> None:
    header(t("heading_reports"), t("sub_reports"))

    action_col, hint_col = st.columns([0.36, 0.64])
    with action_col:
        generate_clicked = st.button(
            "✦  " + t("generate_report"),
            type="primary",
            use_container_width=True,
        )
    with hint_col:
        st.caption(t("prototype_security_warning"))

    if generate_clicked:
        try:
            api_request(
                "POST",
                "/api/reports/weekly/generate",
                agency_id=agency_id,
                payload={"instructions": None},
            )
            st.success(t("report_generated"))
            st.rerun()
        except APIError as exc:
            show_error(str(exc))

    report = api_get("/api/reports/weekly", agency_id, {})
    if not report:
        return

    generated_reports = api_get(
        "/api/tasks?task_type=generate_weekly_report&limit=20",
        agency_id,
        [],
    )
    if generated_reports:
        latest_report = generated_reports[0]
        response = latest_report.get("result") or {}
        narrative = response.get("result") or {}
        summary = (
            narrative.get("executive_summary_ar")
            if st.session_state.language == "ar"
            else narrative.get("executive_summary_en")
        )
        with st.container(border=True):
            st.markdown(f"### {t('report_summary')}")
            st.write(summary or t("no_reports_yet"))

            highlights = (
                narrative.get("highlights_ar", [])
                if st.session_state.language == "ar"
                else narrative.get("highlights_en", [])
            )
            if highlights:
                st.markdown(f"**{t('report_highlights')}**")
                for item in highlights:
                    st.write("• " + str(item))

            actions = (
                narrative.get("recommended_actions_ar", [])
                if st.session_state.language == "ar"
                else narrative.get("recommended_actions_en", [])
            )
            if actions:
                st.markdown(f"**{t('report_actions')}**")
                for item in actions:
                    st.write("• " + str(item))

            limitations = (
                narrative.get("limitations_ar", [])
                if st.session_state.language == "ar"
                else narrative.get("limitations_en", [])
            )
            with st.expander(t("report_limitations")):
                for item in limitations:
                    st.write("• " + str(item))

            status_col, date_col = st.columns(2)
            status_col.metric(t("report_status"), status_text(latest_report.get("status", "")))
            date_col.caption(str(latest_report.get("created_at", ""))[:19])

            if latest_report.get("status") == "pending_approval":
                notes = st.text_input(t("decision_notes"), key=f"report_notes_{latest_report['id']}")
                approve_col, reject_col = st.columns(2)
                with approve_col:
                    if st.button(
                        t("approve"),
                        type="primary",
                        key=f"approve_report_{latest_report['id']}",
                        use_container_width=True,
                    ):
                        try:
                            api_request(
                                "POST",
                                f"/api/tasks/{latest_report['id']}/approve",
                                agency_id=agency_id,
                                payload={"notes": notes or None},
                            )
                            st.success(t("approve_success"))
                            st.rerun()
                        except APIError as exc:
                            show_error(str(exc))
                with reject_col:
                    if st.button(
                        t("reject"),
                        key=f"reject_report_{latest_report['id']}",
                        use_container_width=True,
                    ):
                        try:
                            api_request(
                                "POST",
                                f"/api/tasks/{latest_report['id']}/reject",
                                agency_id=agency_id,
                                payload={"reason": notes or "Rejected by owner"},
                            )
                            st.success(t("reject_success"))
                            st.rerun()
                        except APIError as exc:
                            show_error(str(exc))
    else:
        st.info(t("no_reports_yet"))

    period_start = str(report.get("period_start", ""))[:10]
    period_end = str(report.get("period_end", ""))[:10]
    st.caption(f"{t('report_period')}: {period_start} — {period_end}")

    statuses = report.get("task_status_counts", {})
    lead_statuses = report.get("lead_status_counts", {})
    department_counts = report.get("department_task_counts", {})
    task_type_counts = report.get("task_type_counts", {})
    approval_rate = report.get("approval_rate_percent")
    average_duration = report.get("average_task_duration_ms")

    metric_cols = st.columns(4)
    metric_cols[0].metric(t("leads_week"), report.get("leads_created", 0))
    metric_cols[1].metric(t("tasks_week"), report.get("tasks_created", 0))
    metric_cols[2].metric(
        t("approval_rate"),
        f"{approval_rate:.1f}%" if approval_rate is not None else "—",
        help=t("decided_tasks"),
    )
    metric_cols[3].metric(
        t("avg_duration"),
        f"{average_duration:.0f} ms" if average_duration is not None else "—",
    )

    lead_tab, task_tab, team_tab = st.tabs([
        t("lead_pipeline"), t("task_performance"), t("department_activity")
    ])
    with lead_tab:
        lead_labels = {
            "new": t("new_leads"),
            "needs_information": t("info_leads"),
            "qualified": t("qualified_leads"),
        }
        if any(lead_statuses.values()):
            frame = pd.DataFrame({
                "الحالة" if st.session_state.language == "ar" else "Status":
                    [lead_labels.get(key, key) for key in lead_statuses],
                "العدد" if st.session_state.language == "ar" else "Count":
                    list(lead_statuses.values()),
            })
            st.bar_chart(frame.set_index(frame.columns[0]))
        else:
            st.info(t("no_data"))

    with task_tab:
        if any(statuses.values()):
            frame = pd.DataFrame({
                "الحالة" if st.session_state.language == "ar" else "Status":
                    [status_text(key) for key in statuses],
                "العدد" if st.session_state.language == "ar" else "Count":
                    list(statuses.values()),
            })
            st.bar_chart(frame.set_index(frame.columns[0]))
        else:
            st.info(t("no_tasks_period"))
        if task_type_counts:
            frame = pd.DataFrame({
                "نوع المهمة" if st.session_state.language == "ar" else "Task type":
                    [t(key) for key in task_type_counts],
                "العدد" if st.session_state.language == "ar" else "Count":
                    list(task_type_counts.values()),
            })
            st.markdown(f"### {t('task_mix')}")
            st.bar_chart(frame.set_index(frame.columns[0]))

    with team_tab:
        department_labels = {
            "Sales": t("sales"),
            "Finance": t("finance"),
            "Marketing": t("marketing"),
            "Customer Success": t("customer_success"),
            "Reporting": t("reporting"),
        }
        if any(department_counts.values()):
            frame = pd.DataFrame({
                "القسم" if st.session_state.language == "ar" else "Department":
                    [department_labels.get(key, key) for key in department_counts],
                "المهام" if st.session_state.language == "ar" else "Tasks":
                    list(department_counts.values()),
            })
            st.bar_chart(frame.set_index(frame.columns[0]))
            st.dataframe(frame, use_container_width=True, hide_index=True)
        else:
            st.info(t("no_tasks_period"))

    summary_rows = [
        {"المؤشر" if st.session_state.language == "ar" else "Metric": t("leads_week"), "القيمة" if st.session_state.language == "ar" else "Value": report.get("leads_created", 0)},
        {"المؤشر" if st.session_state.language == "ar" else "Metric": t("tasks_week"), "القيمة" if st.session_state.language == "ar" else "Value": report.get("tasks_created", 0)},
        {"المؤشر" if st.session_state.language == "ar" else "Metric": t("pending"), "القيمة" if st.session_state.language == "ar" else "Value": statuses.get("pending_approval", 0)},
        {"المؤشر" if st.session_state.language == "ar" else "Metric": t("approved_tasks"), "القيمة" if st.session_state.language == "ar" else "Value": statuses.get("approved", 0)},
        {"المؤشر" if st.session_state.language == "ar" else "Metric": t("rejected"), "القيمة" if st.session_state.language == "ar" else "Value": statuses.get("rejected", 0)},
        {"المؤشر" if st.session_state.language == "ar" else "Metric": t("approval_rate"), "القيمة" if st.session_state.language == "ar" else "Value": f"{approval_rate:.1f}%" if approval_rate is not None else "—"},
    ]
    csv_data = pd.DataFrame(summary_rows).to_csv(index=False).encode("utf-8-sig")
    st.download_button(
        label=t("export_report"),
        data=csv_data,
        file_name=f"atlas-weekly-report-{period_end or 'summary'}.csv",
        mime="text/csv",
    )

    with st.expander("تفاصيل التقرير" if st.session_state.language == "ar" else "Report details"):
        st.json(report)


def inject_css() -> None:
    st.markdown(
        """
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700;800&family=Inter:wght@400;500;600;700;800&display=swap');
        :root { --atlas-navy:#10243a; --atlas-navy-2:#18344d; --atlas-teal:#16a58c; --atlas-mint:#e4f5f0; --atlas-bg:#f4f7fa; --atlas-ink:#162a3d; --atlas-muted:#728196; }
        html, body, [class*="css"] { font-family:'Cairo','Inter',sans-serif; }
        .stApp { background:var(--atlas-bg); color:var(--atlas-ink); }
        [data-testid="stHeader"] { background:transparent; }
        [data-testid="stSidebar"] { background:linear-gradient(180deg,#10243a 0%,#142d44 100%); border-right:1px solid rgba(255,255,255,.06); }
        [data-testid="stSidebar"] * { color:#e8f0f5 !important; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label { padding:9px 12px; border-radius:10px; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label:hover { background:rgba(255,255,255,.08); }
        [data-testid="stSidebar"] input { color:#10243a !important; }
        .block-container { padding-top:2.2rem; padding-bottom:3rem; max-width:1500px; }
        .brand-lockup { display:flex; align-items:center; gap:12px; padding:8px 4px 28px; }
        .brand-symbol { width:42px;height:42px;border-radius:14px;background:linear-gradient(140deg,#23c3a3,#0f806e);display:flex;align-items:center;justify-content:center;font-size:23px;color:white;box-shadow:0 8px 24px rgba(22,165,140,.22); }
        .brand-name { font-size:20px;font-weight:800;letter-spacing:.06em;color:#fff;line-height:1.1; }
        .brand-sub { font-size:10px;color:#9fb4c7;letter-spacing:.18em;margin-top:5px; }
        .sidebar-caption { color:#88a0b3;font-size:10px;letter-spacing:.16em;font-weight:700;margin:8px 0 9px; }
        .connection-chip { display:inline-flex;align-items:center;gap:7px;padding:7px 11px;border-radius:999px;background:#e7f7f1;color:#127c67;font-size:12px;font-weight:700; }
        .connection-dot { width:7px;height:7px;border-radius:50%;background:#16a58c;display:inline-block; }
        .page-heading { margin-bottom:25px; }
        .eyebrow { color:var(--atlas-teal);font-size:10px;letter-spacing:.18em;font-weight:800;margin-bottom:8px; }
        .eyebrow span { color:#aab6c1;padding:0 5px; }
        .page-heading h1 { font-size:32px;font-weight:800;color:var(--atlas-ink);margin:0 0 7px;line-height:1.3; }
        .page-heading p { color:var(--atlas-muted);font-size:14px;margin:0; }
        .metric-card { background:white;border:1px solid #e7edf2;border-radius:17px;padding:19px 20px;min-height:116px;box-shadow:0 5px 18px rgba(17,42,65,.035); }
        .metric-top { display:flex;justify-content:space-between;align-items:center;color:#78899a;font-size:12px;font-weight:600; }
        .metric-icon { width:32px;height:32px;border-radius:11px;background:#e5f6f1;color:#0d987f;display:flex;align-items:center;justify-content:center;font-size:17px; }
        .metric-value { font-size:29px;font-weight:800;color:var(--atlas-ink);margin-top:7px;line-height:1.2; }
        .metric-warm .metric-icon { background:#fff4e6;color:#d68d28; }
        .metric-cool .metric-icon { background:#e9f1ff;color:#477ed7; }
        .section-gap { height:16px; }
        .list-row { display:flex;justify-content:space-between;align-items:center;gap:12px;padding:13px 0;border-bottom:1px solid #e9eef2; }
        .list-row strong { display:block;color:#20374b;font-size:13px; }
        .list-row small { display:block;color:#8b9aaa;font-size:11px;margin-top:3px; }
        .subtle { color:#73869a;font-size:12px; }
        .status-pill { padding:5px 9px;border-radius:999px;font-size:10px;font-weight:700;white-space:nowrap;background:#eef2f6;color:#697a8c; }
        .status-pending_approval { background:#fff3df;color:#a66b12; }
        .status-approved { background:#e3f6ed;color:#14825f; }
        .status-rejected { background:#fce8e8;color:#b54c4c; }
        .status-new { background:#eaf1fa;color:#4876a9; }
        .org-card { display:flex;align-items:center;gap:13px;background:#fff;border:1px solid #e5edf2;border-radius:15px;padding:15px 17px;box-shadow:0 5px 18px rgba(17,42,65,.035); }
        .org-top,.org-middle { max-width:680px;margin:0 auto; }
        .org-avatar { width:39px;height:39px;flex:0 0 39px;border-radius:12px;background:#e4f5f0;color:#11967d;display:flex;align-items:center;justify-content:center;font-size:19px; }
        .org-card strong { display:block;color:#1c3348;font-size:13px; }
        .org-card small { display:block;color:#7b8a9a;font-size:11px;margin-top:3px;line-height:1.5; }
        .org-tag { margin-left:auto;color:#138d78;font-size:9px;font-weight:800;letter-spacing:.12em;background:#e7f7f1;padding:5px 8px;border-radius:7px; }
        .org-connector { width:1px;height:24px;background:#b7d8ce;margin:0 auto; }
        .org-specialist { display:block;text-align:center;height:100%; }
        .org-specialist .org-avatar { margin:0 auto 9px; }
        .agent-meta { color:#128e79;font-size:11px;font-weight:700;margin-top:12px; }
        div.stButton > button, div.stFormSubmitButton > button { border-radius:10px;min-height:42px;font-weight:700;border:1px solid #dce6ec; }
        div.stButton > button[kind="primary"], div.stFormSubmitButton > button[kind="primary"] { background:#11977f;border:1px solid #11977f;color:white; }
        div.stButton > button:hover, div.stFormSubmitButton > button:hover { border-color:#11977f;color:#0d806d; }
        div.stButton > button[kind="primary"]:hover, div.stFormSubmitButton > button[kind="primary"]:hover { color:white;background:#0b826e; }
        [data-testid="stMetric"] { background:#fff;border:1px solid #e7edf2;border-radius:14px;padding:12px 15px; }
        [data-testid="stExpander"] { background:#fff;border:1px solid #e7edf2;border-radius:14px; }
        [data-testid="stDataFrame"] { border:1px solid #e5edf2;border-radius:12px;overflow:hidden; }
        h3 { color:#21394e;font-weight:800; }
        .stAlert { border-radius:12px; }
        [data-testid="stTabs"] button { font-weight:700; border-radius:10px 10px 0 0; }
        [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] { background:rgba(35,195,163,.18); border:1px solid rgba(35,195,163,.26); }
        .metric-card { transition:transform .18s ease, box-shadow .18s ease; }
        .metric-card:hover { transform:translateY(-2px); box-shadow:0 10px 24px rgba(17,42,65,.08); }
        [data-testid="stDownloadButton"] button { border-radius:10px; font-weight:700; }
        @media (max-width: 720px) {
          .block-container { padding-left:1rem; padding-right:1rem; padding-top:1.2rem; }
          .page-heading h1 { font-size:25px; }
          .metric-card { min-height:96px; padding:14px; }
          .metric-value { font-size:24px; }
        }
        footer { visibility:hidden; }
        </style>
        """,
        unsafe_allow_html=True,
    )


def main() -> None:
    inject_css()
    if "language" not in st.session_state:
        st.session_state.language = "ar"
    if "page" not in st.session_state:
        st.session_state.page = "overview"
    if "agency_id" not in st.session_state:
        st.session_state.agency_id = "demo-agency"

    with st.sidebar:
        st.markdown(
            """
            <div class="brand-lockup">
              <div class="brand-symbol">✦</div>
              <div><div class="brand-name">ATLAS AI</div><div class="brand-sub">TRAVEL OPERATIONS OS</div></div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(f"<div class='sidebar-caption'>{t('nav')}</div>", unsafe_allow_html=True)
        page_keys = ["overview", "leads", "tasks", "team", "reports", "settings"]
        page_labels = [t(key) for key in page_keys]
        try:
            current_index = page_keys.index(st.session_state.page)
        except ValueError:
            current_index = 0
        chosen = st.radio(
            t("nav"),
            page_keys,
            index=current_index,
            format_func=lambda key: {
                "overview": "◫  " + t("overview"),
                "leads": "◈  " + t("leads"),
                "tasks": "◷  " + t("tasks"),
                "team": "✳  " + t("team"),
                "reports": "▥  " + t("reports"),
                "settings": "⚙  " + t("settings"),
            }[key],
            label_visibility="collapsed",
        )
        st.session_state.page = chosen
        st.markdown("---")
        st.markdown(f"<div class='sidebar-caption'>{t('agency')}</div>", unsafe_allow_html=True)
        st.session_state.agency_id = st.text_input(
            t("agency"),
            value=st.session_state.agency_id,
            label_visibility="collapsed",
        ).strip() or "demo-agency"
        st.markdown(f"<div class='sidebar-caption'>{t('language')}</div>", unsafe_allow_html=True)
        language_choice = st.selectbox(
            t("language"),
            ["ar", "en"],
            index=0 if st.session_state.language == "ar" else 1,
            format_func=lambda value: "العربية" if value == "ar" else "English",
            label_visibility="collapsed",
        )
        if language_choice != st.session_state.language:
            st.session_state.language = language_choice
            st.rerun()
        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)
        st.caption("ATLAS AI · Prototype 0.4.0")
        st.caption(t("not_auth"))

    agency_id = st.session_state.agency_id
    try:
        health = api_request("GET", "/health", agency_id=agency_id)
        api_ok = health.get("status") == "ok"
    except APIError:
        api_ok = False

    main_col, status_col, refresh_col = st.columns([0.76, 0.17, 0.07])
    with refresh_col:
        if st.button("↻", help=t("refresh"), use_container_width=True):
            st.rerun()
    with status_col:
        if api_ok:
            st.markdown(
                f"<div class='connection-chip'><span class='connection-dot'></span>{t('connected')}</div>",
                unsafe_allow_html=True,
            )
        else:
            st.error(t("disconnected"))
    with main_col:
        st.caption(f"ATLAS AI  /  {t(st.session_state.page)}")

    if st.session_state.page == "overview":
        render_overview(agency_id, api_ok)
    elif st.session_state.page == "leads":
        render_leads(agency_id)
    elif st.session_state.page == "tasks":
        render_tasks(agency_id)
    elif st.session_state.page == "team":
        render_team(agency_id)
    elif st.session_state.page == "reports":
        render_reports(agency_id)
    else:
        header(t("heading_settings"), t("sub_settings"))
        st.text_input(t("api_address"), value=API_URL, disabled=True)
        workspace = api_get("/api/workspace", agency_id, {})
        if workspace:
            st.markdown(f"### {t('workspace_profile')}")
            st.write(f"**{workspace.get('name', '—')}**")
            w1, w2, w3 = st.columns(3)
            w1.metric(t("workspace_plan"), workspace.get("plan", "—"))
            w2.metric(t("workspace_currency"), workspace.get("default_currency", "—"))
            w3.metric(t("workspace_timezone"), workspace.get("timezone", "—"))
            st.caption(f"Agency ID: {workspace.get('agency_id', '—')} · Status: {workspace.get('status', '—')}")
        st.warning(t("prototype_security_warning"))
        st.info(t("mock"))

        audit = api_get("/api/audit?limit=50", agency_id, [])
        st.markdown(f"### {t('audit_history')}")
        if audit:
            rows = [
                {
                    t("audit_action"): event.get("action"),
                    t("audit_entity"): event.get("entity_type"),
                    t("audit_actor"): event.get("actor_id"),
                    t("audit_time"): str(event.get("created_at", ""))[:19],
                }
                for event in audit
            ]
            st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
        else:
            st.info(t("no_data"))


if __name__ == "__main__":
    main()
