import os
import torch
import random
from PIL import Image
from diffusers import (
    StableDiffusionControlNetPipeline,
    ControlNetModel,
    DPMSolverMultistepScheduler
)
from controlnet_aux import OpenposeDetector
from deep_translator import GoogleTranslator

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

OUTPUT_FILE = "vho.png"

NEGATIVE_PROMPT = (
    "worst quality, low quality, lowres, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, asymmetrical face, mutated, "
    "extra limbs, distorted face, plastic skin"
)

QUALITY_LOCK = (
    "ultra high quality, professional studio portrait, "
    "cinematic lighting, sharp focus, realistic skin texture"
)

FACE_LOCK = (
    "same person, same face, same identity, preserve facial structure, "
    "preserve eyes, preserve nose, preserve mouth, "
    "real human face, natural proportions"
)

translator = GoogleTranslator(source="tr", target="en")

def parse_prompt(prompt_tr: str) -> str:
    translated = translator.translate(prompt_tr)
    return f"{translated}, {QUALITY_LOCK}, {FACE_LOCK}"

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

pipe.load_ip_adapter(
    "h94/IP-Adapter",
    subfolder="models",
    weight_name="ip-adapter-plus-face_sd15.safetensors"
)

pipe.set_ip_adapter_scale(1.05)

openpose = OpenposeDetector.from_pretrained("lllyasviel/ControlNet")

def extract_pose(path: str) -> Image.Image:
    return openpose(Image.open(path).convert("RGB"))

def create_foto(
    foto: str,
    prompt: str,
    seed: int | None = None,
    steps: int = 45,
    cfg: float = 7.5
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    if seed is None:
        seed = random.randint(0, 999999999)

    generator = torch.Generator(device=device).manual_seed(seed)

    reference = Image.open(foto).convert("RGB")
    pose = extract_pose(foto)

    final_prompt = parse_prompt(prompt)

    result = pipe(
        prompt=final_prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=pose,
        ip_adapter_image=reference,
        guidance_scale=cfg,
        num_inference_steps=steps,
        generator=generator,
        controlnet_conditioning_scale=1.0
    ).images[0]

    if os.path.exists(OUTPUT_FILE):
        os.remove(OUTPUT_FILE)

    result.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)