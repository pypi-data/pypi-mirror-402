import torch  
import random  
import os  
from datetime import datetime  
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler  
from deep_translator import GoogleTranslator  
  
device = "cuda" if torch.cuda.is_available() else "cpu"  
dtype = torch.float16 if device == "cuda" else torch.float32  
  
FIXED_OUTPUT_FILE = "vho1.png"  
  
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
    "minimal": "minimalist composition"  
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
  
def _build_prompt(prompt_tr: str) -> str:  
    translated = translator.translate(prompt_tr)  
    prompt_lower = prompt_tr.lower()  
    styles = []  
    for tr, en in TR_STYLE_MAP.items():  
        if tr in prompt_lower:  
            styles.append(en)  
  
    parts = [translated]  
    if styles:  
        parts.append(", ".join(styles))  
    parts.append(QUALITY_LOCK)  
    return ", ".join(parts)  
  
_pipe = StableDiffusionPipeline.from_pretrained(  
    "runwayml/stable-diffusion-v1-5",  
    torch_dtype=dtype,  
    safety_checker=None  
).to(device)  
  
_pipe.scheduler = DPMSolverMultistepScheduler.from_config(_pipe.scheduler.config)  
_pipe.enable_attention_slicing()  
  
def create_text(  
    prompt: str,  
    kalite: float = 7.5,  
    cfg: float = 7.5,  
    steps: int | None = None,  
    seed: int | None = None,  
    filename: str | None = None  
) -> str:  
    final_prompt = _build_prompt(prompt)  
  
    if steps is None:  
        steps = int(20 + (kalite * 2))  
  
    if seed is None:  
        seed = random.randint(0, 999999999)  
  
    generator = torch.Generator(device=device).manual_seed(seed)  
  
    image = _pipe(  
        prompt=final_prompt,  
        negative_prompt=NEGATIVE_LOCK,  
        num_inference_steps=steps,  
        guidance_scale=float(cfg),  
        generator=generator  
    ).images[0]  
  
    filename = FIXED_OUTPUT_FILE  
  
    if os.path.exists(filename):  
        os.remove(filename)  
  
    image.save(filename)  
    return os.path.abspath(filename)  
  