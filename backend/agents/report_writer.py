"""Rule-based weekly report writer using only ATLAS AI's recorded metrics."""

from typing import Any


class ReportWriterAgent:
    agent_id = "report_writer"

    def run(self, snapshot: dict[str, Any], instructions: str | None = None) -> dict[str, Any]:
        leads = int(snapshot.get("leads_created", 0))
        tasks = int(snapshot.get("tasks_created", 0))
        lead_status = snapshot.get("lead_status_counts", {})
        task_status = snapshot.get("task_status_counts", {})
        departments = snapshot.get("department_task_counts", {})

        new_leads = int(lead_status.get("new", 0))
        needs_info = int(lead_status.get("needs_information", 0))
        qualified = int(lead_status.get("qualified", 0))
        pending = int(task_status.get("pending_approval", 0))
        approved = int(task_status.get("approved", 0))
        rejected = int(task_status.get("rejected", 0))
        decisions = approved + rejected
        approval_rate = snapshot.get("approval_rate_percent")

        highlights_ar = [
            f"تم تسجيل {leads} عميل جديد خلال آخر سبعة أيام.",
            f"تم إنشاء {tasks} مهمة؛ منها {pending} معلقة و{approved} معتمدة و{rejected} مرفوضة.",
        ]
        highlights_en = [
            f"{leads} new leads were recorded in the last seven days.",
            f"{tasks} tasks were created: {pending} pending, {approved} approved, and {rejected} rejected.",
        ]
        actions_ar: list[str] = []
        actions_en: list[str] = []

        if approval_rate is None:
            highlights_ar.append("لا توجد قرارات اعتماد أو رفض كافية لحساب نسبة الاعتماد.")
            highlights_en.append("There are no approval or rejection decisions to calculate an approval rate.")
        else:
            highlights_ar.append(f"نسبة الاعتماد من القرارات المكتملة: {approval_rate:.1f}% ({approved} من {decisions}).")
            highlights_en.append(f"Approval rate among completed decisions: {approval_rate:.1f}% ({approved} of {decisions}).")

        if needs_info:
            highlights_ar.append(f"يوجد {needs_info} عميلًا في حالة تحتاج إلى معلومات إضافية.")
            highlights_en.append(f"{needs_info} leads currently need additional information.")
            actions_ar.append("راجع العملاء الذين يحتاجون إلى معلومات، وابدأ ببيانات التواصل وتواريخ السفر.")
            actions_en.append("Review leads needing information, starting with contact details and travel dates.")
        if pending:
            highlights_ar.append(f"هناك {pending} مهمة تنتظر مراجعة صاحب الوكالة.")
            highlights_en.append(f"{pending} tasks are waiting for agency-owner review.")
            actions_ar.append("راجع المهام المعلقة واتخذ قرار الاعتماد أو الرفض مع تسجيل الملاحظات.")
            actions_en.append("Review pending tasks and approve or reject them with decision notes.")
        if not tasks:
            actions_ar.append("ابدأ بتسجيل طلبات العملاء ثم أنشئ المهام المناسبة للأقسام.")
            actions_en.append("Start by recording customer requests, then create the relevant department tasks.")
        elif not pending:
            actions_ar.append("وزّع مهام متابعة جديدة وفق احتياجات العملاء المسجلة.")
            actions_en.append("Assign follow-up work based on the customer needs recorded in the system.")

        department_names = {
            "Sales": "المبيعات",
            "Finance": "المالية",
            "Marketing": "التسويق",
            "Customer Success": "خدمة العملاء",
            "Reporting": "التقارير",
        }
        active_departments = [
            (name, int(count)) for name, count in departments.items() if int(count) > 0
        ]
        active_departments.sort(key=lambda pair: (-pair[1], pair[0]))
        if active_departments:
            highlights_ar.append(
                "توزيع المهام حسب القسم: "
                + "، ".join(f"{department_names.get(name, name)} {count}" for name, count in active_departments)
                + "."
            )
            highlights_en.append(
                "Tasks by department: " + ", ".join(f"{name} {count}" for name, count in active_departments) + "."
            )
        else:
            highlights_ar.append("لم تُسجّل مهام للأقسام خلال الفترة.")
            highlights_en.append("No department tasks were recorded during this period.")

        if not actions_ar:
            actions_ar.append("استمر في متابعة العملاء والمهام حسب الأولوية المسجلة.")
            actions_en.append("Continue following up on leads and tasks based on recorded priority.")

        average_duration = snapshot.get("average_task_duration_ms")
        duration_ar = (
            f"متوسط زمن تنفيذ الوكيل المسجل {average_duration:.0f} مللي ثانية."
            if average_duration is not None else "لا توجد بيانات كافية عن زمن تنفيذ المهام."
        )
        duration_en = (
            f"Recorded average agent processing time: {average_duration:.0f} ms."
            if average_duration is not None else "There is not enough task-duration data."
        )

        period_start = str(snapshot.get("period_start", ""))[:10]
        period_end = str(snapshot.get("period_end", ""))[:10]
        result = {
            "report_type": "weekly_operations",
            "report_status": "draft_for_owner_review",
            "period_start": snapshot.get("period_start"),
            "period_end": snapshot.get("period_end"),
            "executive_summary_ar": (
                f"خلال الفترة من {period_start} إلى {period_end}، سجلت الوكالة "
                f"{leads} عميل و{tasks} مهمة. توجد {pending} مهمة بانتظار المراجعة."
            ),
            "executive_summary_en": (
                f"From {period_start} to {period_end}, the agency recorded "
                f"{leads} leads and {tasks} tasks. {pending} tasks are awaiting review."
            ),
            "highlights_ar": highlights_ar,
            "highlights_en": highlights_en,
            "recommended_actions_ar": actions_ar,
            "recommended_actions_en": actions_en,
            "lead_pipeline": {"new": new_leads, "needs_information": needs_info, "qualified": qualified},
            "task_status": {"pending_approval": pending, "approved": approved, "rejected": rejected},
            "approval_rate_percent": approval_rate,
            "average_task_duration_ms": average_duration,
            "duration_note_ar": duration_ar,
            "duration_note_en": duration_en,
            "department_task_counts": departments,
            "limitations_ar": [
                "التقرير مبني على السجلات الموجودة في النظام فقط، ولا يمثل إيرادات أو أرباحًا أو حجوزات مؤكدة.",
                "متوسط الزمن يقيس تنفيذ الوكيل داخل النظام، وليس زمن معالجة الموظف أو مدة إغلاق الطلب.",
                "هذه مسودة داخلية تتطلب مراجعة واعتماد صاحب الوكالة.",
            ],
            "limitations_en": [
                "This report uses records stored in ATLAS AI only; it does not represent revenue, profit, or confirmed bookings.",
                "Average duration measures agent processing inside the system, not employee handling time or end-to-end resolution time.",
                "This is an internal draft requiring agency-owner review and approval.",
            ],
            "owner_instructions": instructions,
            "source": "agency_records_last_7_days",
        }
        return {
            "result": result,
            "confidence": 0.0,
            "confidence_calibrated": False,
            "assumptions": [
                "الأرقام من تقرير المؤشرات الأسبوعي المسجل للوكالة الحالية فقط.",
                "التحليل قائم على قواعد واضحة وليس نموذج ذكاء اصطناعي لغوي متصل.",
            ],
            "risks": [
                "قد لا تعكس السجلات غير المكتملة جميع عمليات الوكالة خارج النظام.",
                "لا توجد بيانات مالية عن الإيرادات أو الأرباح أو التحصيلات ضمن هذا التقرير.",
            ],
            "next_action": "راجع الملخص والتوصيات ثم اعتمد التقرير أو ارفضه مع توضيح السبب.",
            "requires_owner_approval": True,
        }
