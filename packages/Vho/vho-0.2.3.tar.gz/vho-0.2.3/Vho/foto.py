import os
import cv2
import torch
import numpy as np
from PIL import Image
from diffusers import StableDiffusionInpaintPipeline, DPMSolverMultistepScheduler

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

NEGATIVE_PROMPT = (
    "worst quality, low quality, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, asymmetrical face, mutated"
)

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()


def _detect_face(gray):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    return face_cascade.detectMultiScale(gray, 1.1, 5, minSize=(80, 80))


def face_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.ones((h, w), dtype=np.uint8) * 255

    for (x, y, fw, fh) in _detect_face(gray):
        cx, cy = x + fw // 2, y + fh // 2
        r = int(max(fw, fh) * 0.42)
        cv2.circle(mask, (cx, cy), r, 0, -1)

    return Image.fromarray(mask)


def hair_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.zeros((h, w), dtype=np.uint8)

    for (x, y, fw, fh) in _detect_face(gray):
        top = max(0, y - int(fh * 0.9))
        bottom = y + int(fh * 0.2)
        left = max(0, x - int(fw * 0.3))
        right = min(w, x + fw + int(fw * 0.3))
        mask[top:bottom, left:right] = 255

    return Image.fromarray(mask)


def clothes_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.zeros((h, w), dtype=np.uint8)

    for (x, y, fw, fh) in _detect_face(gray):
        top = y + fh
        bottom = min(h, y + int(fh * 3.0))
        left = max(0, x - int(fw * 1.2))
        right = min(w, x + fw + int(fw * 1.2))
        mask[top:bottom, left:right] = 255

    return Image.fromarray(mask)


def _inpaint(image, mask, prompt, strength):
    return pipe(
        prompt=prompt,
        negative_prompt=NEGATIVE_PROMPT,
        image=image,
        mask_image=mask,
        strength=strength,
        guidance_scale=6.5,
        num_inference_steps=35
    ).images[0]


def create_foto(
    foto: str,
    prompt: str,
    output: str = "vho.png"
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    img = cv2.imread(foto)
    base = Image.open(foto).convert("RGB")

    f_mask = face_mask(img).convert("L")
    h_mask = hair_mask(img).convert("L")
    c_mask = clothes_mask(img).convert("L")

    step1 = _inpaint(
        base,
        f_mask,
        "same face, same identity, preserve face",
        strength=0.3
    )

    step2 = _inpaint(
        step1,
        h_mask,
        "vivid purple dyed hair, high saturation",
        strength=0.85
    )

    step3 = _inpaint(
        step2,
        c_mask,
        "wearing a bright red dress, elegant clothing",
        strength=0.85
    )

    final = pipe(
        prompt=prompt + ", cinematic studio lighting, professional portrait",
        negative_prompt=NEGATIVE_PROMPT,
        image=step3,
        strength=0.25,
        guidance_scale=6.5,
        num_inference_steps=25
    ).images[0]

    final.save(output)
    return os.path.abspath(output)