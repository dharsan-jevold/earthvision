from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.database.session import get_db
from app.models.analysis import AnalysisRecord
from app.models.project import Project
from app.models.user import User
from app.schemas.project import (
    AnalysisRecordDetailOut,
    AnalysisRecordOut,
    ProjectCreate,
    ProjectOut,
    SaveAnalysisRequest,
)

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectOut, status_code=201)
def create_project(payload: ProjectCreate, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = Project(
        owner_id=user.id,
        name=payload.name,
        min_lon=payload.bbox.min_lon,
        min_lat=payload.bbox.min_lat,
        max_lon=payload.bbox.max_lon,
        max_lat=payload.bbox.max_lat,
    )
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("", response_model=list[ProjectOut])
def list_projects(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Project).filter(Project.owner_id == user.id).order_by(Project.created_at.desc()).all()


def _get_owned_project(project_id: int, db: Session, user: User) -> Project:
    project = db.query(Project).filter(Project.id == project_id, Project.owner_id == user.id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.delete("/{project_id}", status_code=204)
def delete_project(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    project = _get_owned_project(project_id, db, user)
    db.delete(project)
    db.commit()


@router.post("/analyses", response_model=AnalysisRecordOut, status_code=201)
def save_analysis(payload: SaveAnalysisRequest, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_project(payload.project_id, db, user)  # authorization check
    record = AnalysisRecord(
        project_id=payload.project_id,
        before_scene_id=payload.before_scene_id,
        after_scene_id=payload.after_scene_id,
        provider=payload.provider,
        overall_severity=payload.result.overall_severity,
        total_changed_fraction=payload.result.total_changed_fraction,
        result_json=payload.result.model_dump(mode="json"),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


@router.get("/{project_id}/analyses", response_model=list[AnalysisRecordOut])
def list_analyses(project_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    _get_owned_project(project_id, db, user)
    return (
        db.query(AnalysisRecord)
        .filter(AnalysisRecord.project_id == project_id)
        .order_by(AnalysisRecord.created_at.desc())
        .all()
    )


@router.get("/analyses/{analysis_id}", response_model=AnalysisRecordDetailOut)
def get_analysis(analysis_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    record = db.query(AnalysisRecord).filter(AnalysisRecord.id == analysis_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Analysis not found")
    _get_owned_project(record.project_id, db, user)
    return record
