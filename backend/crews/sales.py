"""Sales crew with deterministic mock agents."""

from typing import Any

from backend.agents.lead_qualifier import LeadQualifierAgent
from backend.agents.offer_builder import OfferBuilderAgent
from backend.models import Lead


class SalesCrew:
    def __init__(self) -> None:
        self.lead_qualifier = LeadQualifierAgent()
        self.offer_builder = OfferBuilderAgent()

    def execute(
        self,
        task_type: str,
        lead: Lead,
        instructions: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        if task_type == "qualify_lead":
            return self.lead_qualifier.agent_id, self.lead_qualifier.run(lead, instructions)
        if task_type == "build_offer":
            return self.offer_builder.agent_id, self.offer_builder.run(lead, instructions)
        raise ValueError(f"Unsupported sales task type: {task_type}")
