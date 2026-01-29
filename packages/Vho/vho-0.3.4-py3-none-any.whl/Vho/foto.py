import os
import torch
from PIL import Image
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    DPMSolverMultistepScheduler
)
from controlnet_aux import OpenposeDetector

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
OUTPUT_FILE = "vho.png"

NEGATIVE_PROMPT = (
    "worst quality, low quality, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, asymmetrical face, mutated"
)

controlnet_pose = ControlNetModel.from_pretrained(
    "lllyasviel/control_v11p_sd15_openpose",
    torch_dtype=dtype
).to(device)

pipe = StableDiffusionControlNetPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    controlnet=controlnet_pose,
    torch_dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()

pipe.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="models",
    weight_name="ip-adapter-plus-face_sd15.safetensors"
)

pipe.set_ip_adapter_scale(0.85)

openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

def extract_pose(image_path: str) -> Image.Image:
    img = Image.open(image_path).convert("RGB")
    return openpose(img)

def create_foto(
    foto: str,
    prompt: str,
    steps: int = 40,
    cfg: float = 7.5
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    base_image = Image.open(foto).convert("RGB")
    pose_image = extract_pose(foto)

    result = pipe(
        prompt=prompt + ", professional portrait, cinematic lighting, high detail",
        negative_prompt=NEGATIVE_PROMPT,
        image=pose_image,
        ip_adapter_image=base_image,
        guidance_scale=cfg,
        num_inference_steps=steps,
        controlnet_conditioning_scale=1.0
    ).images[0]

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    result.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)