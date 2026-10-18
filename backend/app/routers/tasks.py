from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User, PersonalTask, CompletedExternalTask
from ..schemas import PersonalTaskCreate, PersonalTaskUpdate, PersonalTaskResponse, ItemStatusToggle
from ..auth import get_current_user

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

@router.get("", response_model=List[PersonalTaskResponse])
def get_tasks(
    status_filter: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    query = db.query(PersonalTask).filter(PersonalTask.user_id == current_user.id)
    if status_filter:
        query = query.filter(PersonalTask.status == status_filter)
    tasks = query.order_by(PersonalTask.due_date.asc()).all()
    return tasks

@router.get("/completed-external", response_model=List[str])
def get_completed_external_tasks(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    rows = db.query(CompletedExternalTask).filter(CompletedExternalTask.user_id == current_user.id).all()
    return [r.item_id for r in rows]

@router.post("/toggle-status")
def toggle_item_status(
    payload: ItemStatusToggle,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    item_id = payload.item_id
    new_status = payload.status if payload.status in ["todo", "done"] else "todo"

    if item_id.startswith("personal-"):
        try:
            task_id = int(item_id.replace("personal-", ""))
            task = db.query(PersonalTask).filter(
                PersonalTask.id == task_id,
                PersonalTask.user_id == current_user.id
            ).first()
            if not task:
                raise HTTPException(status_code=404, detail="Tâche personnelle introuvable.")
            task.status = new_status
            db.commit()
            return {"item_id": item_id, "status": new_status, "is_personal": True}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))
    else:
        # External item (Moodle or Timetable ADE)
        existing = db.query(CompletedExternalTask).filter(
            CompletedExternalTask.user_id == current_user.id,
            CompletedExternalTask.item_id == item_id
        ).first()

        if new_status == "done":
            if not existing:
                db.add(CompletedExternalTask(user_id=current_user.id, item_id=item_id))
                db.commit()
        else:
            if existing:
                db.delete(existing)
                db.commit()
        return {"item_id": item_id, "status": new_status, "is_personal": False}

@router.post("", response_model=PersonalTaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    payload: PersonalTaskCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = PersonalTask(
        user_id=current_user.id,
        title=payload.title,
        description=payload.description,
        subject=payload.subject,
        due_date=payload.due_date,
        event_type=payload.event_type,
        status=payload.status
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task

@router.put("/{task_id}", response_model=PersonalTaskResponse)
def update_task(
    task_id: int,
    payload: PersonalTaskUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(PersonalTask).filter(
        PersonalTask.id == task_id,
        PersonalTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée.")

    if payload.title is not None:
        task.title = payload.title
    if payload.description is not None:
        task.description = payload.description
    if payload.subject is not None:
        task.subject = payload.subject
    if payload.due_date is not None:
        task.due_date = payload.due_date
    if payload.event_type is not None:
        task.event_type = payload.event_type
    if payload.status is not None:
        task.status = payload.status

    db.commit()
    db.refresh(task)
    return task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    task = db.query(PersonalTask).filter(
        PersonalTask.id == task_id,
        PersonalTask.user_id == current_user.id
    ).first()
    if not task:
        raise HTTPException(status_code=404, detail="Tâche non trouvée.")

    db.delete(task)
    db.commit()
    return None


