from typing import Dict, List, Optional
from app.schemas import Task, TaskStatus


class TaskStorage:
    def __init__(self):
        self._tasks: Dict[int, Task] = {}
        self._next_id: int = 1

    def create_task(self, task_data: dict, owner_id: int) -> Task:
        task_id = self._next_id
        self._next_id += 1
        task = Task(id=task_id, owner_id=owner_id, **task_data)
        self._tasks[task_id] = task
        return task

    def get_task(self, task_id: int) -> Optional[Task]:
        return self._tasks.get(task_id)

    def get_user_tasks(
        self,
        owner_id: int,
        status: Optional[str] = None,
        min_priority: Optional[int] = None
    ) -> List[Task]:
        tasks = [t for t in self._tasks.values() if t.owner_id == owner_id]

        if status:
            tasks = [t for t in tasks if t.status == status]

        if min_priority is not None:
            tasks = [t for t in tasks if t.priority >= min_priority]

        return sorted(tasks, key=lambda x: x.id)

    def update_task_status(self, task_id: int, status: TaskStatus) -> Optional[Task]:
        if task_id in self._tasks:
            task = self._tasks[task_id]
            task.status = status
            return task
        return None

    def delete_task(self, task_id: int) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False

    def get_all_tasks(self) -> List[Task]:
        return list(self._tasks.values())

    def clear(self):
        self._tasks.clear()
        self._next_id = 1


_storage_instance = None


def get_storage() -> TaskStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = TaskStorage()
    return _storage_instance