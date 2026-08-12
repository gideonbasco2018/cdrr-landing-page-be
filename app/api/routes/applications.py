from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.schemas.applications import ApplicationCreate, ApplicationResponse
from app.crud import applications as crud_application
from app.core.security_external import verify_bearer_token

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post(
    "/",
    response_model=ApplicationResponse,
    dependencies=[Depends(verify_bearer_token)],
)
def create_application(payload: ApplicationCreate, db: Session = Depends(get_db)):
    return crud_application.create_application(db, payload)
