import os
import json
import re
import time

from dotenv import load_dotenv
from google import genai


# ==================================================
# LOAD ENVIRONMENT VARIABLES
# ==================================================

load_dotenv()


# ==================================================
# GEMINI CONFIGURATION
# ==================================================

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

STORY_MODEL = os.getenv(
    "STORY_MODEL",
    "gemini-3.8-flash"
)


# ==================================================
# CHECK API KEY
# ==================================================

if not GEMINI_API_KEY:
    raise RuntimeError(
        "GEMINI_API_KEY is missing from .env"
    )


# ==================================================
# CREATE GEMINI CLIENT
# ==================================================

client = genai.Client(
    api_key=GEMINI_API_KEY
)


# ==================================================
# CLEAN JSON RESPONSE
# ==================================================

def clean_json_response(text: str):

    text = text.strip()

    # Remove ```json
    text = re.sub(
        r"^```json\s*",
        "",
        text,
        flags=re.IGNORECASE
    )

    # Remove ```
    text = re.sub(
        r"^```\s*",
        "",
        text
    )

    # Remove closing ```
    text = re.sub(
        r"\s*```$",
        "",
        text
    )

    return text.strip()


# ==================================================
# GENERATE STORY
# ==================================================

def generate_story(
    outline,
    character_name: str,
    tone: str,
    art_style: str
):

    # --------------------------------------------------
    # CONVERT OUTLINE TO TEXT
    # --------------------------------------------------

    outline_text = json.dumps(
        outline,
        indent=2
    )


    # --------------------------------------------------
    # CREATE PROMPT
    # --------------------------------------------------

    prompt = f"""
You are a professional comic book writer.

Create detailed narration and dialogue
for a 5-panel comic story.

Main character:
{character_name}

Story tone:
{tone}

Art style:
{art_style}

Comic outline:
{outline_text}

For every panel, create:

- panel_number
- narration
- dialogue

The narration should clearly explain
what is happening in the scene.

The dialogue should contain natural
conversation between characters when appropriate.

Keep the story connected from panel 1
to panel 5.

Make the story engaging and suitable
for a comic book.

Return ONLY valid JSON.

Do not write any explanation before
or after the JSON.

Use exactly this structure:

[
  {{
    "panel_number": 1,
    "narration": "Narration for panel 1",
    "dialogue": "Dialogue for panel 1"
  }},
  {{
    "panel_number": 2,
    "narration": "Narration for panel 2",
    "dialogue": "Dialogue for panel 2"
  }},
  {{
    "panel_number": 3,
    "narration": "Narration for panel 3",
    "dialogue": "Dialogue for panel 3"
  }},
  {{
    "panel_number": 4,
    "narration": "Narration for panel 4",
    "dialogue": "Dialogue for panel 4"
  }},
  {{
    "panel_number": 5,
    "narration": "Narration for panel 5",
    "dialogue": "Dialogue for panel 5"
  }}
]
"""


    # ==================================================
    # CALL GEMINI WITH RETRY
    # ==================================================

    response = None

    for attempt in range(3):

        try:

            print(
                f"Generating comic story... "
                f"Attempt {attempt + 1}/3"
            )

            response = client.models.generate_content(
                model=STORY_MODEL,
                contents=prompt
            )

            break

        except Exception as e:

            print(
                f"Gemini story request failed: {e}"
            )

            if attempt == 2:

                raise RuntimeError(
                    "Gemini story generation is "
                    "currently unavailable after "
                    "3 attempts.\n\n"
                    f"Original error:\n{e}"
                )

            print(
                "Gemini may be temporarily busy. "
                "Retrying in 5 seconds..."
            )

            time.sleep(5)


    # ==================================================
    # CHECK RESPONSE
    # ==================================================

    if response is None:

        raise RuntimeError(
            "Gemini did not return a story response."
        )


    # ==================================================
    # GET RESPONSE TEXT
    # ==================================================

    raw_text = response.text


    if not raw_text:

        raise ValueError(
            "Gemini returned an empty story response."
        )


    # ==================================================
    # CLEAN JSON
    # ==================================================

    cleaned = clean_json_response(
        raw_text
    )


    # ==================================================
    # CONVERT JSON TO PYTHON
    # ==================================================

    try:

        story = json.loads(
            cleaned
        )

    except json.JSONDecodeError as e:

        raise ValueError(
            "Gemini returned invalid story JSON.\n\n"
            f"JSON error:\n{e}\n\n"
            f"Gemini response:\n{raw_text}"
        )


    # ==================================================
    # CHECK RESPONSE TYPE
    # ==================================================

    if not isinstance(
        story,
        list
    ):

        raise ValueError(
            "Gemini story response is not a list."
        )


    # ==================================================
    # CHECK PANEL COUNT
    # ==================================================

    if len(story) != 5:

        raise ValueError(
            "Expected 5 story panels but received "
            f"{len(story)}."
        )


    # ==================================================
    # CHECK REQUIRED FIELDS
    # ==================================================

    required_fields = [
        "panel_number",
        "narration",
        "dialogue"
    ]


    for index, panel in enumerate(story):

        if not isinstance(
            panel,
            dict
        ):

            raise ValueError(
                f"Story panel {index + 1} "
                "is not valid."
            )


        for field in required_fields:

            if field not in panel:

                raise ValueError(
                    f"Story panel {index + 1} "
                    f"is missing the field: {field}"
                )


    # ==================================================
    # SUCCESS
    # ==================================================

    print(
        "Comic story generated successfully!"
    )


    # ==================================================
    # RETURN STORY
    # ==================================================

    return story