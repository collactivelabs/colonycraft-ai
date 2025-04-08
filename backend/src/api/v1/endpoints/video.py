from fastapi import APIRouter, Depends
from ....tasks.video_tasks import generate_video_task
from ....models.task import Task, TaskStatus
from ....core.database import SessionLocal
from ....core.security import get_current_user

router = APIRouter()

@router.post("/generate-video")
async def generate_video(prompt: str, user=Depends(get_current_user)):
	db = SessionLocal()
	new_task = Task(user_id=user.id, type="video")
	new_task.status = TaskStatus.PROCESSING
	db.add(new_task)
	db.commit()
	generate_video_task.delay(new_task.id, prompt)
	return {"task_id": new_task.id, "status": "queued"}