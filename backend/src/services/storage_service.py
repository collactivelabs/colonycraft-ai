from google.cloud import storage
from ..core.config import settings
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = settings.GOOGLE_APPLICATION_CREDENTIALS

def upload_to_gcs(file, destination_path: str) -> str:
	"""
	Uploads a file to Google Cloud Storage and returns the public URL.
	"""
	client = storage.Client()
	bucket = client.bucket(settings.gcs_bucket_name)
	blob = bucket.blob(destination_path)
	blob.upload_from_file(file.file)
	blob.make_public()
	return blob.public_url