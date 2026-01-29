import os
import random
import logging
from dataclasses import dataclass
from typing import Optional

import torch
import imageio
from diffusers import AnimateDiffPipeline, DPMSolverMultistepScheduler, MotionAdapter
from deep_translator import GoogleTranslator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)
logger = logging.getLogger("videogen")

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

@dataclass
class VideoConfig:
    fps: int = 8
    num_frames: int = 24
    kalite: float = 7.5
    cfg: float = 7.5
    seed: Optional[int] = None
    filename: str = "output.mp4"

class PromptBuilder:
    @staticmethod
    def build(prompt_tr: str) -> str:
        translated = translator.translate(prompt_tr)
        prompt_lower = prompt_tr.lower()
        styles = [
            en for tr, en in TR_STYLE_MAP.items()
            if tr in prompt_lower
        ]
        parts = [translated]
        if styles:
            parts.append(", ".join(styles))
        parts.append(QUALITY_LOCK)
        final_prompt = ", ".join(parts)
        logger.debug(final_prompt)
        return final_prompt

class AnimateDiffVideoGenerator:
    _pipe = None

    def __init__(self):
        self.device = DEVICE
        self.dtype = DTYPE

    def _load_pipe(self):
        if AnimateDiffVideoGenerator._pipe is not None:
            return AnimateDiffVideoGenerator._pipe

        motion_adapter = MotionAdapter.from_pretrained(
            "guoyww/animatediff-motion-adapter-v1-5",
            torch_dtype=self.dtype
        )

        pipe = AnimateDiffPipeline.from_pretrained(
            "runwayml/stable-diffusion-v1-5",
            motion_adapter=motion_adapter,
            torch_dtype=self.dtype,
            safety_checker=None
        ).to(self.device)

        pipe.scheduler = DPMSolverMultistepScheduler.from_config(
            pipe.scheduler.config
        )
        pipe.enable_attention_slicing()

        AnimateDiffVideoGenerator._pipe = pipe
        return pipe

    def generate(self, prompt: str, config: VideoConfig) -> str:
        pipe = self._load_pipe()

        seed = config.seed or random.randint(0, 999_999_999)
        generator = torch.Generator(device=self.device).manual_seed(seed)

        steps = int(20 + (config.kalite * 2))
        final_prompt = PromptBuilder.build(prompt)

        result = pipe(
            prompt=final_prompt,
            negative_prompt=NEGATIVE_LOCK,
            num_frames=config.num_frames,
            num_inference_steps=steps,
            guidance_scale=float(config.cfg),
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

        return os.path.abspath(config.filename)

def create_video(
    prompt: str,
    fps: int = 8,
    kalite: float = 7.5,
    cfg: float = 7.5,
    seed: Optional[int] = None,
    filename: str = "video.mp4"
) -> str:
    config = VideoConfig(
        fps=fps,
        kalite=kalite,
        cfg=cfg,
        seed=seed,
        filename=filename
    )
    generator = AnimateDiffVideoGenerator()
    return generator.generate(prompt, config)

__all__ = ["create_video", "VideoConfig"]