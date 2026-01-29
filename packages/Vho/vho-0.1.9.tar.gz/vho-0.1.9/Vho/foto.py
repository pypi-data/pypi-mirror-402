import os
import cv2
import torch
import numpy as np
from PIL import Image
import mediapipe as mp
from diffusers import StableDiffusionInpaintPipeline, DPMSolverMultistepScheduler

device = "cuda" if torch.cuda.is_available() else "cpu"
dtype = torch.float16 if device == "cuda" else torch.float32

OUTPUT_FILE = "vho_pro.png"

NEGATIVE_PROMPT = (
    "worst quality, low quality, lowres, blurry, jpeg artifacts, "
    "bad anatomy, bad proportions, extra fingers, missing fingers, "
    "extra limbs, fused fingers, malformed hands, "
    "deformed face, distorted face, asymmetrical face, "
    "mutated, ugly"
)

def create_face_mask(image_path: str, mask_path: str = "face_mask.png") -> str:
    mp_face = mp.solutions.face_mesh.FaceMesh(static_image_mode=True)
    img = cv2.imread(image_path)

    if img is None:
        raise FileNotFoundError("Görsel okunamadı")

    h, w, _ = img.shape
    rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    res = mp_face.process(rgb)

    mask = np.ones((h, w), dtype=np.uint8) * 255

    if res.multi_face_landmarks:
        for face in res.multi_face_landmarks:
            points = []
            for lm in face.landmark:
                points.append((int(lm.x * w), int(lm.y * h)))
            hull = cv2.convexHull(np.array(points))
            cv2.fillConvexPoly(mask, hull, 0)

    Image.fromarray(mask).save(mask_path)
    return mask_path

pipe = StableDiffusionInpaintPipeline.from_pretrained(
    "runwayml/stable-diffusion-v1-5",
    dtype=dtype,
    safety_checker=None
).to(device)

pipe.scheduler = DPMSolverMultistepScheduler.from_config(pipe.scheduler.config)
pipe.enable_attention_slicing()

def create_foto(
    foto: str,
    prompt: str,
    strength: float = 0.75,
    cfg: float = 6.5,
    steps: int = 35,
    output: str = OUTPUT_FILE
) -> str:
    if not os.path.exists(foto):
        raise FileNotFoundError("Görsel bulunamadı")

    mask_path = create_face_mask(foto)

    image = Image.open(foto).convert("RGB")
    mask = Image.open(mask_path).convert("L")

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