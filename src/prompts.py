"""Prompt helpers for the default G-29 chart task."""

import random
from typing import Any, Dict, List, Optional


PROMPTS = {
    "pie_max": [
        "Highlight the largest segment in this pie chart.",
        "Find the maximum slice and draw a red rectangular border around it.",
    ],
    "pie_min": [
        "Highlight the smallest segment in this pie chart.",
        "Find the minimum slice and draw a red rectangular border around it.",
    ],
    "bar_max": [
        "Highlight the tallest bar in this chart.",
        "Find the maximum bar and draw a red rectangular border around it.",
    ],
    "bar_min": [
        "Highlight the shortest bar in this chart.",
        "Find the minimum bar and draw a red rectangular border around it.",
    ],
    "line_max": [
        "Highlight the highest point in this line chart.",
        "Find the maximum point and draw a red rectangular border around it.",
    ],
    "line_min": [
        "Highlight the lowest point in this line chart.",
        "Find the minimum point and draw a red rectangular border around it.",
    ],
    "scatter_max": [
        "Highlight the highest point in this scatter chart.",
        "Find the maximum point and draw a red rectangular border around it.",
    ],
    "scatter_min": [
        "Highlight the lowest point in this scatter chart.",
        "Find the minimum point and draw a red rectangular border around it.",
    ],
}


def _meta_value(metadata: Optional[Dict[str, Any]], key: str) -> Optional[str]:
    if not metadata:
        return None
    value = metadata.get(key)
    if value is None:
        return None
    return str(value).strip() or None


def get_prompt(
    chart_type: str = "bar",
    extreme_type: str = "max",
    metadata: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a contextual prompt for the chart-extreme task."""

    title = _meta_value(metadata, "title")
    x_label = _meta_value(metadata, "x_label")
    y_label = _meta_value(metadata, "y_label")

    chart_names = {
        "pie": "pie chart",
        "bar": "bar chart",
        "line": "line chart",
        "scatter": "scatter chart",
    }
    chart_name = chart_names.get(chart_type, "chart")

    if title:
        if x_label and y_label:
            scene = (
                f"The scene shows a {chart_name} titled '{title}' with "
                f"{x_label} on the x-axis and {y_label} on the y-axis."
            )
        elif y_label:
            scene = f"The scene shows a {chart_name} titled '{title}' with {y_label} on the y-axis."
        else:
            scene = f"The scene shows a {chart_name} titled '{title}'."

        if chart_type == "pie":
            target = "largest" if extreme_type == "max" else "smallest"
            return (
                f"{scene} Find the category with the {target} share and draw a red "
                "rectangular border around the corresponding segment to highlight it."
            )

        metric = (y_label or "value").lower()
        if chart_type == "bar":
            qualifier = "highest" if extreme_type == "max" else "lowest"
            target_name = (x_label or "item").lower()
            return (
                f"{scene} Find the {target_name} with the {qualifier} {metric} and draw "
                "a red rectangular border around the corresponding bar to highlight it."
            )

        qualifier = "highest" if extreme_type == "max" else "lowest"
        return (
            f"{scene} Find the point with the {qualifier} {metric} and draw a red "
            "rectangular border around the corresponding point to highlight it."
        )

    key = f"{chart_type}_{extreme_type}"
    return random.choice(PROMPTS.get(key, PROMPTS["bar_max"]))


def get_all_prompts(chart_type: str = "bar", extreme_type: str = "max") -> List[str]:
    """Return all static fallback prompts for a chart/extreme pair."""

    return PROMPTS.get(f"{chart_type}_{extreme_type}", PROMPTS["bar_max"])
