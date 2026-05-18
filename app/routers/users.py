from fastapi import APIRouter, Depends, HTTPException
from app.dependencies import get_current_user, get_storage, User
from app.storage import TaskStorage

router = APIRouter(prefix="/users", tags=["users"])


@router.get("/me", response_model=User)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return current_user


@router.get("/{user_id}", response_model=User)
def get_user(
    user_id: int,
    current_user: User = Depends(get_current_user),
    storage: TaskStorage = Depends(get_storage)
):
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Access denied")
    return User(id=user_id, role="user")