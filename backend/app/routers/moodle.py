from urllib.parse import quote

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from ..database import get_db
from ..models import User
from ..auth import get_current_user
from ..services.moodle_service import fetch_moodle_data
from ..services import moodle_resources as resources

router = APIRouter(prefix="/api/moodle", tags=["moodle"])

@router.get("/assignments")
def get_assignments(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_moodle_data(
        url=creds.moodle_url if creds else None,
        username=creds.moodle_username if creds else None,
        password=creds.moodle_password if creds else None,
        token=creds.moodle_token if creds else None,
        force_refresh=force_refresh
    )
    return {
        "configured": data.get("configured", False),
        "connection_error": data.get("connection_error"),
        "site_name": data.get("site_name", "Moodle"),
        "assignments": data.get("upcoming_assignments", [])
    }

@router.get("/courses")
def get_courses(
    force_refresh: bool = Query(False),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    creds = current_user.credentials
    data = fetch_moodle_data(
        url=creds.moodle_url if creds else None,
        username=creds.moodle_username if creds else None,
        password=creds.moodle_password if creds else None,
        token=creds.moodle_token if creds else None,
        force_refresh=force_refresh
    )
    return {
        "configured": data.get("configured", False),
        "connection_error": data.get("connection_error"),
        "site_name": data.get("site_name", "Moodle"),
        "courses": data.get("courses", [])
    }


@router.get("/resources/courses")
def get_resource_courses(force_refresh: bool = Query(False), current_user: User = Depends(get_current_user)):
    return resources.list_courses(current_user, force_refresh=force_refresh)


@router.get("/resources/courses/{course_id}")
def get_resource_course(course_id: int, force_refresh: bool = Query(False), current_user: User = Depends(get_current_user)):
    return resources.get_course(current_user, course_id, force_refresh=force_refresh)


@router.get("/resources/courses/{course_id}/modules/{cmid}/files/{index}")
def download_resource_file(
    course_id: int,
    cmid: int,
    index: int,
    inline: bool = Query(False),
    current_user: User = Depends(get_current_user),
):
    try:
        upstream, name, mime = resources.open_file(current_user, course_id, cmid, index)
    except resources.MoodleError as e:
        raise HTTPException(status_code=502, detail=str(e))

    disposition = "inline" if inline and mime in resources.INLINE_MIMES else "attachment"
    headers = {
        "Content-Disposition": f"{disposition}; filename*=UTF-8''{quote(name)}",
        "X-Content-Type-Options": "nosniff",
        "Cache-Control": "private, no-store",
    }
    if upstream.headers.get("Content-Length"):
        headers["Content-Length"] = upstream.headers["Content-Length"]

    def stream():
        try:
            yield from upstream.iter_content(65536)
        finally:
            upstream.close()

    media = mime if disposition == "inline" else "application/octet-stream"
    return StreamingResponse(stream(), media_type=media, headers=headers)
