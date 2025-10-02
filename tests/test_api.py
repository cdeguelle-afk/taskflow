from datetime import date

from fastapi.testclient import TestClient
from sqlmodel import SQLModel, create_engine, Session

from app.database import get_session
from app.main import app


def get_test_engine():
    return create_engine("sqlite://", connect_args={"check_same_thread": False})


def create_db(engine):
    SQLModel.metadata.drop_all(engine)
    SQLModel.metadata.create_all(engine)


def override_get_session(engine):
    def _get_session():
        with Session(engine) as session:
            yield session
    return _get_session


def create_client():
    engine = get_test_engine()
    create_db(engine)
    app.dependency_overrides[get_session] = override_get_session(engine)
    client = TestClient(app)
    return client, engine


def test_project_lifecycle():
    client, engine = create_client()
    try:
        response = client.get("/api/projects")
        assert response.status_code == 200
        projects = response.json()
        assert any(project["name"] == "Inbox" for project in projects)

        payload = {"name": "Travail", "color": "#16a34a"}
        response = client.post("/api/projects", json=payload)
        assert response.status_code == 201
        project = response.json()
        assert project["name"] == "Travail"

        update = {"name": "Travail Pro"}
        response = client.put(f"/api/projects/{project['id']}", json=update)
        assert response.status_code == 200
        assert response.json()["name"] == "Travail Pro"

        response = client.delete(f"/api/projects/{project['id']}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
        engine.dispose()


def test_task_workflow():
    client, engine = create_client()
    try:
        project_payload = {"name": "Personnel", "color": "#f97316"}
        project = client.post("/api/projects", json=project_payload).json()

        task_payload = {
            "title": "Acheter des fleurs",
            "description": "Penser au bouquet d'anniversaire",
            "priority": 3,
            "project_id": project["id"],
            "due_date": date.today().isoformat(),
        }
        response = client.post("/api/tasks", json=task_payload)
        assert response.status_code == 201
        task = response.json()
        assert task["title"] == "Acheter des fleurs"
        assert task["completed"] is False

        response = client.patch(f"/api/tasks/{task['id']}/toggle")
        assert response.status_code == 200
        toggled = response.json()
        assert toggled["completed"] is True

        update_payload = {"priority": 4, "description": "Bouquet avec des pivoines"}
        response = client.put(f"/api/tasks/{task['id']}", json=update_payload)
        assert response.status_code == 200
        updated = response.json()
        assert updated["priority"] == 4
        assert "pivoines" in updated["description"]

        summary = client.get("/api/tasks/summary").json()
        assert summary["total"] >= 1
        assert summary["completed"] >= 1

        response = client.delete(f"/api/tasks/{task['id']}")
        assert response.status_code == 204
    finally:
        app.dependency_overrides.clear()
        engine.dispose()
