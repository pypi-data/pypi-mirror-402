import os
import random
import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

FIXED_OUTPUT_FILE = "vho1.png"

NEGATIVE_LOCK = (
    "worst quality, low quality, lowres, blurry, jpeg artifacts, "
    "bad anatomy, bad proportions, extra fingers, missing fingers, "
    "extra limbs, fused fingers, malformed hands, "
    "deformed face, asymmetrical face, cross eye, lazy eye, "
    "distorted body, mutated, ugly"
)

def _build_prompt(prompt: str) -> str:
    return prompt

_img2img_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

_img2img_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    _img2img_pipe.scheduler.config
)

_img2img_pipe.enable_attention_slicing()

def create_foto(
    foto: str,
    prompt: str,
    strength: float = 0.45,
    cfg: float = 6.5,
    steps: int = 32,
    seed: int | None = None,
    filename: str | None = None
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError(f"Görsel bulunamadı: {foto}")

    init_image = Image.open(foto).convert("RGB")

    FACE_LOCK = (
        "same person, same face, same identity, "
        "preserve facial structure, preserve eyes, "
        "preserve face proportions, "
        "natural human face, realistic skin texture"
    )

    FACE_NEGATIVE = (
        "different face, different person, face changed, "
        "deformed face, distorted face, plastic face, "
        "anime face, doll face, wax face, "
        "over-sharpened face, over-smoothed skin"
    )

    final_prompt = _build_prompt(prompt) + ", " + FACE_LOCK
    final_negative = NEGATIVE_LOCK + ", " + FACE_NEGATIVE

    if seed is None:
        seed = random.randint(0, 999999999)

    generator = torch.Generator(device=device).manual_seed(seed)

    image = _img2img_pipe(
        prompt=final_prompt,
        negative_prompt=final_negative,
        image=init_image,
        strength=strength,
        guidance_scale=float(cfg),
        num_inference_steps=steps,
        generator=generator
    ).images[0]

    filename = filename or FIXED_OUTPUT_FILE

    if os.path.exists(filename):
        os.remove(filename)

    image.save(filename)
    return os.path.abspath(filename)