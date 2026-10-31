"""Sales lead qualification agent."""

from typing import Any

from backend.models import Lead
from backend.services.mock_llm import mock_llm


class LeadQualifierAgent:
    agent_id = "lead_qualifier"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        required = {
            "destination": lead.destination,
            "travel_start": lead.travel_start,
            "travel_end": lead.travel_end,
        }
        missing_fields = [name for name, value in required.items() if not value]
        if lead.travelers < 1:
            missing_fields.append("travelers")

        budget_note = (
            "لم يتم إدخال ميزانية بعد."
            if lead.budget_amount is None
            else f"الميزانية المسجلة: {lead.budget_amount:g} {lead.currency_code}."
        )
        complete_count = len(required) - len([name for name in required if not required[name]])
        qualification = "qualified" if not missing_fields else "needs_information"
        confidence = round(0.60 + (0.10 * complete_count), 2)

        summary = mock_llm.summarize(
            "lead_qualification",
            {"destination": lead.destination, "travelers": lead.travelers},
        )
        if instructions:
            summary = f"{summary} تعليمات المراجع: {instructions}"

        return {
            "result": {
                "qualification_status": qualification,
                "summary": summary,
                "missing_fields": missing_fields,
                "budget_note": budget_note,
                "lead_id": lead.id,
            },
            "confidence": min(confidence, 0.90),
            "assumptions": [
                "تم الاعتماد على البيانات المدخلة فقط دون التحقق من العميل أو الموردين.",
                "حالة التأهيل لا تعني تأكيد سعر أو توافر أو حجز.",
            ],
            "risks": [
                "لا يوجد اتصال بموردي الفنادق أو الطيران للتحقق من الأسعار والتوافر.",
            ],
            "next_action": (
                "مراجعة بيانات العميل واعتماد نتيجة التأهيل."
                if not missing_fields
                else "طلب البيانات الناقصة من العميل قبل إعداد عرض تفصيلي."
            ),
            "requires_owner_approval": True,
        }
