"""Prompt templates for the multi-view camera positioning task."""

import random
from typing import Optional

# View name mapping for human-friendly prompts
VIEW_NAME_MAP = {
    "front": "front",
    "left": "left side",
    "right": "right side",
    "back": "back",
    "front_left": "front-left diagonal",
    "front_right": "front-right diagonal",
    "back_left": "back-left diagonal",
    "back_right": "back-right diagonal",
    "top_down": "top-down",
}

DEFAULT_RUBIK_INFO = (
    "Primary object is a Rubik's cube at the origin, aligned with the world axes and "
    "face colors set to (+X red, -X orange, +Y green, -Y blue, +Z black, -Z yellow)."
)

DEFAULT_ORIENTATION_INFO = (
    "All objects keep their default upright orientation, aligned to the world axes, "
    "with centers lying on the XY plane (z=0)."
)

PROMPTS = {
    "default": [
        "{rubik_info} {orientation_info} Additional objects: {object_summary}. "
        "The camera is currently viewing the scene from the {initial_view} perspective. "
        "Move the camera to the {target_view} view and render the scene from that new angle.",
        "Start with this setup — {rubik_info} {orientation_info} Auxiliary objects present: {object_summary}. "
        "Reposition the camera from {initial_view} to {target_view} perspective. "
        "Show the scene as it appears from the target viewpoint.",
        "Scene setup: {rubik_info} {orientation_info} Extra objects in the scene: {object_summary}. "
        "Change the viewing angle from {initial_view} to {target_view}. "
        "Generate the scene rendered from the new camera position.",
    ],
    "explicit_direction": [
        "Scene setup: {rubik_info} {orientation_info} Auxiliary objects: {object_summary}. "
        "Rotate the camera {direction} to reach the {target_view} view. The current view is {initial_view}.",
        "Keep the scene layout in mind — {rubik_info} {orientation_info} Additional objects: {object_summary}. "
        "Move the camera {direction} until it reaches the {target_view} perspective.",
    ],
    "with_object_count": [
        "The scene contains {num_objects} object(s). {rubik_info} {orientation_info} Auxiliary objects: {object_summary}. "
        "Move the camera from {initial_view} to {target_view} to view them from the new angle.",
        "There are {num_objects} object(s) in the scene. {rubik_info} {orientation_info} Additional objects: {object_summary}. "
        "Rotate the camera from {initial_view} to {target_view} to see them from a different perspective.",
    ],
    "top_down_special": [
        "{rubik_info} {orientation_info} Additional objects: {object_summary}. "
        "Switch to a top-down (bird's-eye) view of the scene. The current view is {initial_view}.",
        "With the scene arranged as follows — {rubik_info} {orientation_info} Auxiliary objects: {object_summary} — "
        "position the camera directly above the scene to show the top-down perspective.",
        "{rubik_info} {orientation_info} Extra objects: {object_summary}. Move to a top-down view to see the scene from above.",
    ],
    "back_view_special": [
        "{rubik_info} {orientation_info} Additional objects: {object_summary}. "
        "Rotate the camera to view the scene from behind. The current view is {initial_view}.",
        "Scene layout — {rubik_info} {orientation_info} Auxiliary objects: {object_summary}. "
        "Move to the back view to see the reverse side of the objects.",
    ],
}


def get_prompt(
    initial_view: str,
    target_view: str,
    num_objects: int = 1,
    object_summary: Optional[str] = None,
    rubik_info: Optional[str] = None,
    orientation_info: Optional[str] = None,
    **kwargs,
) -> str:
    """Get a formatted prompt based on view selection, object count, and scene details."""
    if target_view == "top_down":
        prompt_type = "top_down_special"
    elif target_view == "back":
        prompt_type = "back_view_special"
    elif num_objects > 1:
        prompt_type = "with_object_count"
    else:
        prompt_type = "default"

    prompts = PROMPTS.get(prompt_type, PROMPTS["default"])
    template = random.choice(prompts)

    initial_view_name = VIEW_NAME_MAP.get(initial_view, initial_view)
    target_view_name = VIEW_NAME_MAP.get(target_view, target_view)

    rubik_info_text = rubik_info or DEFAULT_RUBIK_INFO
    orientation_info_text = orientation_info or DEFAULT_ORIENTATION_INFO
    object_summary_text = object_summary.strip() if object_summary else "none"

    kwargs = {
        key: value
        for key, value in kwargs.items()
        if key not in {"rubik_info", "object_summary", "orientation_info"}
    }

    try:
        return template.format(
            initial_view=initial_view_name,
            target_view=target_view_name,
            num_objects=num_objects,
            object_summary=object_summary_text,
            rubik_info=rubik_info_text,
            orientation_info=orientation_info_text,
            **kwargs,
        )
    except KeyError:
        return template
