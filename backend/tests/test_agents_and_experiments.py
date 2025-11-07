import pytest


@pytest.mark.asyncio
async def test_agent_crud_and_experiment_execution(client):
    user_payload = {
        "username": "runner",
        "email": "runner@example.com",
        "password": "RunnerPass123!",
        "preferences": {},
    }
    await client.post("/api/auth/register", json=user_payload)
    login_response = await client.post(
        "/api/auth/login",
        json={"email": user_payload["email"], "password": user_payload["password"]},
    )
    tokens = login_response.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    agent_payload = {
        "name": "Test Agent",
        "framework": "langchain",
        "description": "Testing agent",
        "parameters": {"temperature": 0.5},
    }
    response = await client.post("/api/agents/", json=agent_payload, headers=headers)
    assert response.status_code == 201
    agent = response.json()
    agent_id = agent["id"]

    response = await client.get("/api/agents/", headers=headers)
    agents = response.json()
    assert any(a["id"] == agent_id for a in agents)

    experiment_payload = {
        "name": "Experiment 1",
        "agent_id": agent_id,
        "input_payload": {"prompt": "Hello world"},
    }
    response = await client.post("/api/experiments/", json=experiment_payload, headers=headers)
    assert response.status_code == 201
    experiment = response.json()
    assert experiment["status"] == "completed"
    assert experiment["result_payload"]["framework"] == "LangChain"

    response = await client.get(f"/api/experiments/{experiment['id']}/status", headers=headers)
    assert response.status_code == 200
    status_info = response.json()
    assert status_info["status"] == "completed"
