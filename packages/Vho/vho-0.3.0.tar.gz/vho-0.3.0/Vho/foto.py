import os
import random
import torch
from PIL import Image
from diffusers import (
    StableDiffusionPipeline,
    StableDiffusionImg2ImgPipeline,
    DPMSolverMultistepScheduler
)
from deep_translator import GoogleTranslator

# =========================
# CONFIG
# =========================

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
OUTPUT_FILE = "vho.png"

translator = GoogleTranslator(source="tr", target="en")

NEGATIVE_PROMPT = (
    "worst quality, low quality, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, mutated, oversaturated, noisy"
)

# =========================
# PROMPT BUILDER
# =========================

def build_prompt(prompt_tr: str) -> str:
    translated = translator.translate(prompt_tr)
    return (
        translated
        + ", professional photography, clean color regions, "
        + "accurate hair color, accurate clothing color, "
        + "studio lighting, realistic skin tones"
    )

# =========================
# PIPELINES
# =========================

# 1) TEXT → IMAGE (REFERANS ÜRETİM)
txt_pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

txt_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    txt_pipe.scheduler.config
)

# 2) IMAGE → IMAGE (EDIT)
img_pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

img_pipe.scheduler = DPMSolverMultistepScheduler.from_config(
    img_pipe.scheduler.config
)

# =========================
# STAGE 1 — REFERENCE GENERATION
# =========================

def generate_reference(prompt: str) -> Image.Image:
    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )

    return txt_pipe(
        prompt=build_prompt(prompt),
        negative_prompt=NEGATIVE_PROMPT,
        guidance_scale=8.0,
        num_inference_steps=35,
        generator=generator
    ).images[0]

# =========================
# STAGE 2 — EDIT REAL IMAGE
# =========================

def edit_real_image(
    foto: str,
    prompt: str,
    strength: float = 0.55,
    cfg: float = 7.5,
    steps: int = 40
) -> Image.Image:
    base_image = Image.open(foto).convert("RGB")

    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )

    return img_pipe(
        prompt=build_prompt(prompt)
        + ", keep same person, preserve identity",
        negative_prompt=NEGATIVE_PROMPT,
        image=base_image,
        strength=strength,
        guidance_scale=cfg,
        num_inference_steps=steps,
        generator=generator
    ).images[0]

# =========================
# STAGE 3 — MERGE + POLISH
# =========================

def merge_and_polish(
    edited: Image.Image,
    reference: Image.Image,
    prompt: str
) -> Image.Image:
    reference = reference.resize(edited.size, Image.LANCZOS)

    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )

    return img_pipe(
        prompt=build_prompt(prompt)
        + ", final polish, cinematic grading, professional retouch",
        negative_prompt=NEGATIVE_PROMPT,
        image=edited,
        strength=0.25,
        guidance_scale=6.5,
        num_inference_steps=25,
        generator=generator
    ).images[0]

# =========================
# PUBLIC API
# =========================

def create_foto(
    foto: str,
    prompt: str
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    reference = generate_reference(prompt)
    edited = edit_real_image(foto, prompt)
    final = merge_and_polish(edited, reference, prompt)

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    final.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)