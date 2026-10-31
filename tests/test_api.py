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
    lead = client.post("/api/leads", json={"customer_name": "Report Demo"}).json()
    client.post("/api/tasks", json={"task_type": "qualify_lead", "lead_id": lead["id"]})

    agents = client.get("/api/agents").json()
    assert {agent["agent_id"] for agent in agents} >= {
        "general_manager",
        "lead_qualifier",
        "offer_builder",
    }

    report = client.get("/api/reports/weekly").json()
    assert report["leads_created"] == 1
    assert report["tasks_created"] == 1
    assert report["task_status_counts"]["pending_approval"] == 1


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
