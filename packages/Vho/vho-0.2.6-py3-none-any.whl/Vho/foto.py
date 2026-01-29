import torch
import random
import os
from PIL import Image
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline,
    DPMSolverMultistepScheduler
)
from deep_translator import GoogleTranslator

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

translator = GoogleTranslator(source="tr", target="en")

TR_STYLE_MAP = {
    "gerçekçi": "realistic",
    "sinematik": "cinematic lighting",
    "anime": "anime style",
    "çizgi film": "cartoon style",
    "karanlık": "dark dramatic mood",
    "neon": "neon cyberpunk lighting",
    "portre": "portrait photography",
    "detaylı": "highly detailed",
    "fantastik": "fantasy art",
    "bilim kurgu": "science fiction",
    "minimal": "minimalist composition",
}

QUALITY_LOCK = (
    "masterpiece, ultra high quality, professional photography, "
    "sharp focus, perfect lighting, high detail, clean composition"
)

NEGATIVE_LOCK = (
    "worst quality, low quality, lowres, blurry, jpeg artifacts, "
    "bad anatomy, bad proportions, deformed face, asymmetrical face, "
    "mutated, ugly"
)

def build_prompt(prompt_tr: str) -> str:
    translated = translator.translate(prompt_tr)
    styles = [en for tr, en in TR_STYLE_MAP.items() if tr in prompt_tr.lower()]
    return ", ".join([translated] + styles + [QUALITY_LOCK])

# ---------------- TEXT → IMAGE (REFERANS) ----------------

txt_pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

txt_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    txt_pipe.scheduler.config
)

def create_reference(prompt: str) -> Image.Image:
    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )
    return txt_pipe(
        prompt=build_prompt(prompt),
        negative_prompt=NEGATIVE_LOCK,
        guidance_scale=7.5,
        num_inference_steps=30,
        generator=generator
    ).images[0]

# ---------------- IMAGE + REFERANS BİRLEŞTİRME ----------------

img_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

img_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    img_pipe.scheduler.config
)

def create_foto(
    foto: str,
    prompt: str,
    strength: float = 0.55,
    output: str = "vho_pro_final.png"
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    real_image = Image.open(foto).convert("RGB")
    reference = create_reference(prompt)

    reference = reference.resize(real_image.size, Image.LANCZOS)
    blended = Image.blend(real_image, reference, alpha=0.35)

    result = img_pipe(
        prompt=build_prompt(prompt),
        negative_prompt=NEGATIVE_LOCK,
        image=blended,
        strength=strength,
        guidance_scale=6.5,
        num_inference_steps=35
    ).images[0]

    result.save(output)
    return os.path.abspath(output)