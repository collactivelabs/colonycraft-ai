from fastapi import APIRouter, Depends
from src.tasks.image_tasks import generate_image_task
from src.models.task import Task, TaskStatus
from src.core.database import SessionLocal
from src.core.security import get_current_user

router = APIRouter()

@router.post("/generate-image")
async def generate_image(prompt: str, user=Depends(get_current_user)):
	with SessionLocal() as db:
		new_task = Task(user_id=user.id, type="image")
		new_task.status = TaskStatus.PROCESSING
		db.add(new_task)
		db.commit()
		generate_image_task.delay(new_task.id, prompt)
		return {"task_id": new_task.id, "status": "queued"}