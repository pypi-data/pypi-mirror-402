import os
import random
from dataclasses import dataclass
from typing import Optional

import torch
import imageio
from diffusers import AnimateDiffPipeline, DPMSolverMultistepScheduler, MotionAdapter
from deep_translator import GoogleTranslator

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
DTYPE = torch.float16 if DEVICE == "cuda" else torch.float32

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
    "masterpiece, ultra high quality, professional cinematic visuals, "
    "sharp focus, perfect lighting, high detail"
)

NEGATIVE_LOCK = (
    "worst quality, low quality, lowres, blurry, jpeg artifacts, "
    "bad anatomy, bad proportions, extra fingers, missing fingers, "
    "extra limbs, fused fingers, malformed hands, "
    "deformed face, asymmetrical face, cross eye, lazy eye, "
    "distorted body, mutated, ugly"
)

translator = GoogleTranslator(source="tr", target="en")

@dataclass(frozen=True)
class VideoConfig:
    fps: int = 8
    frames: int = 24
    kalite: float = 7.5
    cfg: float = 7.5
    seed: Optional[int] = None
    filename: str = "video.mp4"

class _PromptEngine:
    @staticmethod
    def build(prompt: str) -> str:
        translated = translator.translate(prompt)
        lower = prompt.lower()
        styles = [v for k, v in TR_STYLE_MAP.items() if k in lower]
        base = [translated]
        if styles:
            base.append(", ".join(styles))
        base.append(QUALITY_LOCK)
        return ", ".join(base)

class _Pipeline:
    _instance = None

    @staticmethod
    def get():
        if _Pipeline._instance is not None:
            return _Pipeline._instance

        adapter = MotionAdapter.from_pretrained(
            "guoyww/animatediff-motion-adapter-v1-5",
            torch_dtype=DTYPE
        )

        pipe = AnimateDiffPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            motion_adapter=adapter,
            torch_dtype=DTYPE,
            safety_checker=None
        ).to(DEVICE)

        pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
        pipe.enable_attention_slicing()

        if DEVICE == "cuda":
            pipe.enable_xformers_memory_efficient_attention()

        _Pipeline._instance = pipe
        return pipe

def create_video(prompt: str, config: VideoConfig) -> str:
    seed = config.seed if config.seed is not None else random.randint(0, 2**32 - 1)
    generator = torch.Generator(device=DEVICE).manual_seed(seed)
    steps = int(20 + config.kalite * 2)
    final_prompt = _PromptEngine.build(prompt)
    pipe = _Pipeline.get()

    with torch.inference_mode(), torch.autocast(
        DEVICE, enabled=(DEVICE == "cuda")
    ):
        result = pipe(
            prompt=final_prompt,
            negative_prompt=NEGATIVE_LOCK,
            num_frames=config.frames,
            num_inference_steps=steps,
            guidance_scale=config.cfg,
            generator=generator
        )

    frames = result.frames[0]

    imageio.mimsave(
        config.filename,
        frames,
        fps=config.fps,
        codec="libx264",
        quality=8
    )

    torch.cuda.empty_cache() if DEVICE == "cuda" else None
    return os.path.abspath(config.filename)