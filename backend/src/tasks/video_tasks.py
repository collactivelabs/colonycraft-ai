from ..core.celery import celery
from ..services.video_service import generate_video
from ..services.storage_service import upload_to_gcs
from ..models.task import Task, TaskStatus
from ..models.file import File
from ..core.database import SessionLocal


@celery.task
def generate_video_task(task_id: int, inputs: list):
	with SessionLocal() as db:
		new_task = db.query(Task).filter(Task.id == task_id).first()
		new_task.status = TaskStatus.PROCESSING

		# Generate the video
		video_path = generate_video(inputs)

		# Upload to GCS
		destination_path = f"videos/{task_id}.mp4"
		with open(video_path, "rb") as video_file:
			video_url = upload_to_gcs(video_file, destination_path)

		# Save file metadata to the database
		file = File(
			user_id=new_task.user_id,
			file_url=video_url,
			type="video"
		)
		db.add(file)
		db.commit()

		# Update the task
		new_task.result_url = video_url
		new_task.status = "completed"
		db.commit()