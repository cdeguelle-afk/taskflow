from datetime import date, datetime
from typing import Optional

from sqlmodel import Field, Relationship, SQLModel


class ProjectBase(SQLModel):
    name: str = Field(index=True, nullable=False, max_length=80)
    color: str = Field(default="#7c3aed", max_length=20)


class Project(ProjectBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    tasks: list["Task"] = Relationship(back_populates="project")


class ProjectCreate(ProjectBase):
    pass


class ProjectRead(ProjectBase):
    id: int


class ProjectUpdate(SQLModel):
    name: Optional[str] = Field(default=None, max_length=80)
    color: Optional[str] = Field(default=None, max_length=20)


class TaskBase(SQLModel):
    title: str = Field(index=True, nullable=False, max_length=120)
    description: Optional[str] = Field(default=None)
    due_date: Optional[date] = Field(default=None, index=True)
    priority: int = Field(default=2, ge=1, le=4)
    completed: bool = Field(default=False, index=True)
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")


class Task(TaskBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow, nullable=False)
    project: Optional[Project] = Relationship(back_populates="tasks")


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: int
    created_at: datetime


class TaskUpdate(SQLModel):
    title: Optional[str] = Field(default=None, max_length=120)
    description: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[int] = Field(default=None, ge=1, le=4)
    completed: Optional[bool] = None
    project_id: Optional[int] = Field(default=None, foreign_key="project.id")
