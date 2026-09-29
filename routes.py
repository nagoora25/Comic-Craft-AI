from pathlib import Path
import traceback

from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from app.ai.gemini_flash import generate_outline
from app.gemini_pro import generate_story
from app.image_generator import generate_image
from app.layout_builder import build_comic_layout
from app.exporters import save_pdf


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

TEMPLATES_DIR = BASE_DIR / "templates"

templates = Jinja2Templates(
    directory=str(TEMPLATES_DIR)
)

router = APIRouter()


# ============================================================
# FALLBACK OUTLINE
# ============================================================

def create_fallback_outline(
    story_prompt,
    character_name,
    setting,
    tone,
    art_style
):
    """
    Creates a 5-panel fox comic outline when
    Gemini is unavailable.
    """

    character = character_name or "Fox"

    return [
        {
            "panel_number": 1,
            "title": "Entering the Enchanted Forest",

            "scene_description": (
                f"A brave {character} enters a mysterious "
                "enchanted forest filled with glowing trees, "
                "magical flowers and soft mist."
            ),

            "image_prompt": (
                f"A brave red fox entering an enchanted forest, "
                "glowing magical trees, colorful flowers, soft "
                "mist, fantasy environment, cinematic composition, "
                "detailed comic book scene"
            )
        },

        {
            "panel_number": 2,
            "title": "The Mysterious Path",

            "scene_description": (
                f"The {character} discovers a mysterious glowing "
                "path and follows it deeper into the forest."
            ),

            "image_prompt": (
                f"A brave red fox walking along a glowing magical "
                "path deep inside an enchanted forest, glowing "
                "flowers, ancient trees, mysterious shadows, "
                "fantasy atmosphere, detailed comic book scene"
            )
        },

        {
            "panel_number": 3,
            "title": "The Magical Creature",

            "scene_description": (
                f"Behind the ancient trees, the {character} "
                "discovers a mysterious magical creature."
            ),

            "image_prompt": (
                f"A brave red fox discovering a friendly magical "
                "creature behind ancient trees in an enchanted "
                "forest, glowing magic, fantasy environment, "
                "cinematic lighting, detailed comic book scene"
            )
        },

        {
            "panel_number": 4,
            "title": "The Hidden Crystal",

            "scene_description": (
                f"The {character} discovers an ancient glowing "
                "crystal that protects the entire enchanted forest."
            ),

            "image_prompt": (
                f"A brave red fox discovering a glowing ancient "
                "crystal inside an enchanted forest, magical energy "
                "surrounding the crystal, ancient trees, dramatic "
                "fantasy lighting, detailed comic book scene"
            )
        },

        {
            "panel_number": 5,
            "title": "The New Guardian",

            "scene_description": (
                f"After the adventure, the {character} becomes "
                "the guardian of the magical forest."
            ),

            "image_prompt": (
                f"A brave red fox standing proudly as guardian "
                "of an enchanted forest, beautiful sunrise, "
                "glowing trees, peaceful magical atmosphere, "
                "heroic ending, detailed comic book scene"
            )
        }
    ]


# ============================================================
# FALLBACK STORY
# ============================================================

def create_fallback_story():

    return [
        {
            "panel_number": 1,

            "narration": (
                "A brave fox stepped into the enchanted forest, "
                "ready to discover its mysterious secrets."
            ),

            "dialogue": (
                "Fox: I wonder what mysteries are hidden here."
            )
        },

        {
            "panel_number": 2,

            "narration": (
                "The fox followed a glowing path that led "
                "deeper into the magical forest."
            ),

            "dialogue": (
                "Fox: This mysterious path must be leading somewhere."
            )
        },

        {
            "panel_number": 3,

            "narration": (
                "Behind the ancient trees, the fox discovered "
                "a strange but friendly magical creature."
            ),

            "dialogue": (
                "Creature: You have entered a very special place."
            )
        },

        {
            "panel_number": 4,

            "narration": (
                "Together they discovered an ancient crystal "
                "that protected the entire forest."
            ),

            "dialogue": (
                "Fox: I will make sure this magical crystal is protected."
            )
        },

        {
            "panel_number": 5,

            "narration": (
                "The fox returned from the adventure with a new "
                "purpose and became the guardian of the forest."
            ),

            "dialogue": (
                "Fox: Every great adventure brings a new responsibility."
            )
        }
    ]


# ============================================================
# GENERATION PIPELINE
# ============================================================

def run_generation(
    story_prompt: str,
    character_name: str,
    setting: str,
    tone: str,
    art_style: str
):

    print()
    print("=" * 60)
    print("COMICCRAFT GENERATION STARTED")
    print("=" * 60)

    fallback_used = False

    # ========================================================
    # STEP 1 - GEMINI OUTLINE
    # ========================================================

    print()
    print("[1/5] Generating comic outline...")

    try:

        outline = generate_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        print(
            "Gemini outline generated successfully!"
        )

    except Exception as exc:

        print()
        print("Gemini outline generation failed.")

        print(
            "ERROR TYPE:",
            type(exc).__name__
        )

        print(
            "ERROR MESSAGE:",
            str(exc)
        )

        print()
        print(
            "Using ComicCraft fallback outline..."
        )

        outline = create_fallback_outline(
            story_prompt=story_prompt,
            character_name=character_name,
            setting=setting,
            tone=tone,
            art_style=art_style
        )

        fallback_used = True

        print(
            "Fallback outline created successfully!"
        )

    print(
        "Number of panels:",
        len(outline)
    )


    # ========================================================
    # STEP 2 - STORY
    # ========================================================

    print()
    print("[2/5] Generating comic story...")

    if fallback_used:

        story = create_fallback_story()

        print(
            "Fallback story created successfully!"
        )

    else:

        try:

            story = generate_story(
                outline=outline,
                character_name=character_name,
                tone=tone
            )

            print(
                "Gemini story generated successfully!"
            )

        except Exception as exc:

            print()
            print(
                "Gemini story generation failed."
            )

            print(
                "ERROR TYPE:",
                type(exc).__name__
            )

            print(
                "ERROR MESSAGE:",
                str(exc)
            )

            print()
            print(
                "Switching to fallback story..."
            )

            story = create_fallback_story()

            fallback_used = True

            print(
                "Fallback story created successfully!"
            )


    # ========================================================
    # STEP 3 - IMAGE GENERATION
    # ========================================================

    print()
    print("[3/5] Generating AI images...")

    images = []

    for index, panel in enumerate(outline):

        panel_number = index + 1

        print()
        print(
            f"Generating AI image for Panel {panel_number}..."
        )

        image_prompt = panel.get(
            "image_prompt",
            panel.get(
                "scene_description",
                ""
            )
        )

        try:

            image_path = generate_image(
                image_prompt=image_prompt,
                art_style=art_style
            )

            images.append(
                image_path
            )

            print(
                f"Panel {panel_number} image generated successfully!"
            )

            print(
                "Image:",
                image_path
            )

        except Exception as exc:

            print()
            print(
                f"Image generation failed for Panel {panel_number}."
            )

            print(
                "ERROR TYPE:",
                type(exc).__name__
            )

            print(
                "ERROR MESSAGE:",
                str(exc)
            )

            raise RuntimeError(
                f"AI image generation failed "
                f"for Panel {panel_number}: {exc}"
            )


    print()
    print(
        "All AI images generated successfully!"
    )


    # ========================================================
    # STEP 4 - BUILD COMIC LAYOUT
    # ========================================================

    print()
    print("[4/5] Building comic layout...")

    layout = build_comic_layout(
        outline=outline,
        story=story,
        images=images
    )

    print(
        "Comic layout created successfully!"
    )


    # ========================================================
    # STEP 5 - CREATE PDF
    # ========================================================

    print()
    print("[5/5] Creating PDF...")

    pdf_path = save_pdf(
        layout
    )

    print(
        "PDF created successfully!"
    )

    print(
        "PDF path:",
        pdf_path
    )


    # ========================================================
    # FINAL MESSAGE
    # ========================================================

    print()
    print("=" * 60)

    if fallback_used:

        print(
            "COMIC GENERATED USING FALLBACK MODE"
        )

    else:

        print(
            "COMIC GENERATED USING GEMINI"
        )

    print("=" * 60)

    return (
        layout,
        pdf_path,
        fallback_used
    )


# ============================================================
# HOME PAGE
# ============================================================

@router.get(
    "/",
    response_class=HTMLResponse
)
async def home(request: Request):

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={}
    )


# ============================================================
# GENERATE COMIC
# ============================================================

@router.post(
    "/generate",
    response_class=HTMLResponse
)
async def generate_comic(
    request: Request,

    story_prompt: str = Form(...),

    character_name: str = Form(...),

    setting: str = Form(...),

    tone: str = Form(...),

    art_style: str = Form(...)
):

    print()
    print("=" * 60)
    print("POST /generate RECEIVED")
    print("=" * 60)

    print(
        "Story prompt:",
        story_prompt
    )

    print(
        "Character:",
        character_name
    )

    print(
        "Setting:",
        setting
    )

    print(
        "Tone:",
        tone
    )

    print(
        "Art style:",
        art_style
    )

    try:

        layout, pdf_path, fallback_used = run_generation(

            story_prompt=story_prompt,

            character_name=character_name,

            setting=setting,

            tone=tone,

            art_style=art_style

        )

        return templates.TemplateResponse(
            request=request,
            name="comic_preview.html",
            context={
                "layout": layout,
                "pdf_path": pdf_path,
                "fallback_used": fallback_used
            }
        )

    except Exception as exc:

        print()
        print("!" * 60)
        print("COMIC GENERATION FAILED")
        print("!" * 60)

        print(
            "ERROR TYPE:",
            type(exc).__name__
        )

        print(
            "ERROR MESSAGE:",
            str(exc)
        )

        print()
        print(
            "FULL TRACEBACK:"
        )

        traceback.print_exc()

        print(
            "!" * 60
        )

        return HTMLResponse(

            content=f"""
<!DOCTYPE html>

<html>

<head>

    <title>ComicCraft Error</title>

    <style>

        body {{
            font-family: Arial, sans-serif;
            background: #fff4f4;
            padding: 40px;
        }}

        .box {{
            max-width: 850px;
            margin: auto;
            background: white;
            padding: 30px;
            border-radius: 15px;
            box-shadow:
                0 10px 30px
                rgba(0, 0, 0, 0.10);
        }}

        h1 {{
            color: #d32f2f;
        }}

        pre {{
            background: #f5f5f5;
            padding: 20px;
            border-radius: 10px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}

        a {{
            display: inline-block;
            margin-top: 20px;
            padding: 12px 20px;
            background: #6c4cff;
            color: white;
            text-decoration: none;
            border-radius: 8px;
        }}

    </style>

</head>

<body>

    <div class="box">

        <h1>
            ⚠️ ComicCraft Error
        </h1>

        <p>
            Something went wrong while
            generating the comic.
        </p>

        <pre>
{type(exc).__name__}: {str(exc)}
        </pre>

        <a href="/">
            ← Back to ComicCraft
        </a>

    </div>

</body>

</html>
            """,

            status_code=500
        )


# ============================================================
# JSON GENERATION API
# ============================================================

@router.post(
    "/generate-comic/json"
)
async def generate_comic_json(

    story_prompt: str,

    character_name: str,

    setting: str,

    tone: str,

    art_style: str

):

    try:

        layout, pdf_path, fallback_used = run_generation(

            story_prompt=story_prompt,

            character_name=character_name,

            setting=setting,

            tone=tone,

            art_style=art_style

        )

        return {

            "success": True,

            "fallback_used": fallback_used,

            "layout": layout,

            "pdf_path": pdf_path

        }

    except Exception as exc:

        print()
        print(
            "JSON GENERATION ERROR:"
        )

        traceback.print_exc()

        return JSONResponse(

            status_code=500,

            content={

                "success": False,

                "error": type(exc).__name__,

                "message": str(exc)

            }

        )


# ============================================================
# TEST IMAGE
# ============================================================

@router.get(
    "/test-image",
    response_class=HTMLResponse
)
async def test_image():

    try:

        image_path = generate_image(

            image_prompt=(
                "A brave red fox exploring "
                "an enchanted forest, glowing "
                "trees, magical flowers, "
                "beautiful fantasy environment"
            ),

            art_style="comic book"

        )

        return HTMLResponse(

            content=f"""
<!DOCTYPE html>

<html>

<head>

    <title>
        ComicCraft - AI Image Test
    </title>

</head>

<body
    style="
        font-family: Arial;
        text-align: center;
        padding: 40px;
    "
>

    <h1>
        🎨 AI Image Test
    </h1>

    <img
        src="{image_path}"
        alt="AI Generated Fox"
        style="
            max-width: 600px;
            width: 90%;
            border-radius: 15px;
            box-shadow:
                0 10px 30px
                rgba(0,0,0,0.15);
        "
    >

    <h2>
        AI image generated successfully!
    </h2>

    <p>
        ComicCraft Hugging Face image generation
        is working correctly.
    </p>

    <br>

    <a href="/">
        ← Back to ComicCraft
    </a>

</body>

</html>
            """

        )

    except Exception as exc:

        print()
        print(
            "IMAGE TEST ERROR:"
        )

        traceback.print_exc()

        return HTMLResponse(

            content=f"""
<h1>
    Image Generation Failed
</h1>

<pre>
{type(exc).__name__}: {str(exc)}
</pre>

<a href="/">
    ← Back to ComicCraft
</a>
            """,

            status_code=500

        )


# ============================================================
# EXPORT SUCCESS
# ============================================================

@router.get(
    "/export-success",
    response_class=HTMLResponse
)
async def export_success(
    request: Request
):

    return templates.TemplateResponse(

        request=request,

        name="export_success.html",

        context={}

    )