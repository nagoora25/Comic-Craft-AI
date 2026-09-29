from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent


def build_comic_layout(
    outline,
    story,
    images
):
    """
    Combine the comic outline, story and generated images
    into a simple panel-by-panel layout.
    """

    layout = []

    for index, panel in enumerate(outline):

        story_panel = {}

        if index < len(story):
            story_panel = story[index]

        image_path = ""

        if index < len(images):
            image_path = images[index]

        panel_data = {
            "panel_number": panel.get(
                "panel_number",
                index + 1
            ),

            "title": panel.get(
                "title",
                f"Panel {index + 1}"
            ),

            "scene_description": panel.get(
                "scene_description",
                ""
            ),

            "image_prompt": panel.get(
                "image_prompt",
                ""
            ),

            "image_path": image_path,

            "narration": story_panel.get(
                "narration",
                ""
            ),

            "dialogue": story_panel.get(
                "dialogue",
                ""
            )
        }

        layout.append(panel_data)

    return layout