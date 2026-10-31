"""Deterministic mock language service used when no provider key is configured."""

from typing import Any


class MockLLM:
    """A predictable local adapter; it never calls an external model provider."""

    mode = "mock"

    def summarize(self, task_name: str, facts: dict[str, Any]) -> str:
        if task_name == "lead_qualification":
            destination = facts.get("destination") or "وجهة غير محددة"
            return f"تم تحليل طلب السفر إلى {destination} اعتمادًا على البيانات المسجلة فقط."
        if task_name == "offer_draft":
            destination = facts.get("destination") or "وجهة غير محددة"
            return f"تم إعداد هيكل مبدئي لثلاثة مستويات عرض إلى {destination} دون تسعير أو تأكيد توافر."
        return "تم استلام المهمة وتحليل البيانات المتاحة في وضع المحاكاة."


mock_llm = MockLLM()
