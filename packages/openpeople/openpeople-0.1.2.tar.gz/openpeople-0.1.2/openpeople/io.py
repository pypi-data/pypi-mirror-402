"""
I/O helpers for loading OpenPeople data.
"""

import json
import os
from typing import Optional

from openpeople.types import (
    Person,
    PersonMetadata,
    Prompt,
)


def load_person(person_dir: str) -> Person:
    """
    Load a Person from a directory containing metadata and prompts.

    Args:
        person_dir: Path to the person's data directory.

    Returns:
        Fully loaded Person object.

    Raises:
        FileNotFoundError: If required files are missing.
        ValueError: If JSON parsing or validation fails.
    """
    # Load metadata
    metadata_path = os.path.join(person_dir, "metadata.json")
    with open(metadata_path, "r", encoding="utf-8") as f:
        metadata_dict = json.load(f)

    metadata = PersonMetadata.model_validate(metadata_dict)
    person = Person(metadata, person_dir)

    # Load prompts
    prompts_path = os.path.join(person_dir, "prompts.json")
    if os.path.exists(prompts_path):
        with open(prompts_path, "r", encoding="utf-8") as f:
            prompts_dict = json.load(f)
        for key, prompt_data in prompts_dict.items():
            person._prompts[key] = Prompt.model_validate(prompt_data)

    return person


def get_data_dir() -> str:
    """Get the path to the package data directory."""
    # Use importlib.resources for proper package resource handling
    try:
        from importlib.resources import files

        return str(files("openpeople") / "data")
    except (ImportError, TypeError):
        # Fallback for older Python or development mode
        return os.path.join(os.path.dirname(__file__), "data")


def get_curated_dir() -> str:
    """Get the path to the curated data directory."""
    return os.path.join(get_data_dir(), "curated")


def list_person_dirs(base_dir: str) -> list[str]:
    """
    List all person directories in a base directory.

    Args:
        base_dir: Path to search for person directories.

    Returns:
        Sorted list of full paths to person directories.
    """
    if not os.path.exists(base_dir):
        return []

    dirs = []
    for name in os.listdir(base_dir):
        path = os.path.join(base_dir, name)
        if os.path.isdir(path) and name.startswith("P"):
            # Check for metadata.json to confirm it's a valid person dir
            if os.path.exists(os.path.join(path, "metadata.json")):
                dirs.append(path)

    return sorted(dirs)
