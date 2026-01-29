import os
import random
import shutil
from typing import Optional, List

import torch
import imageio
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from deep_translator import GoogleTranslator

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

FRAMES_DIR = "frames"
OUTPUT_VIDEO = "vho.mp4"

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
    "bad anatomy, bad proportions, extra fingers, missing fingers, "
    "extra limbs, fused fingers, malformed hands, "
    "deformed face, asymmetrical face, cross eye, lazy eye, "
    "distorted body, mutated, ugly"
)

translator = GoogleTranslator(source="tr", target="en")

def build_prompt(prompt_tr: str) -> str:
    translated = translator.translate(prompt_tr)
    prompt_lower = prompt_tr.lower()
    styles = [en for tr, en in TR_STYLE_MAP.items() if tr in prompt_lower]
    parts = [translated]
    if styles:
        parts.append(", ".join(styles))
    parts.append(QUALITY_LOCK)
    return ", ".join(parts)

_pipe: StableDiffusionPipeline | None = None

def load_pipe() -> StableDiffusionPipeline:
    global _pipe
    if _pipe is not None:
        return _pipe

    pipe = StableDiffusionPipeline.from_pretrained(
        "runwayml/stable-diffusion-v1-5",
        torch_dtype=DTYPE,
        safety_checker=None
    ).to(DEVICE)

    pipe.scheduler = DPMSolverMultistepScheduler.from_config(
        pipe.scheduler.config
    )
    pipe.enable_attention_slicing()

    _pipe = pipe
    return pipe

def generate_frames(
    prompt: str,
    num_frames: int = 24,
    kalite: float = 7.5,
    cfg: float = 7.5,
    seed: Optional[int] = None
) -> List[str]:

    if os.path.exists(FRAMES_DIR):
        shutil.rmtree(FRAMES_DIR)
    os.makedirs(FRAMES_DIR)

    pipe = load_pipe()
    final_prompt = build_prompt(prompt)

    if seed is None:
        seed = random.randint(0, 999_999_999)

    steps = int(20 + (kalite * 2))
    frame_paths: List[str] = []

    for i in range(num_frames):
        generator = torch.Generator(device=DEVICE).manual_seed(seed + i)

        image = pipe(
            prompt=final_prompt,
            negative_prompt=NEGATIVE_LOCK,
            num_inference_steps=steps,
            guidance_scale=float(cfg),
            generator=generator
        ).images[0]

        frame_path = os.path.join(FRAMES_DIR, f"frame_{i:04d}.png")
        image.save(frame_path)
        frame_paths.append(frame_path)

    return frame_paths

def frames_to_video(
    frame_paths: List[str],
    fps: int = 8,
    output: str = OUTPUT_VIDEO
) -> str:

    frames = [imageio.imread(fp) for fp in frame_paths]

    imageio.mimsave(
        output,
        frames,
        fps=fps,
        codec="libx264",
        quality=8
    )

    return os.path.abspath(output)

def create_video(
    prompt: str,
    fps: int = 8,
    num_frames: int = 24,
    kalite: float = 7.5,
    cfg: float = 7.5,
    seed: Optional[int] = None
) -> str:
    frames = generate_frames(
        prompt=prompt,
        num_frames=num_frames,
        kalite=kalite,
        cfg=cfg,
        seed=seed
    )
    return frames_to_video(frames, fps=fps)