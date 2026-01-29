import os
import random
import torch
from PIL import Image
from diffusers import StableDiffusionImg2ImgPipeline, DPMSolverMultistepScheduler
from deep_translator import GoogleTranslator

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

OUTPUT_FILE = "vho.png"

translator = GoogleTranslator(source="tr", target="en")

NEGATIVE_PROMPT = (
    "worst quality, low quality, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, mutated, oversaturated, noisy"
)

def build_prompt(prompt_tr: str) -> str:
    translated = translator.translate(prompt_tr)
    return (
        translated
        + ", professional photography, clean color regions, "
        + "accurate hair color, accurate clothing color, "
        + "studio lighting, realistic skin tones"
    )

pipe = StableDiffusionImg2ImgPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)

pipe.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="models",
    weight_name="ip-adapter_sd15.bin"
)

pipe.set_ip_adapter_scale(0.85)

def create_foto(
    foto: str,
    prompt: str,
    strength: float = 0.55,
    steps: int = 40,
    cfg: float = 7.5
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    base_image = Image.open(foto).convert("RGB")

    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )

    final_prompt = build_prompt(prompt)

    result = pipe(
        prompt=final_prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=base_image,
        ip_adapter_image=base_image,
        strength=strength,
        guidance_scale=cfg,
        num_inference_steps=steps,
        generator=generator
    ).images[0]

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    result.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)