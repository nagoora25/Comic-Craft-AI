import os
import re
from pathlib import Path

from dotenv import load_dotenv
from huggingface_hub import InferenceClient


# Load .env
BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


# Folder where generated comic images are saved
PANELS_DIR = BASE_DIR / "static" / "panels"
PANELS_DIR.mkdir(parents=True, exist_ok=True)


# Hugging Face token
HF_API_KEY = os.getenv("HF_API_KEY")

# Image model
IMAGE_MODEL = os.getenv(
    "IMAGE_MODEL",
    "black-forest-labs/FLUX.1-schnell"
)


def safe_filename(text: str) -> str:
    """
    Convert prompt text into a safe filename.
    """

    text = re.sub(
        r"[^a-zA-Z0-9_-]+",
        "_",
        text
    )

    return text[:60]


def generate_image(
    image_prompt: str,
    art_style: str = "comic book"
):
    """
    Generate an actual AI image using
    Hugging Face Inference Providers.
    """

    if not HF_API_KEY:
        raise RuntimeError(
            "HF_API_KEY is missing in the .env file."
        )

    # Add art style to the AI prompt
    final_prompt = (
        f"{image_prompt}. "
        f"Art style: {art_style}. "
        "High quality comic panel, "
        "detailed characters, cinematic composition, "
        "clear scene, vibrant colors."
    )

    print("Generating AI image...")
    print("Prompt:", final_prompt)
    print("Model:", IMAGE_MODEL)

    # Hugging Face client
    client = InferenceClient(
        api_key=HF_API_KEY,
        provider="auto"
    )

    # Generate image
    image = client.text_to_image(
        prompt=final_prompt,
        model=IMAGE_MODEL,
        width=512,
        height=512,
        num_inference_steps=20,
        guidance_scale=7.5
    )

    # Create filename
    filename = safe_filename(image_prompt)

    if not filename:
        filename = "comic_panel"

    # Find next panel number
    existing_files = list(
        PANELS_DIR.glob(f"{filename}_*.png")
    )

    panel_number = len(existing_files) + 1

    image_path = PANELS_DIR / (
        f"{filename}_{panel_number}.png"
    )

    # Save actual AI-generated image
    image.save(
        image_path,
        format="PNG"
    )

    print("AI image generated successfully!")
    print("Saved:", image_path)

    # Return browser-accessible path
    return (
        "/static/panels/"
        + image_path.name
    )