import os
import torch
from PIL import Image
from diffusers import StableDiffusionControlNetPipeline, ControlNetModel, DPMSolverMultistepScheduler
from controlnet_aux import OpenposeDetector

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
OUTPUT_FILE = "vho.png"

NEGATIVE_PROMPT = (
    "worst quality, low quality, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, asymmetrical face, mutated"
)

controlnet = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_openpose",
    torch_dtype=dtype
).to(device)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet,
    torch_dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()

openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

def extract_pose(image_path: str) -> Image.Image:
    img = Image.open(image_path).convert("RGB")
    return openpose(img)

def create_foto(
    foto: str,
    prompt: str
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    pose_image = extract_pose(foto)

    result = pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=pose_image,
        guidance_scale=7.5,
        num_inference_steps=35,
        controlnet_conditioning_scale=1.0
    ).images[0]

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    result.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)