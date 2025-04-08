from diffusers import StableDiffusionPipeline
import torch
from PIL import Image

def generate_image(prompt: str, style: str = "default") -> Image.Image:
	pipe = StableDiffusionPipeline.from_pretrained("stabilityai/stable-diffusion-2-1").to("cuda" if torch.cuda.is_available() else "cpu")
	image = pipe(prompt).images[0]
	return Image.fromarray(image)