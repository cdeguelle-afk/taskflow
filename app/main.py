from collections import Counter
from datetime import date
from pathlib import Path
from typing import Optional

from fastapi import Depends, FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select

from .database import create_db_and_tables, get_session
from .models import (
    Project,
    ProjectCreate,
    ProjectRead,
    ProjectUpdate,
    Task,
    TaskCreate,
    TaskRead,
    TaskUpdate,
)

app = FastAPI(title="Taskflow", version="0.1.0")
static_dir = Path(__file__).parent / "static"
app.mount("/static", StaticFiles(directory=static_dir), name="static")


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()
    with get_session() as session:
        inbox_exists = session.exec(select(Project).where(Project.name == "Inbox")).first()
        if inbox_exists is None:
            session.add(Project(name="Inbox", color="#2563eb"))


@app.get("/", response_class=HTMLResponse)
def read_index() -> HTMLResponse:
    index_path = static_dir / "index.html"
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.get("/api/projects", response_model=list[ProjectRead])
def list_projects(session: Session = Depends(get_session)) -> list[ProjectRead]:
    projects = session.exec(select(Project).order_by(Project.name)).all()
    return projects


@app.post("/api/projects", response_model=ProjectRead, status_code=201)
def create_project(project: ProjectCreate, session: Session = Depends(get_session)) -> ProjectRead:
    existing = session.exec(select(Project).where(Project.name == project.name)).first()
    if existing:
        raise HTTPException(status_code=400, detail="A project with this name already exists")
    db_project = Project.model_validate(project)
    session.add(db_project)
    session.flush()
    session.refresh(db_project)
    return db_project


@app.put("/api/projects/{project_id}", response_model=ProjectRead)
def update_project(project_id: int, payload: ProjectUpdate, session: Session = Depends(get_session)) -> ProjectRead:
    db_project = session.get(Project, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_project, key, value)
    session.add(db_project)
    session.flush()
    session.refresh(db_project)
    return db_project


@app.delete("/api/projects/{project_id}", status_code=204)
def delete_project(project_id: int, session: Session = Depends(get_session)) -> None:
    db_project = session.get(Project, project_id)
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    if db_project.name == "Inbox":
        raise HTTPException(status_code=400, detail="The Inbox project cannot be deleted")
    for task in db_project.tasks:
        task.project_id = None
        session.add(task)
    session.delete(db_project)


@app.get("/api/tasks", response_model=list[TaskRead])
def list_tasks(
    project_id: Optional[int] = None,
    completed: Optional[bool] = None,
    search: Optional[str] = None,
    due_before: Optional[date] = None,
    due_after: Optional[date] = None,
    session: Session = Depends(get_session),
) -> list[TaskRead]:
    statement = select(Task)
    if project_id is not None:
        statement = statement.where(Task.project_id == project_id)
    if completed is not None:
        statement = statement.where(Task.completed.is_(completed))
    if search:
        like_pattern = f"%{search.lower()}%"
        statement = statement.where(Task.title.ilike(like_pattern) | Task.description.ilike(like_pattern))
    if due_before is not None:
        statement = statement.where(Task.due_date <= due_before)
    if due_after is not None:
        statement = statement.where(Task.due_date >= due_after)
    statement = statement.order_by(Task.completed, Task.priority.desc(), Task.due_date.is_(None), Task.due_date)
    return session.exec(statement).all()


@app.get("/api/tasks/{task_id}", response_model=TaskRead)
def read_task(task_id: int, session: Session = Depends(get_session)) -> TaskRead:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.post("/api/tasks", response_model=TaskRead, status_code=201)
def create_task(payload: TaskCreate, session: Session = Depends(get_session)) -> TaskRead:
    if payload.project_id is not None and session.get(Project, payload.project_id) is None:
        raise HTTPException(status_code=400, detail="Project does not exist")
    task = Task.model_validate(payload)
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


@app.put("/api/tasks/{task_id}", response_model=TaskRead)
def update_task(task_id: int, payload: TaskUpdate, session: Session = Depends(get_session)) -> TaskRead:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    update_data = payload.model_dump(exclude_unset=True)
    if "project_id" in update_data and update_data["project_id"] is not None:
        if session.get(Project, update_data["project_id"]) is None:
            raise HTTPException(status_code=400, detail="Project does not exist")
    for key, value in update_data.items():
        setattr(task, key, value)
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


@app.patch("/api/tasks/{task_id}/toggle", response_model=TaskRead)
def toggle_task_completion(task_id: int, session: Session = Depends(get_session)) -> TaskRead:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    task.completed = not task.completed
    session.add(task)
    session.flush()
    session.refresh(task)
    return task


@app.delete("/api/tasks/{task_id}", status_code=204)
def delete_task(task_id: int, session: Session = Depends(get_session)) -> None:
    task = session.get(Task, task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    session.delete(task)


@app.get("/api/tasks/summary")
def task_summary(session: Session = Depends(get_session)) -> dict[str, int]:
    tasks = session.exec(select(Task.completed)).all()
    counter = Counter(tasks)
    total = len(tasks)
    completed = counter.get(True, 0)
    return {
        "total": total,
        "completed": completed,
        "active": total - completed,
    }
