from fastapi.testclient import TestClient

from backend.main import app


def test_health_endpoint_returns_ok(client: TestClient) -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "app": "ATLAS AI",
        "mode": "mock",
    }


def test_api_uses_atlas_ai_branding() -> None:
    assert app.title == "ATLAS AI API"


def test_root_endpoint_describes_api(client: TestClient) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["api_docs"] == "/docs"


def test_create_and_list_leads_are_persisted(client: TestClient) -> None:
    payload = {
        "customer_name": "Demo Customer",
        "destination": "Makkah",
        "travel_start": "2027-01-10",
        "travel_end": "2027-01-15",
        "travelers": 3,
        "budget_amount": 25000,
        "currency_code": "egp",
    }
    created = client.post("/api/leads", json=payload)
    assert created.status_code == 201
    lead = created.json()
    assert lead["customer_name"] == "Demo Customer"
    assert lead["currency_code"] == "EGP"
    assert lead["agency_id"] == "demo-agency"

    listed = client.get("/api/leads")
    assert listed.status_code == 200
    assert len(listed.json()) == 1
    assert listed.json()[0]["id"] == lead["id"]


def test_agency_data_is_scoped_by_header(client: TestClient) -> None:
    client.post("/api/leads", json={"customer_name": "Agency A"})
    assert client.get("/api/leads", headers={"X-Agency-ID": "agency-b"}).json() == []


def test_general_manager_routes_qualification_for_owner_review(client: TestClient) -> None:
    lead_response = client.post(
        "/api/leads",
        json={
            "customer_name": "Qualification Demo",
            "destination": "Riyadh",
            "travel_start": "2027-02-01",
            "travel_end": "2027-02-05",
            "travelers": 2,
            "phone": "01012345678",
        },
    )
    lead_id = lead_response.json()["id"]

    task_response = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": lead_id},
    )
    assert task_response.status_code == 201
    task = task_response.json()
    assert task["assigned_agent_id"] == "lead_qualifier"
    assert task["status"] == "pending_approval"
    assert task["requires_owner_approval"] is True
    assert task["result"]["result"]["qualification_status"] == "qualified"
    assert task["result"]["result"]["completeness_score"] == 75
    assert task["result"]["confidence"] == 0.0
    assert {
        "result",
        "confidence",
        "assumptions",
        "risks",
        "next_action",
        "requires_owner_approval",
    }.issubset(task["result"])



def test_qualification_explains_missing_contact_and_recommended_details(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={
            "customer_name": "Incomplete Lead",
            "destination": "Makkah",
            "travel_start": "2027-04-10",
            "travel_end": "2027-04-14",
            "travelers": 2,
        },
    ).json()

    task = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": lead["id"]},
    )
    assert task.status_code == 201
    result = task.json()["result"]["result"]

    assert result["qualification_status"] == "needs_information"
    assert result["completeness_score"] == 55
    assert result["critical_missing_fields"] == ["contact_method"]
    assert result["recommended_missing_fields"] == ["budget_amount", "preferences"]
    assert any("رقم الهاتف أو البريد الإلكتروني" in question for question in result["recommended_questions"])
    assert "لا يمكن متابعة العميل" in " ".join(task.json()["result"]["risks"])

def test_owner_can_approve_or_reject_pending_tasks(client: TestClient) -> None:
    lead = client.post("/api/leads", json={"customer_name": "Approval Demo"}).json()
    task = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": lead["id"]},
    ).json()

    approved = client.post(
        f"/api/tasks/{task['id']}/approve",
        json={"notes": "Reviewed in demo"},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"

    second_task = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": lead["id"]},
    ).json()
    rejected = client.post(
        f"/api/tasks/{second_task['id']}/reject",
        json={"reason": "Needs more information"},
    )
    assert rejected.status_code == 200
    assert rejected.json()["status"] == "rejected"



def test_department_agents_route_finance_and_keep_amounts_unconfirmed(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={
            "customer_name": "Finance Demo",
            "destination": "Makkah",
            "travelers": 2,
            "budget_amount": 18000,
            "currency_code": "EGP",
        },
    ).json()

    costing = client.post(
        "/api/tasks",
        json={"task_type": "prepare_cost_sheet", "lead_id": lead["id"]},
    )
    assert costing.status_code == 201
    cost_task = costing.json()
    assert cost_task["assigned_agent_id"] == "costing_agent"
    cost_result = cost_task["result"]["result"]
    assert cost_result["total_cost"] is None
    assert cost_result["selling_price"] is None
    assert cost_result["customer_budget"]["amount"] == 18000
    assert cost_task["status"] == "pending_approval"
    assert cost_task["requires_owner_approval"] is True

    invoice = client.post(
        "/api/tasks",
        json={"task_type": "draft_invoice", "lead_id": lead["id"]},
    )
    assert invoice.status_code == 201
    invoice_result = invoice.json()["result"]["result"]
    assert invoice.json()["assigned_agent_id"] == "invoice_agent"
    assert invoice_result["total_due"] is None
    assert invoice_result["document_status"] == "draft_shell_only"


def test_marketing_and_support_agents_only_create_reviewable_drafts(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={"customer_name": "Content Demo", "destination": "Makkah", "travelers": 3},
    ).json()

    marketing = client.post(
        "/api/tasks",
        json={"task_type": "draft_marketing_content", "lead_id": lead["id"]},
    )
    assert marketing.status_code == 201
    marketing_body = marketing.json()
    assert marketing_body["assigned_agent_id"] == "marketing_content_agent"
    assert "Makkah" in marketing_body["result"]["result"]["copy_en"]
    assert marketing_body["result"]["result"]["content_status"] == "draft_for_review"
    assert marketing_body["status"] == "pending_approval"

    support = client.post(
        "/api/tasks",
        json={"task_type": "draft_customer_reply", "lead_id": lead["id"]},
    )
    assert support.status_code == 201
    support_result = support.json()["result"]["result"]
    assert support.json()["assigned_agent_id"] == "support_agent"
    assert support_result["send_status"] == "not_sent"
    assert support.json()["requires_owner_approval"] is True


def test_complaint_handler_flags_urgent_cases_for_human_review(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={"customer_name": "Complaint Demo", "destination": "Jeddah"},
    ).json()
    task = client.post(
        "/api/tasks",
        json={
            "task_type": "classify_complaint",
            "lead_id": lead["id"],
            "instructions": "العميل عالق في المطار اليوم بسبب مشكلة في الحجز",
        },
    )
    assert task.status_code == 201
    body = task.json()
    result = body["result"]["result"]
    assert body["assigned_agent_id"] == "complaint_handler"
    assert result["priority"] == "urgent_review"
    assert result["category"] in {"multiple", "booking"}
    assert result["customer_contacted"] is False
    assert body["status"] == "pending_approval"


def test_agent_directory_lists_all_departments(client: TestClient) -> None:
    agents = client.get("/api/agents").json()
    agent_ids = {item["agent_id"] for item in agents}
    assert {
        "finance_manager",
        "costing_agent",
        "invoice_agent",
        "marketing_manager",
        "marketing_content_agent",
        "customer_success_manager",
        "support_agent",
        "complaint_handler",
        "reporting_manager",
        "report_writer",
    }.issubset(agent_ids)

def test_offer_builder_never_invents_prices_or_availability(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={
            "customer_name": "Offer Demo",
            "destination": "Jeddah",
            "travel_start": "2027-03-01",
            "travel_end": "2027-03-05",
            "travelers": 2,
            "currency_code": "SAR",
        },
    ).json()

    task = client.post(
        "/api/tasks",
        json={"task_type": "build_offer", "lead_id": lead["id"]},
    )
    assert task.status_code == 201
    body = task.json()
    result = body["result"]["result"]
    assert body["assigned_agent_id"] == "offer_builder"
    assert len(result["packages"]) == 3
    assert all(package["price"] is None for package in result["packages"])
    assert all(package["availability"] == "not_verified" for package in result["packages"])
    assert body["status"] == "pending_approval"


def test_edit_keeps_owner_approval_required(client: TestClient) -> None:
    lead = client.post("/api/leads", json={"customer_name": "Edit Demo"}).json()
    task = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": lead["id"]},
    ).json()
    edited_result = task["result"] | {
        "next_action": "تم تعديل الخطوة التالية بواسطة المالك."
    }

    edited = client.post(
        f"/api/tasks/{task['id']}/edit",
        json={"result": edited_result, "notes": "Owner edit"},
    )
    assert edited.status_code == 200
    assert edited.json()["status"] == "pending_approval"
    assert edited.json()["requires_owner_approval"] is True

    edited_result["requires_owner_approval"] = False
    invalid = client.post(
        f"/api/tasks/{task['id']}/edit",
        json={"result": edited_result},
    )
    assert invalid.status_code == 422


def test_agents_and_weekly_report_include_activity(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={
            "customer_name": "Report Demo",
            "destination": "Makkah",
            "travelers": 2,
            "phone": "01000000000",
        },
    ).json()
    task = client.post("/api/tasks", json={"task_type": "qualify_lead", "lead_id": lead["id"]}).json()
    client.post(f"/api/tasks/{task['id']}/approve", json={"notes": "reviewed"})
    client.post("/api/tasks", json={"task_type": "draft_marketing_content", "lead_id": lead["id"]})

    agents = client.get("/api/agents").json()
    assert {agent["agent_id"] for agent in agents} >= {
        "general_manager",
        "lead_qualifier",
        "offer_builder",
    }

    report = client.get("/api/reports/weekly").json()
    assert report["leads_created"] == 1
    assert report["tasks_created"] == 2
    assert report["task_status_counts"]["pending_approval"] == 1
    assert report["task_status_counts"]["approved"] == 1
    assert report["approval_rate_percent"] == 100.0
    assert report["lead_status_counts"]["needs_information"] == 1
    assert report["task_type_counts"]["qualify_lead"] == 1
    assert report["task_type_counts"]["draft_marketing_content"] == 1
    assert report["department_task_counts"]["Sales"] == 1
    assert report["department_task_counts"]["Marketing"] == 1
    assert report["average_task_duration_ms"] is not None


def test_weekly_report_is_scoped_to_the_selected_agency(client: TestClient) -> None:
    lead = client.post("/api/leads", json={"customer_name": "Agency A"}).json()
    client.post("/api/tasks", json={"task_type": "qualify_lead", "lead_id": lead["id"]})
    response = client.get("/api/reports/weekly", headers={"X-Agency-ID": "agency-b"})
    assert response.status_code == 200
    report = response.json()
    assert report["leads_created"] == 0
    assert report["tasks_created"] == 0
    assert all(value == 0 for value in report["department_task_counts"].values())



def test_workspace_registry_and_audit_events_are_agency_scoped(client: TestClient) -> None:
    workspace = client.get("/api/workspace")
    assert workspace.status_code == 200
    assert workspace.json()["agency_id"] == "demo-agency"
    assert workspace.json()["plan"] == "prototype"
    assert workspace.json()["authentication_enabled"] is False
    assert workspace.json()["tenant_security"] == "prototype_header_only"

    lead = client.post("/api/leads", json={"customer_name": "Audit Demo"})
    assert lead.status_code == 201
    audit = client.get("/api/audit")
    assert audit.status_code == 200
    assert any(
        event["action"] == "lead.created" and event["entity_id"] == lead.json()["id"]
        for event in audit.json()
    )
    other_audit = client.get("/api/audit", headers={"X-Agency-ID": "agency-b"})
    assert other_audit.status_code == 200
    assert other_audit.json() == []


def test_weekly_report_writer_creates_reviewable_narrative_task(client: TestClient) -> None:
    lead = client.post(
        "/api/leads",
        json={
            "customer_name": "Weekly Report Demo",
            "destination": "Makkah",
            "travelers": 2,
            "phone": "01012345678",
        },
    ).json()
    client.post("/api/tasks", json={"task_type": "qualify_lead", "lead_id": lead["id"]})

    generated = client.post(
        "/api/reports/weekly/generate",
        json={"instructions": "ركز على المهام التي تنتظر اعتماد المالك."},
    )
    assert generated.status_code == 201
    task = generated.json()
    assert task["task_type"] == "generate_weekly_report"
    assert task["lead_id"] is None
    assert task["assigned_agent_id"] == "report_writer"
    assert task["status"] == "pending_approval"
    assert task["requires_owner_approval"] is True

    result = task["result"]["result"]
    assert result["report_type"] == "weekly_operations"
    assert result["report_status"] == "draft_for_owner_review"
    assert "1 عميل" in result["executive_summary_ar"]
    assert result["task_status"]["pending_approval"] == 1
    assert result["limitations_ar"]
    assert "revenue" not in result
    assert task["result"]["confidence_calibrated"] is False

    filtered = client.get("/api/tasks?task_type=generate_weekly_report")
    assert filtered.status_code == 200
    assert len(filtered.json()) == 1
    assert filtered.json()[0]["id"] == task["id"]
    assert any(event["action"] == "report.generated" for event in client.get("/api/audit").json())

    approved = client.post(
        f"/api/tasks/{task['id']}/approve",
        json={"notes": "تمت مراجعة التقرير التجريبي."},
    )
    assert approved.status_code == 200
    assert approved.json()["status"] == "approved"


def test_weekly_report_writer_uses_only_selected_agency_records(client: TestClient) -> None:
    client.post("/api/leads", json={"customer_name": "Demo Tenant Lead"})
    generated = client.post(
        "/api/reports/weekly/generate",
        json={},
        headers={"X-Agency-ID": "agency-b"},
    )
    assert generated.status_code == 201
    result = generated.json()["result"]["result"]
    assert result["lead_pipeline"] == {"new": 0, "needs_information": 0, "qualified": 0}
    assert result["task_status"]["pending_approval"] == 0


def test_task_lookup_and_missing_lead(client: TestClient) -> None:
    missing = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": "missing-id"},
    )
    assert missing.status_code == 404

    lead = client.post("/api/leads", json={"customer_name": "Lookup Demo"}).json()
    task = client.post(
        "/api/tasks",
        json={"task_type": "qualify_lead", "lead_id": lead["id"]},
    ).json()
    fetched = client.get(f"/api/tasks/{task['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["id"] == task["id"]
