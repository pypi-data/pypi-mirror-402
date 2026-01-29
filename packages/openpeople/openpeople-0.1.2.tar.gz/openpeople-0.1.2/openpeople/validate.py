"""
Validation utilities for OpenPeople datasets.
"""

import hashlib
import json
import os
from dataclasses import dataclass, field
from typing import Optional

from openpeople.io import get_curated_dir, list_person_dirs


# Required asset keys for curated people
REQUIRED_ASSET_KEYS = [
    "character_sheet",
    "emotions_sheet",
    "studio_selfie",
    "studio_posture",
    "amateur_selfie",
    "amateur_posture",
]


@dataclass
class ValidationResult:
    """Result of a validation check."""

    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    def __bool__(self) -> bool:
        return self.valid


def compute_sha256(filepath: str) -> str:
    """Compute SHA256 hash of a file."""
    sha256_hash = hashlib.sha256()
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(8192), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def validate_person(person_dir: str, check_sha256: bool = True) -> ValidationResult:
    """
    Validate a single person directory.

    Args:
        person_dir: Path to the person directory.
        check_sha256: Whether to verify file checksums.

    Returns:
        ValidationResult with errors and warnings.
    """
    errors = []
    warnings = []
    person_id = os.path.basename(person_dir)

    # Check metadata.json exists and is valid
    metadata_path = os.path.join(person_dir, "metadata.json")
    if not os.path.exists(metadata_path):
        errors.append(f"{person_id}: missing metadata.json")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    try:
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
    except json.JSONDecodeError as e:
        errors.append(f"{person_id}: invalid metadata.json - {e}")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    # Check required metadata fields
    required_fields = [
        "person_id",
        "version",
        "character_details",
    ]
    for field_name in required_fields:
        if field_name not in metadata:
            errors.append(
                f"{person_id}: metadata missing required field '{field_name}'"
            )

    # Check required character_details fields
    if "character_details" in metadata:
        character_details = metadata["character_details"]
        required_character_fields = ["demographics", "visible_traits"]
        for field_name in required_character_fields:
            if field_name not in character_details:
                errors.append(
                    f"{person_id}: character_details missing required field '{field_name}'"
                )

    # Check prompts.json
    prompts_path = os.path.join(person_dir, "prompts.json")
    if not os.path.exists(prompts_path):
        warnings.append(f"{person_id}: missing prompts.json")
    else:
        try:
            with open(prompts_path, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{person_id}: invalid prompts.json - {e}")

    # Check provenance.json
    provenance_path = os.path.join(person_dir, "provenance.json")
    if not os.path.exists(provenance_path):
        warnings.append(f"{person_id}: missing provenance.json")
    else:
        try:
            with open(provenance_path, "r", encoding="utf-8") as f:
                json.load(f)
        except json.JSONDecodeError as e:
            errors.append(f"{person_id}: invalid provenance.json - {e}")

    # Check assets directory
    assets_dir = os.path.join(person_dir, "assets")
    if not os.path.exists(assets_dir):
        errors.append(f"{person_id}: missing assets directory")

    # Check required asset files exist in assets directory
    if os.path.exists(assets_dir):
        existing_files = set(os.listdir(assets_dir))
        if len(existing_files) == 0:
            warnings.append(f"{person_id}: assets directory is empty")

    # Check asset keys if assets field exists in metadata
    if "assets" in metadata:
        asset_keys = {asset["key"] for asset in metadata["assets"]}
        for required_key in REQUIRED_ASSET_KEYS:
            if required_key not in asset_keys:
                errors.append(f"{person_id}: missing required asset '{required_key}'")

        # Validate each asset
        for asset in metadata["assets"]:
            asset_path = os.path.join(assets_dir, asset["filename"])
            if not os.path.exists(asset_path):
                errors.append(f"{person_id}: asset file missing: {asset['filename']}")
            elif check_sha256 and "sha256" in asset:
                actual_sha256 = compute_sha256(asset_path)
                if actual_sha256 != asset["sha256"]:
                    errors.append(
                        f"{person_id}: sha256 mismatch for {asset['filename']} "
                        f"(expected {asset['sha256'][:16]}..., got {actual_sha256[:16]}...)"
                    )

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)


def curated(check_sha256: bool = True, min_count: int = 1) -> ValidationResult:
    """
    Validate the entire curated dataset.

    Args:
        check_sha256: Whether to verify file checksums.
        min_count: Minimum number of people expected (default 1).

    Returns:
        ValidationResult with all errors and warnings.
    """
    errors = []
    warnings = []

    curated_dir = get_curated_dir()
    if not os.path.exists(curated_dir):
        errors.append(f"Curated directory not found: {curated_dir}")
        return ValidationResult(valid=False, errors=errors, warnings=warnings)

    person_dirs = list_person_dirs(curated_dir)
    if len(person_dirs) < min_count:
        errors.append(f"Expected at least {min_count} people, found {len(person_dirs)}")

    for person_dir in person_dirs:
        result = validate_person(person_dir, check_sha256=check_sha256)
        errors.extend(result.errors)
        warnings.extend(result.warnings)

    return ValidationResult(valid=len(errors) == 0, errors=errors, warnings=warnings)
