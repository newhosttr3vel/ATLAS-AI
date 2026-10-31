"""Deterministic department agents for the ATLAS AI prototype.

Agents create reviewable drafts and checklists. They do not call customers,
issue invoices, confirm bookings, or invent supplier prices.
"""
from datetime import date
from typing import Any

from backend.models import Lead


def _response(result: dict[str, Any], *, assumptions: list[str], risks: list[str], next_action: str) -> dict[str, Any]:
    return {
        "result": result,
        "confidence": 0.0,
        "confidence_calibrated": False,
        "assumptions": assumptions,
        "risks": risks,
        "next_action": next_action,
        "requires_owner_approval": True,
    }


def _trip_dates(lead: Lead) -> str:
    if lead.travel_start and lead.travel_end:
        return f"من {lead.travel_start.isoformat()} إلى {lead.travel_end.isoformat()}"
    return "مواعيد السفر قيد التأكيد"


class CostingAgent:
    agent_id = "costing_agent"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        items = [
            {"item": name, "supplier": None, "net_cost": None, "currency": None, "source": "لم يرد عرض مورد"}
            for name in ("الإقامة", "الطيران", "النقل", "خدمات أخرى")
        ]
        return _response(
            {
                "costing_status": "waiting_for_supplier_quotes",
                "customer": lead.customer_name,
                "destination": lead.destination,
                "travelers": lead.travelers,
                "travel_dates": _trip_dates(lead),
                "customer_budget": (
                    {"amount": lead.budget_amount, "currency": lead.currency_code,
                     "meaning": "حد ميزانية العميل المسجل فقط، وليس تكلفة أو سعر بيع"}
                    if lead.budget_amount is not None else None
                ),
                "line_items": items,
                "subtotal": None,
                "taxes_and_fees": None,
                "total_cost": None,
                "selling_price": None,
                "owner_supplied_notes": instructions,
                "required_inputs": [
                    "عرض سعر مكتوب من كل مورد مع اسم المورد وتاريخ صلاحية السعر.",
                    "عملة كل عرض، وما إذا كانت الضرائب والرسوم مشمولة.",
                    "تفاصيل الغرف أو الرحلات أو خدمات النقل والكميات.",
                    "سياسة الإلغاء وشروط الدفع لكل مورد.",
                ],
            },
            assumptions=[
                "لم يتم إدخال عروض موردين قابلة للتحقق؛ لذلك لم يتم إجراء أي حساب مالي.",
                "ميزانية العميل ليست تكلفة المورد ولا مبلغًا مستحقًا على العميل.",
            ],
            risks=[
                "لا توجد أسعار موردين أو رسوم مؤكدة في النظام.",
                "لا يجوز مشاركة سعر نهائي قبل مراجعة عروض الموردين والضرائب وهامش الربح.",
            ],
            next_action="أدخل عروض الموردين الفعلية وبنود التكلفة ثم اطلب مراجعة مالية جديدة.",
        )


class InvoiceAgent:
    agent_id = "invoice_agent"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        return _response(
            {
                "document_status": "draft_shell_only",
                "document_type": "مسودة بيانات فاتورة غير صالحة للتحصيل",
                "invoice_number": None,
                "issue_date": date.today().isoformat(),
                "customer": {"name": lead.customer_name, "email": lead.email, "phone": lead.phone},
                "service": {
                    "destination": lead.destination,
                    "travel_dates": _trip_dates(lead),
                    "travelers": lead.travelers,
                },
                "line_items": [],
                "subtotal": None,
                "taxes": None,
                "total_due": None,
                "currency": None,
                "customer_budget_reference": (
                    f"{lead.budget_amount:,.2f} {lead.currency_code} — ميزانية العميل المسجلة وليست مبلغ الفاتورة"
                    if lead.budget_amount is not None else None
                ),
                "owner_supplied_notes": instructions,
                "missing_before_issuance": [
                    "الخدمات الفعلية والكميات المتفق عليها.",
                    "أسعار البيع المعتمدة وعملة الفاتورة.",
                    "الضرائب والرسوم بعد مراجعتها محاسبيًا.",
                    "بيانات الكيان القانوني ورقمه الضريبي وعنوانه.",
                    "شروط الدفع وتاريخ الاستحقاق.",
                ],
            },
            assumptions=[
                "هذه مسودة هيكلية داخلية فقط وليست فاتورة ضريبية أو طلب دفع.",
                "لم يتم اعتبار ميزانية العميل مبلغًا مستحقًا.",
            ],
            risks=[
                "لا يوجد رقم فاتورة رسمي أو تسعير أو بيانات ضريبية معتمدة.",
                "يجب مراجعة المستند واعتماده من المسؤول المالي قبل إصداره أو مشاركته.",
            ],
            next_action="استكمال بيانات الخدمات والأسعار والضرائب والكيان القانوني ثم مراجعة المسؤول المالي.",
        )


class MarketingContentAgent:
    agent_id = "marketing_content_agent"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        destination = lead.destination or "[الوجهة]"
        dates = _trip_dates(lead)
        travelers = str(lead.travelers) if lead.travelers else "[عدد المسافرين]"
        arabic_copy = (
            f"✈️ رحلتك القادمة إلى {destination}\n"
            "نساعدك في ترتيب تفاصيل رحلتك بما يناسب احتياجاتك.\n"
            f"التواريخ: {dates}\nعدد المسافرين: {travelers}\n"
            "تواصل معنا لمناقشة متطلباتك والحصول على عرض مخصص بعد التحقق من الأسعار والتوافر."
        )
        english_copy = (
            f"✈️ Plan your next trip to {destination}.\n"
            "Our team can help organize a trip around your needs.\n"
            f"Dates: {dates}\nTravelers: {travelers}\n"
            "Contact us to discuss your requirements and request a tailored quote, subject to supplier confirmation."
        )
        return _response(
            {
                "content_status": "draft_for_review",
                "channel_suggestion": "منشور اجتماعي أو رسالة تسويقية بعد مراجعة الإدارة",
                "copy_ar": arabic_copy,
                "copy_en": english_copy,
                "call_to_action": "تواصل معنا لمعرفة الخيارات المناسبة",
                "owner_supplied_brief": instructions,
                "fact_check": [
                    "لم تتم إضافة اسم فندق أو شركة طيران أو سعر أو عرض غير موجود في سجل العميل.",
                    "لم تتم إضافة ادعاءات عن التوافر أو الخصومات أو محدودية المقاعد.",
                ],
            },
            assumptions=[
                "المحتوى مبني فقط على بيانات سجل العميل وتعليمات المالك.",
                "المسودة نموذج داخلي وليست حملة منشورة أو عرضًا تجاريًا مؤكدًا.",
            ],
            risks=[
                "يجب التحقق من أي سعر أو اسم مورد أو ميزة إضافية قبل النشر.",
                "لا يتم نشر المحتوى أو مراسلة العملاء تلقائيًا.",
            ],
            next_action="راجع النص والهوية البصرية والتفاصيل التجارية ثم اعتمده قبل النشر.",
        )


class CustomerSupportAgent:
    agent_id = "support_agent"

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        case_notes = (instructions or "").strip()
        reply_ar = (
            f"مرحبًا {lead.customer_name}، شكرًا لتواصلك معنا. استلمنا استفسارك، "
            "وسيُراجع فريقنا التفاصيل المتاحة ويتحقق منها قبل تزويدك برد واضح. نشكرك على تفهمك."
        )
        reply_en = (
            f"Hello {lead.customer_name}, thank you for contacting us. We have received your inquiry. "
            "Our team will review the available details and verify them before providing a clear update. "
            "Thank you for your understanding."
        )
        return _response(
            {
                "draft_status": "internal_reply_draft",
                "customer": lead.customer_name,
                "case_context_supplied_by_owner": case_notes or "لم يتم إدخال وصف للحالة أو استفسار العميل.",
                "reply_ar": reply_ar,
                "reply_en": reply_en,
                "send_status": "not_sent",
                "human_review_required": True,
            },
            assumptions=[
                "تم التعامل مع الملاحظات كملخص مقدم من الموظف، وليس كحقائق تم التحقق منها.",
                "هذه مسودة داخلية فقط ولم يتم إرسال أي رسالة للعميل.",
            ],
            risks=["يجب مراجعة سجل الحجز والموردين قبل تقديم أي التزام أو وعد للعميل."],
            next_action="راجع ملخص الحالة وأضف تفاصيل الحجز المؤكدة ثم اعتمد الرد المناسب يدويًا.",
        )


class ComplaintHandlerAgent:
    agent_id = "complaint_handler"
    KEYWORDS = {
        "booking": ("حجز", "booking", "reservation"),
        "payment": ("دفع", "خصم", "مبلغ", "استرداد", "payment", "refund", "charge"),
        "hotel": ("فندق", "غرفة", "نظافة", "hotel", "room"),
        "flight": ("طيران", "رحلة جوية", "مطار", "flight", "airline", "airport"),
        "cancellation": ("إلغاء", "الغاء", "cancellation", "cancel"),
        "delay": ("تأخير", "متأخر", "delay", "late"),
    }
    URGENT_TERMS = (
        "طارئ", "عالق", "اليوم", "الآن", "حاليا", "مطار", "سلامة",
        "emergency", "stranded", "today", "now", "safety", "airport",
    )

    def run(self, lead: Lead, instructions: str | None = None) -> dict[str, Any]:
        case_text = (instructions or "").strip()
        normalized = case_text.casefold()
        matches = [
            category for category, words in self.KEYWORDS.items()
            if any(word.casefold() in normalized for word in words)
        ]
        urgent = any(term.casefold() in normalized for term in self.URGENT_TERMS)

        if not case_text:
            category = "needs_case_details"
            priority = "unassigned"
            reason = "لم يتم إدخال نص الشكوى؛ لا يمكن تصنيفها دون تفاصيل."
            steps = [
                "أدخل نص الشكوى كما ورد من العميل دون حذف التفاصيل المهمة.",
                "أضف رقم الحجز وتاريخ السفر إن كانا متاحين.",
                "تحقق من وجود حالة عاجلة أو تأثير على سلامة المسافر.",
            ]
        else:
            category = matches[0] if len(matches) == 1 else ("multiple" if matches else "other")
            priority = "urgent_review" if urgent else "normal_review"
            reason = (
                "ظهرت كلمات تشير إلى حالة قد تكون عاجلة؛ يلزم تدخل موظف فورًا للتحقق."
                if urgent else
                "التصنيف مبني على كلمات مفتاحية في وصف الموظف، وليس تحققًا من صحة الشكوى."
            )
            steps = [
                "تحقق من نص الشكوى وسجل الحجز والمراسلات المرتبطة بها.",
                "تواصل مع المورد المعني للتحقق من الوقائع دون تقديم وعود غير مؤكدة.",
                "وثّق الإجراء والمسؤول وموعد المتابعة داخل نظام الوكالة.",
            ]
            if urgent:
                steps.insert(0, "حوّل الحالة فورًا إلى موظف مسؤول؛ لا تعتمد على التصنيف الآلي وحده.")

        return _response(
            {
                "classification_status": "draft_for_human_review",
                "customer": lead.customer_name,
                "category": category,
                "matched_categories": matches,
                "priority": priority,
                "priority_reason": reason,
                "case_text_supplied_by_owner": case_text or None,
                "recommended_steps": steps,
                "customer_contacted": False,
                "complaint_validity": "not_verified",
            },
            assumptions=[
                "التصنيف الأولي يعتمد على الكلمات المفتاحية الموجودة في وصف الحالة فقط.",
                "لم يتم التحقق من الوقائع أو التواصل مع العميل أو المورد.",
            ],
            risks=["يجب على موظف مراجعة الحالات العاجلة فورًا؛ التصنيف الآلي ليس بديلًا عن التقييم البشري."],
            next_action="راجع التصنيف والأولوية وسجل الإجراء التالي والمسؤول عن المتابعة.",
        )
