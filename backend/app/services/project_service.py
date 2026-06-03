import uuid
from typing import Tuple, Sequence, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, table, column, or_, and_
from fastapi import HTTPException

from app.models.project import Project
from app.models.project_member import ProjectMember
from app.models.client import Client
from app.schemas.project import ProjectCreate, ProjectUpdate


async def list_projects(
    db: AsyncSession,
    workspace_id: uuid.UUID,
    caller_id: uuid.UUID,
    caller_role: str,
    status_filter: str | None = "active",
    client_id: uuid.UUID | None = None,
    page: int = 1,
    per_page: int = 20,
) -> Tuple[Sequence[Dict[str, Any]], int]:
    """List projects based on visibility and status."""
    time_entries = table("time_entries", column("project_id"), column("duration_seconds"))
    
    hours_logged_subq = (
        select(func.sum(time_entries.c.duration_seconds) / 3600.0)
        .where(time_entries.c.project_id == Project.id)
        .correlate(Project)
        .scalar_subquery()
    )

    count_stmt = select(func.count(Project.id.distinct())).select_from(Project)
    
    stmt = (
        select(
            Project,
            Client.name.label("client_name"),
            func.coalesce(hours_logged_subq, 0.0).label("hours_logged"),
        )
        .outerjoin(Client, Client.id == Project.client_id)
    )

    where_clauses = [Project.workspace_id == workspace_id]

    if status_filter and status_filter != "all":
        where_clauses.append(Project.status == status_filter)
        
    if client_id:
        where_clauses.append(Project.client_id == client_id)

    if caller_role in ["member", "viewer"]:
        stmt = stmt.outerjoin(ProjectMember, (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == caller_id))
        count_stmt = count_stmt.outerjoin(ProjectMember, (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == caller_id))
        where_clauses.append(
            or_(Project.visibility == "public", ProjectMember.user_id.is_not(None))
        )

    stmt = stmt.where(and_(*where_clauses))
    count_stmt = count_stmt.where(and_(*where_clauses))

    total = (await db.execute(count_stmt)).scalar() or 0

    if total == 0:
        return [], 0

    stmt = stmt.order_by(Project.name.asc()).offset((page - 1) * per_page).limit(per_page)
    result = await db.execute(stmt)
    rows = result.all()

    projects = []
    for project, client_name, hours_logged in rows:
        p_dict = project.__dict__.copy()
        p_dict["client_name"] = client_name
        p_dict["hours_logged"] = float(hours_logged) if hours_logged else 0.0
        projects.append(p_dict)

    return projects, total

async def create_project(db: AsyncSession, workspace_id: uuid.UUID, data: ProjectCreate) -> Project:
    """Create a new project."""
    stmt = select(Project).where(Project.workspace_id == workspace_id, Project.name == data.name)
    if (await db.execute(stmt)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"detail": "Duplicate project name", "code": "DUPLICATE_NAME"})

    if data.client_id:
        client = await db.execute(select(Client).where(Client.id == data.client_id, Client.workspace_id == workspace_id))
        if not client.scalar_one_or_none():
            raise HTTPException(status_code=400, detail={"detail": "Client not found in workspace", "code": "BAD_REQUEST"})

    project = Project(
        workspace_id=workspace_id,
        **data.model_dump(exclude_unset=True)
    )
    db.add(project)
    await db.flush()
    return project

async def get_project(db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, caller_id: uuid.UUID, caller_role: str) -> Dict[str, Any]:
    """Get project details."""
    stmt = select(Project, Client.name.label("client_name")).outerjoin(Client, Client.id == Project.client_id).where(Project.id == project_id, Project.workspace_id == workspace_id)
    
    if caller_role in ["member", "viewer"]:
        stmt = stmt.outerjoin(ProjectMember, (ProjectMember.project_id == Project.id) & (ProjectMember.user_id == caller_id))
        stmt = stmt.where(or_(Project.visibility == "public", ProjectMember.user_id.is_not(None)))
        
    result = await db.execute(stmt)
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail={"detail": "Project not found or access denied", "code": "NOT_FOUND"})
        
    p_dict = row[0].__dict__.copy()
    p_dict["client_name"] = row[1]
    return p_dict

async def update_project(db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, data: ProjectUpdate) -> Project:
    """Update a project."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    project = (await db.execute(project_stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "NOT_FOUND"})

    if data.name is not None and data.name != project.name:
        check = select(Project).where(Project.workspace_id == workspace_id, Project.name == data.name)
        if (await db.execute(check)).scalar_one_or_none():
            raise HTTPException(status_code=409, detail={"detail": "Duplicate project name", "code": "DUPLICATE_NAME"})

    if data.client_id is not None:
        client = await db.execute(select(Client).where(Client.id == data.client_id, Client.workspace_id == workspace_id))
        if not client.scalar_one_or_none():
            raise HTTPException(status_code=400, detail={"detail": "Client not found in workspace", "code": "BAD_REQUEST"})

    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(project, k, v)
        
    await db.flush()
    return project

async def archive_project(db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Project:
    """Archive a project."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    project = (await db.execute(project_stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "NOT_FOUND"})

    project.status = "archived"
    project.archived_at = datetime.now(timezone.utc)
    await db.flush()
    return project

async def delete_project(db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID) -> None:
    """Delete a project."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    project = (await db.execute(project_stmt)).scalar_one_or_none()
    if not project:
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "NOT_FOUND"})

    te_table = table("time_entries", column("project_id"))
    check_te = select(func.count()).select_from(te_table).where(column("project_id") == project_id)
    count = (await db.execute(check_te)).scalar() or 0
    if count > 0:
        raise HTTPException(status_code=400, detail={"detail": "Archive instead — time entries exist.", "code": "BAD_REQUEST"})

    await db.delete(project)
    await db.flush()

async def list_project_members(db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID) -> Sequence[ProjectMember]:
    """List members of a private project."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    if not (await db.execute(project_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "NOT_FOUND"})
        
    stmt = select(ProjectMember).where(ProjectMember.project_id == project_id)
    result = await db.execute(stmt)
    return result.scalars().all()

async def add_project_member(
    db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID, added_by: uuid.UUID
) -> ProjectMember:
    """Add a member to a private project."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    if not (await db.execute(project_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "NOT_FOUND"})
        
    check = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    if (await db.execute(check)).scalar_one_or_none():
        raise HTTPException(status_code=409, detail={"detail": "Already member", "code": "ALREADY_MEMBER"})

    pm = ProjectMember(project_id=project_id, user_id=user_id, added_by_user_id=added_by)
    db.add(pm)
    await db.flush()
    return pm

async def remove_project_member(
    db: AsyncSession, workspace_id: uuid.UUID, project_id: uuid.UUID, user_id: uuid.UUID
) -> None:
    """Remove a member from a private project."""
    project_stmt = select(Project).where(Project.id == project_id, Project.workspace_id == workspace_id)
    if not (await db.execute(project_stmt)).scalar_one_or_none():
        raise HTTPException(status_code=404, detail={"detail": "Project not found", "code": "NOT_FOUND"})

    check = select(ProjectMember).where(ProjectMember.project_id == project_id, ProjectMember.user_id == user_id)
    pm = (await db.execute(check)).scalar_one_or_none()
    if pm:
        await db.delete(pm)
        await db.flush()
