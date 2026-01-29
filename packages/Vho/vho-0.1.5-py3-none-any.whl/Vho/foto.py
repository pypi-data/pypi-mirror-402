import os
import random
import torch
from PIL import Image

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def create_foto(
    foto: str,
    prompt: str,
    strength: float = 0.45,
    cfg: float = 6.5,
    steps: int = 32,
    seed: int | None = None,
    filename: str | None = None
) -> str:
    foto_path = foto
    if not os.path.isabs(foto):
        foto_path = os.path.join(BASE_DIR, foto)

    if not os.path.exists(foto_path):
        raise FileNotFoundError(f"Görsel bulunamadı: {foto_path}")

    init_image = Image.open(foto_path).convert("RGB")

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

    out_name = filename or FIXED_OUTPUT_FILE
    out_path = os.path.join(BASE_DIR, out_name)

    if os.path.exists(out_path):
        os.remove(out_path)

    image.save(out_path)
    return out_path