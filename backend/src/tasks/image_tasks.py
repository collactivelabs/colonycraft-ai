from ..core.database import get_db_context, Session
from ..core.celery import celery
from ..services.image_service import generate_image
from ..services.storage_service import upload_to_gcs
from ..models.task import Task, TaskStatus
from io import BytesIO
from ..core.exceptions import logger

@celery.task
def generate_image_task(task_id: int, prompt: str):
	with get_db_context() as db:
		new_task = db.query(Task).filter(Task.id == task_id).first()
		if not new_task:
			logger.error(f"Task {task_id} not found")
			return

		try:
			new_task.status = TaskStatus.PROCESSING
			db.commit()

			image = generate_image(prompt)
			image_bytes = BytesIO()
			image.save(image_bytes, format="PNG")
			image_bytes.seek(0)

			destination_path = f"images/{task_id}.png"
			image_url = upload_to_gcs(image_bytes, destination_path)

			file = file(
				user_id=new_task.user_id,
				file_url=image_url,
				type="image"
			)
			db.add(file)

			new_task.result_url = image_url
			new_task.status = TaskStatus.COMPLETED

		except Exception as e:
			logger.error(f"Failed to process task {task_id}: {str(e)}", exc_info=True)
			new_task.status = TaskStatus.FAILED
			new_task.error_message = str(e)
			raise