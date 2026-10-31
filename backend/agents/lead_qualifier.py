"""Rule-based lead qualification agent for the ATLAS AI mock prototype."""

from datetime import date
from typing import Any

from backend.models import Lead


class LeadQualifierAgent:
    """Evaluates lead completeness without claiming live supplier or customer checks."""

    agent_id = "lead_qualifier"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        critical_missing: list[str] = []
        recommended_missing: list[str] = []
        risks: list[str] = []
        questions: list[str] = []

        if not lead.destination:
            critical_missing.append("destination")
            questions.append("ما الوجهة أو المدينة التي يرغب العميل في السفر إليها؟")

        if not lead.travel_start:
            critical_missing.append("travel_start")
        if not lead.travel_end:
            critical_missing.append("travel_end")
        if not lead.travel_start or not lead.travel_end:
            questions.append("ما تاريخ السفر وتاريخ العودة المطلوبان؟")
            duration_nights = None
        else:
            duration_nights = (lead.travel_end - lead.travel_start).days
            if duration_nights < 0:
                critical_missing.extend(["travel_start", "travel_end"])
                risks.append("تاريخ العودة أسبق من تاريخ السفر؛ يجب تصحيح التاريخين.")
                questions.append("يرجى تأكيد تاريخ السفر والعودة؛ تاريخ العودة المسجل أسبق من السفر.")
            elif duration_nights == 0:
                risks.append("مدة الرحلة المسجلة يوم واحد دون مبيت؛ يرجى التأكد من أن هذا مقصود.")

        if not lead.travelers or lead.travelers < 1:
            critical_missing.append("travelers")
            questions.append("كم عدد المسافرين، بما في ذلك الأطفال؟")

        contact_methods = [
            method for method, value in (("phone", lead.phone), ("email", lead.email)) if value
        ]
        if not contact_methods:
            critical_missing.append("contact_method")
            questions.append("ما رقم الهاتف أو البريد الإلكتروني المناسب للتواصل مع العميل؟")

        if lead.budget_amount is None:
            recommended_missing.append("budget_amount")
            questions.append("ما الميزانية الإجمالية المتوقعة، وبأي عملة؟")
        if not lead.notes:
            recommended_missing.append("preferences")
            questions.append("هل توجد تفضيلات أو متطلبات مهمة، مثل مستوى الفندق أو نوع الغرفة أو التنقل؟")

        # Weighted completeness indicator (not an AI confidence probability).
        score = 0
        score += 15 if lead.destination else 0
        score += 25 if lead.travel_start and lead.travel_end and duration_nights is not None and duration_nights >= 0 else 0
        score += 15 if lead.travelers and lead.travelers >= 1 else 0
        score += 20 if contact_methods else 0
        score += 15 if lead.budget_amount is not None else 0
        score += 10 if lead.notes else 0

        qualification = "qualified" if not critical_missing else "needs_information"
        readiness_label = (
            "جاهز مبدئيًا للانتقال إلى إعداد مسودة عرض"
            if qualification == "qualified"
            else "يحتاج استكمال بيانات أساسية قبل إعداد العرض"
        )

        budget_per_traveler = (
            round(lead.budget_amount / lead.travelers, 2)
            if lead.budget_amount is not None and lead.travelers and lead.travelers > 0
            else None
        )
        budget_note = (
            "لم يتم تحديد ميزانية؛ يمكن استكمال التأهيل، لكن يلزم سؤال العميل عنها قبل اقتراح خيارات مناسبة."
            if lead.budget_amount is None
            else (
                f"الميزانية المسجلة: {lead.budget_amount:,.2f} {lead.currency_code} "
                f"(حوالي {budget_per_traveler:,.2f} {lead.currency_code} للفرد)."
            )
        )

        if lead.travel_start and lead.travel_start < date.today():
            risks.append("تاريخ السفر المسجل في الماضي؛ تحقق من التاريخ قبل متابعة الطلب.")

        if not contact_methods:
            risks.append("لا توجد وسيلة اتصال مسجلة؛ لا يمكن متابعة العميل من بيانات النظام الحالية.")
        if recommended_missing:
            risks.append("الميزانية أو تفضيلات الرحلة غير مكتملة؛ قد يؤثر ذلك على ملاءمة الخيارات المقترحة.")

        summary = (
            f"تقييم طلب {lead.customer_name}: {readiness_label}. "
            f"مؤشر اكتمال البيانات {score}%؛ "
            f"{len(critical_missing)} معلومة أساسية و{len(recommended_missing)} معلومة تحسين تحتاج إلى متابعة."
        )

        return {
            "result": {
                "qualification_status": qualification,
                "readiness_label": readiness_label,
                "summary": summary,
                "completeness_score": score,
                "missing_fields": critical_missing,
                "critical_missing_fields": critical_missing,
                "recommended_missing_fields": recommended_missing,
                "recommended_questions": questions,
                "budget_note": budget_note,
                "lead_snapshot": {
                    "customer_name": lead.customer_name,
                    "destination": lead.destination,
                    "travel_start": lead.travel_start.isoformat() if lead.travel_start else None,
                    "travel_end": lead.travel_end.isoformat() if lead.travel_end else None,
                    "duration_nights": duration_nights,
                    "travelers": lead.travelers,
                    "contact_method": " + ".join(contact_methods) if contact_methods else None,
                    "budget": (
                        f"{lead.budget_amount:,.2f} {lead.currency_code}"
                        if lead.budget_amount is not None else None
                    ),
                    "budget_per_traveler": (
                        f"{budget_per_traveler:,.2f} {lead.currency_code}"
                        if budget_per_traveler is not None else None
                    ),
                    "preferences": lead.notes,
                },
                "reviewer_instructions": instructions,
                "lead_id": lead.id,
            },
            # The deterministic mock has no statistically calibrated confidence.
            "confidence": 0.0,
            "assumptions": [
                "تم الاعتماد على بيانات سجل العميل فقط؛ لم يتم التواصل مع العميل.",
                "مؤشر اكتمال البيانات وزنٌ لقائمة حقول محددة، وليس احتمال نجاح الطلب أو دقة نموذج ذكاء اصطناعي.",
                "حالة التأهيل لا تعني تأكيد سعر أو توافر أو حجز.",
            ],
            "risks": risks + [
                "لا يوجد اتصال بموردي الفنادق أو الطيران للتحقق من الأسعار والتوافر."
            ],
            "next_action": (
                "استكمال بيانات التواصل والمعلومات الأساسية الناقصة، ثم إعادة تشغيل التأهيل."
                if critical_missing
                else (
                    "استكمال الميزانية والتفضيلات إن أمكن، ثم إنشاء مسودة عرض ومراجعتها قبل مشاركتها."
                    if recommended_missing
                    else "إنشاء مسودة عرض أولية، ثم التحقق يدويًا من الأسعار والتوافر مع الموردين."
                )
            ),
            "requires_owner_approval": True,
        }
