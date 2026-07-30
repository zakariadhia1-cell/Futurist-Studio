import pytest

from tests.conftest import register_and_login

pytestmark = pytest.mark.asyncio


async def test_project_crud(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    created = await client.post(
        "/api/v1/projects", json={"name": "Website Relaunch", "description": "Neue Site"}, headers=headers
    )
    assert created.status_code == 201
    project_id = created.json()["id"]
    assert created.json()["status"] == "active"

    listed = await client.get("/api/v1/projects", headers=headers)
    assert any(p["id"] == project_id for p in listed.json())

    updated = await client.patch(
        f"/api/v1/projects/{project_id}", json={"status": "done"}, headers=headers
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "done"

    deleted = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert deleted.status_code == 204

    listed_after = await client.get("/api/v1/projects", headers=headers)
    assert all(p["id"] != project_id for p in listed_after.json())


async def test_task_crud_and_project_link(client):
    token = await register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    project = await client.post("/api/v1/projects", json={"name": "Marketing"}, headers=headers)
    project_id = project.json()["id"]

    created = await client.post(
        "/api/v1/tasks",
        json={"title": "Blogpost schreiben", "project_id": project_id, "priority": "high"},
        headers=headers,
    )
    assert created.status_code == 201
    task_id = created.json()["id"]
    assert created.json()["status"] == "todo"

    updated = await client.patch(f"/api/v1/tasks/{task_id}", json={"status": "done"}, headers=headers)
    assert updated.json()["status"] == "done"

    listed = await client.get("/api/v1/tasks", headers=headers)
    assert any(t["id"] == task_id for t in listed.json())

    deleted = await client.delete(f"/api/v1/tasks/{task_id}", headers=headers)
    assert deleted.status_code == 204


async def test_projects_and_tasks_scoped_to_owner(client):
    token_a = await register_and_login(client, email="pa@futurist.os")
    token_b = await register_and_login(client, email="pb@futurist.os")

    created = await client.post(
        "/api/v1/projects", json={"name": "A privat"}, headers={"Authorization": f"Bearer {token_a}"}
    )
    project_id = created.json()["id"]

    forbidden = await client.patch(
        f"/api/v1/projects/{project_id}",
        json={"status": "done"},
        headers={"Authorization": f"Bearer {token_b}"},
    )
    assert forbidden.status_code == 404
