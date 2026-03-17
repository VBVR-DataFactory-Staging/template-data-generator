"""
Your task prompts.

CUSTOMIZE THIS FILE to define prompts/instructions for your task.
Prompts are selected based on task type and returned to the model.
"""

import random


# ======================================================================
#  DEFINE YOUR PROMPTS
# ======================================================================

PROMPTS = {
    "default": [
        # Add your task prompts here. Use multiple variants for diversity.
        "Describe what changes between the initial and final state.",
        "What transformation occurs from the first frame to the last frame?",
    ],
}


def get_prompt(task_type: str = "default") -> str:
    """
    Select a random prompt for the given task type.
    
    Args:
        task_type: Type of task (key in PROMPTS dict)
        
    Returns:
        Random prompt string from the specified type
    """
    prompts = PROMPTS.get(task_type, PROMPTS["default"])
    return random.choice(prompts)


def get_all_prompts(task_type: str = "default") -> list[str]:
    """Get all prompts for a given task type."""
    return PROMPTS.get(task_type, PROMPTS["default"])
