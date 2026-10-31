"""Department routing for finance, marketing, and customer success teams."""
from typing import Any

from backend.agents.department_agents import (
    ComplaintHandlerAgent,
    CostingAgent,
    CustomerSupportAgent,
    InvoiceAgent,
    MarketingContentAgent,
)
from backend.models import Lead


class DepartmentsCrew:
    def __init__(self) -> None:
        self.agents = {
            "prepare_cost_sheet": CostingAgent(),
            "draft_invoice": InvoiceAgent(),
            "draft_marketing_content": MarketingContentAgent(),
            "draft_customer_reply": CustomerSupportAgent(),
            "classify_complaint": ComplaintHandlerAgent(),
        }

    def execute(self, task_type: str, lead: Lead, instructions: str | None = None) -> tuple[str, dict[str, Any]]:
        agent = self.agents.get(task_type)
        if agent is None:
            raise ValueError(f"Unsupported department task type: {task_type}")
        return agent.agent_id, agent.run(lead, instructions)
