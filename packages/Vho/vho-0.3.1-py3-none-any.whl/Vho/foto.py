import os
import cv2
import torch
import random
import numpy as np
from PIL import Image
from diffusers import StableDiffusionPipeline, StableDiffusionInpaintPipeline, DPMSolverMultistepScheduler
from deep_translator import GoogleTranslator

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32
OUTPUT_FILE = "vho.png"

translator = GoogleTranslator(source="tr", target="en")

NEGATIVE_PROMPT = (
    "worst quality, low quality, blurry, jpeg artifacts, "
    "bad anatomy, deformed face, asymmetrical face, mutated"
)

QUALITY_LOCK = (
    "masterpiece, ultra high quality, professional photography, "
    "sharp focus, perfect lighting, high detail, clean composition"
)

def build_prompt(prompt_tr: str) -> str:
    translated = translator.translate(prompt_tr)
    return translated + ", " + QUALITY_LOCK

txt_pipe = StableDiffusionPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

txt_pipe.scheduler = DPMSolverMultistepScheduler.from_config(txt_pipe.scheduler.config)

def generate_reference(prompt: str) -> Image.Image:
    generator = torch.Generator(device=device).manual_seed(
        random.randint(0, 999999999)
    )
    return txt_pipe(
        prompt=build_prompt(prompt),
        negative_prompt=NEGATIVE_PROMPT,
        guidance_scale=7.5,
        num_inference_steps=30,
        generator=generator
    ).images[0]

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    torch_dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()

def detect_face(gray):
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
    )
    return face_cascade.detectMultiScale(
        gray, scaleFactor=1.1, minNeighbors=5, minSize=(80, 80)
    )

def face_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.ones((h, w), dtype=np.uint8) * 255
    for (x, y, fw, fh) in detect_face(gray):
        cx, cy = x + fw // 2, y + fh // 2
        r = int(max(fw, fh) * 0.42)
        cv2.circle(mask, (cx, cy), r, 0, -1)
    return Image.fromarray(mask)

def hair_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    for (x, y, fw, fh) in detect_face(gray):
        top = max(0, y - int(fh * 0.9))
        bottom = y + int(fh * 0.25)
        left = max(0, x - int(fw * 0.35))
        right = min(w, x + fw + int(fw * 0.35))
        mask[top:bottom, left:right] = 255
    return Image.fromarray(mask)

def clothes_mask(img):
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    mask = np.zeros((h, w), dtype=np.uint8)
    for (x, y, fw, fh) in detect_face(gray):
        top = y + fh
        bottom = min(h, y + int(fh * 3.0))
        left = max(0, x - int(fw * 1.2))
        right = min(w, x + fw + int(fw * 1.2))
        mask[top:bottom, left:right] = 255
    return Image.fromarray(mask)

def full_mask(image: Image.Image) -> Image.Image:
    w, h = image.size
    return Image.new("L", (w, h), 255)

def inpaint(image, mask, prompt, strength):
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
    prompt: str
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    img_cv = cv2.imread(foto)
    base = Image.open(foto).convert("RGB")

    reference = generate_reference(prompt)

    f_mask = face_mask(img_cv).convert("L")
    h_mask = hair_mask(img_cv).convert("L")
    c_mask = clothes_mask(img_cv).convert("L")

    step1 = inpaint(
        base,
        f_mask,
        "same face, same identity, preserve facial features",
        strength=0.30
    )

    step2 = inpaint(
        step1,
        h_mask,
        "vivid purple dyed hair, high saturation",
        strength=0.85
    )

    step3 = inpaint(
        step2,
        c_mask,
        "wearing a bright red dress, elegant clothing",
        strength=0.85
    )

    reference = reference.resize(step3.size, Image.LANCZOS)

    final = pipe(
        prompt=build_prompt(prompt) + ", cinematic studio lighting",
        negative_prompt=NEGATIVE_PROMPT,
        image=step3,
        mask_image=full_mask(step3),
        strength=0.25,
        guidance_scale=6.5,
        num_inference_steps=25
    ).images[0]

    final.save(OUTPUT_FILE)
    return os.path.abspath(OUTPUT_FILE)