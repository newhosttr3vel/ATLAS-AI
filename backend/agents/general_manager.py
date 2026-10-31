"""General Manager routes business requests to the appropriate crew."""

from typing import Any

from backend.crews.sales import SalesCrew
from backend.models import Lead


class GeneralManagerAgent:
    agent_id = "general_manager"

    def __init__(self) -> None:
        self.sales_crew = SalesCrew()

    def dispatch(
        self,
        task_type: str,
        lead: Lead,
        instructions: str | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Route a supported request and return a standardized agent response."""
        assigned_agent, response = self.sales_crew.execute(task_type, lead, instructions)
        return assigned_agent, response
