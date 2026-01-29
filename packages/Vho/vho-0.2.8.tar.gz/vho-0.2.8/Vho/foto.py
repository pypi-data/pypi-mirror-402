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

OUTPUT_FILE = "vho.png"

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

# -------- TEXT → IMAGE (SADECE STİL REFERANSI İÇİN) --------

txt_pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

txt_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    txt_pipe.scheduler.config
)

def create_style_reference(prompt: str) -> str:
    ref_prompt = build_prompt(prompt) + ", style reference, color reference, lighting reference"
    return ref_prompt

# -------- IMAGE → IMAGE (ASİL PROFESYONEL ADIM) --------

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
    strength: float = 0.62,
    cfg: float = 8.0,
    steps: int = 40
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    base_image = Image.open(foto).convert("RGB")

    final_prompt = (
        build_prompt(prompt)
        + ", keep same person, preserve identity, realistic skin, "
        + "professional studio look"
    )

    style_guidance = create_style_reference(prompt)

    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )

    result = img_pipe(
        prompt=final_prompt + ", " + style_guidance,
        negative_prompt=NEGATIVE_LOCK,
        image=base_image,
        strength=strength,
        guidance_scale=cfg,
        num_inference_steps=steps,
        generator=generator
    ).images[0]

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    result.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)