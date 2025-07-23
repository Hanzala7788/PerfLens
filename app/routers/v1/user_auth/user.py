from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from app.config.base import get_db
from app.models.user import User
from app.utils.password import get_current_user
# from app.schemas.user import User

router = APIRouter()


@router.get("/users")
def get_user(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
    email: str = Query(None, description="Filter users by partial email match"),
):
    query = db.query(User.email)

    # Apply filtering if email query parameter is provided
    if email:
        query = query.filter(
            User.email.ilike(f"%{email}%")
        )  # Case-insensitive partial match

    db_users = query.all()

    # Convert to a list of emails
    email_list = [user.email for user in db_users]

    return email_list
