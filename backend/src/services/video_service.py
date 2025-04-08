import ffmpeg
import tempfile

def generate_video(image_paths: list) -> str:
	output_path = tempfile.mktemp(suffix=".mp4")
	ffmpeg.input(' '.join(image_paths), pattern_type='glob', framerate=1).output(output_path).run()
	return output_path