import os
import json
import re
import time

from dotenv import load_dotenv
from google import genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

OUTLINE_MODEL = os.getenv(
    "OUTLINE_MODEL",
    "gemini-3.7-flash"
)

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )

client = genai.Client(
    api_key=GEMINI_API_KEY
)


def clean_json_response(text: str):
    text = text.strip()

    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


def generate_outline(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
):

    prompt = f"""
You are an expert comic book story planner.

Create a complete 5-panel comic outline.

Story prompt:
{story_prompt}

Main character:
{character_name}

Setting:
{setting}

Tone:
{tone}

Art style:
{art_style}

For each panel provide:

- panel_number
- title
- scene_description
- image_prompt

The image_prompt must be detailed enough
for an AI image generator to create the scene.

Keep the same main character consistent
through all five panels.

Make the story flow naturally from
panel 1 to panel 5.

Return ONLY valid JSON.

Do not write markdown.
Do not write explanations.

Use exactly this structure:

[
  {{
    "panel_number": 1,
    "title": "Panel title",
    "scene_description": "Scene description",
    "image_prompt": "Detailed image generation prompt"
  }},
  {{
    "panel_number": 2,
    "title": "Panel title",
    "scene_description": "Scene description",
    "image_prompt": "Detailed image generation prompt"
  }},
  {{
    "panel_number": 3,
    "title": "Panel title",
    "scene_description": "Scene description",
    "image_prompt": "Detailed image generation prompt"
  }},
  {{
    "panel_number": 4,
    "title": "Panel title",
    "scene_description": "Scene description",
    "image_prompt": "Detailed image generation prompt"
  }},
  {{
    "panel_number": 5,
    "title": "Panel title",
    "scene_description": "Scene description",
    "image_prompt": "Detailed image generation prompt"
  }}
]
"""

    max_attempts = 5

    for attempt in range(max_attempts):

        try:

            print(
                f"Generating comic outline... "
                f"Attempt {attempt + 1}/{max_attempts}"
            )

            response = client.models.generate_content(
                model=OUTLINE_MODEL,
                contents=prompt
            )

            raw_text = response.text

            if not raw_text:
                raise ValueError(
                    "Gemini returned an empty response."
                )

            cleaned = clean_json_response(
                raw_text
            )

            outline = json.loads(
                cleaned
            )

            if not isinstance(
                outline,
                list
            ):
                raise ValueError(
                    "Gemini outline response is not a list."
                )

            if len(outline) != 5:
                raise ValueError(
                    "Expected 5 panels but received "
                    f"{len(outline)}."
                )

            required_fields = [
                "panel_number",
                "title",
                "scene_description",
                "image_prompt"
            ]

            for index, panel in enumerate(outline):

                if not isinstance(
                    panel,
                    dict
                ):
                    raise ValueError(
                        f"Panel {index + 1} is invalid."
                    )

                for field in required_fields:

                    if field not in panel:

                        raise ValueError(
                            f"Panel {index + 1} "
                            f"is missing: {field}"
                        )

            print(
                "Comic outline generated successfully!"
            )

            return outline

        except Exception as e:

            print(
                f"Gemini request failed: {e}"
            )

            if attempt == max_attempts - 1:

                raise RuntimeError(
                    "Gemini is currently unavailable "
                    "after multiple attempts.\n\n"
                    f"Original error:\n{e}"
                )

            wait_time = 5 * (2 ** attempt)

            print(
                f"Retrying in {wait_time} seconds..."
            )

            time.sleep(wait_time)