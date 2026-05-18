from fastapi import APIRouter, Depends, HTTPException, status
from collections import Counter
from app.dependencies import require_admin, get_storage, User
from app.storage import TaskStorage
from app.schemas import StatsResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=StatsResponse)
def get_stats(
    admin_user: User = Depends(require_admin),
    storage: TaskStorage = Depends(get_storage)
):
    tasks = storage.get_all_tasks()
    total_tasks = len(tasks)
    by_status = Counter(task.status.value for task in tasks)

    return StatsResponse(
        total_tasks=total_tasks,
        by_status=dict(by_status)
    )


@router.delete("/tasks/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def admin_delete_task(
    task_id: int,
    admin_user: User = Depends(require_admin),
    storage: TaskStorage = Depends(get_storage)
):
    if not storage.delete_task(task_id):
        raise HTTPException(status_code=404, detail="Task not found")