import os
import cv2
import torch
import numpy as np
from PIL import Image
from diffusers import StableDiffusionInpaintPipeline, DPMSolverMultistepScheduler

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

OUTPUT_FILE = "vho.png"

NEGATIVE_PROMPT = (
    "worst quality, low quality, lowres, blurry, jpeg artifacts, "
    "bad anatomy, bad proportions, extra fingers, missing fingers, "
    "extra limbs, fused fingers, malformed hands, "
    "deformed face, distorted face, asymmetrical face, "
    "mutated, ugly"
)

def create_face_mask(image_path: str) -> Image.Image:
    img = cv2.imread(image_path)
    if img is None:
        raise FileNotFoundError("Görsel okunamadı")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape

    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )

    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(80, 80)
    )

    mask = np.ones((h, w), dtype=np.uint8) * 255

    for (x, y, fw, fh) in faces:
        cx = x + fw // 2
        cy = y + fh // 2
        r = int(max(fw, fh) * 0.42)
        cv2.circle(mask, (cx, cy), r, 0, -1)

    return Image.fromarray(mask)

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()

def create_foto(
    foto: str,
    prompt: str,
    strength: float = 0.82,
    cfg: float = 6.5,
    steps: int = 35,
    output: str = OUTPUT_FILE
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    image = Image.open(foto).convert("RGB")
    mask = create_face_mask(foto).convert("L")

    final_prompt = (
        prompt
        + ", ultra realistic, professional portrait, cinematic lighting, "
        + "sharp focus, high detail, natural skin texture"
    )

    result = pipe(
        prompt=final_prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=image,
        mask_image=mask,
        strength=strength,
        guidance_scale=cfg,
        num_inference_steps=steps
    ).images[0]

    if os.path.exists(output):
        os.remove(output)

    result.save(output)
    return os.path.abspath(output)