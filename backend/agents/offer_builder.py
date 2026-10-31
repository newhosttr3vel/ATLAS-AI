"""Creates non-priced draft offer structures without inventing supplier data."""

from typing import Any

from backend.models import Lead
from backend.services.mock_llm import mock_llm


class OfferBuilderAgent:
    agent_id = "offer_builder"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        if not lead.destination or not lead.travel_start or not lead.travel_end:
            missing_fields = [
                field
                for field, value in {
                    "destination": lead.destination,
                    "travel_start": lead.travel_start,
                    "travel_end": lead.travel_end,
                }.items()
                if not value
            ]
            return {
                "result": {
                    "offer_status": "needs_information",
                    "destination": lead.destination,
                    "missing_fields": missing_fields,
                    "packages": [],
                },
                "confidence": 0.95,
                "assumptions": ["لم يتم إنشاء باقات قبل اكتمال بيانات الوجهة والتواريخ."],
                "risks": ["لا يمكن إعداد نطاق رحلة مناسب دون بيانات السفر الأساسية."],
                "next_action": "استكمال بيانات الوجهة وتواريخ السفر ثم إعادة إنشاء المسودة.",
                "requires_owner_approval": True,
            }

        package_levels = [
            {
                "tier": "budget",
                "name": "Economy",
                "focus": "التركيز على التكلفة والاحتياجات الأساسية",
            },
            {
                "tier": "comfort",
                "name": "Comfort",
                "focus": "توازن بين الراحة والتكلفة",
            },
            {
                "tier": "premium",
                "name": "Premium",
                "focus": "خيارات أعلى مستوى ومرونة أكبر",
            },
        ]
        packages = [
            {
                **package,
                "price": None,
                "currency_code": lead.currency_code,
                "availability": "not_verified",
                "status": "draft_only",
            }
            for package in package_levels
        ]
        summary = mock_llm.summarize("offer_draft", {"destination": lead.destination})
        if instructions:
            summary = f"{summary} تعليمات المراجع: {instructions}"

        return {
            "result": {
                "offer_status": "draft_only",
                "summary": summary,
                "destination": lead.destination,
                "travel_start": lead.travel_start.isoformat(),
                "travel_end": lead.travel_end.isoformat(),
                "travelers": lead.travelers,
                "packages": packages,
                "pricing_status": "not_provided",
                "availability_status": "not_verified",
            },
            "confidence": 0.75,
            "assumptions": [
                "مستويات الباقات تصنيف تخطيطي وليست عروض موردين حقيقية.",
                "لا توجد أسعار أو توافر مؤكدة ضمن وضع المحاكاة.",
            ],
            "risks": [
                "يجب الحصول على أسعار وتأكيدات مكتوبة من الموردين قبل مشاركة عرض نهائي.",
            ],
            "next_action": "مراجعة هيكل الباقات وإدخال عروض الموردين الفعلية قبل الاعتماد.",
            "requires_owner_approval": True,
        }
