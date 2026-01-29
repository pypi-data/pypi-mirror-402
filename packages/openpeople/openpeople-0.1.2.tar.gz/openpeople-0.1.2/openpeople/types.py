"""
Pydantic models for OpenPeople schema.
"""

from typing import Optional
from pydantic import BaseModel, Field


class HairTraits(BaseModel):
    """Hair characteristics."""

    description: Optional[str] = None
    color: Optional[str] = None
    texture: Optional[str] = None
    length: Optional[str] = None
    style: Optional[str] = None


class VisibleTraits(BaseModel):
    """Visually observable traits."""

    hair: Optional[HairTraits] = None
    facial_hair: Optional[str] = None
    body_type: Optional[str] = None
    height: Optional[str] = None


class Disability(BaseModel):
    """Visible disability representation."""

    type: str
    visibility: str
    notes: Optional[str] = None


class Demographics(BaseModel):
    """Demographic attributes."""

    age_range: Optional[str] = Field(None, description="Age range, e.g., '25-35'")
    sex: Optional[str] = Field(
        None, description="One of: female, male, intersex, nonbinary, unknown"
    )
    ethnicity: Optional[str] = None
    skin_tone: Optional[str] = Field(
        None, description="Fitzpatrick scale I-VI or descriptive"
    )


class StyleContext(BaseModel):
    """Style and context information."""

    wardrobe_style: Optional[str] = None
    vibe: Optional[list[str]] = None
    environment_assumptions: Optional[list[str]] = None


class CharacterDetails(BaseModel):
    """Character details containing demographics and traits."""

    demographics: Optional[Demographics] = None
    visible_traits: Optional[VisibleTraits] = None
    additional_traits: Optional[dict] = None


class Asset(BaseModel):
    """Reference to an image asset."""

    key: str
    filename: str
    kind: str = Field(..., description="e.g., 'image/png'")
    description: str
    width: int
    height: int
    sha256: str


class Prompt(BaseModel):
    """Prompt used to generate an asset."""

    positive_prompt: str
    negative_prompt: Optional[str] = None
    system_prompt: Optional[str] = None
    notes: Optional[str] = None


class Provenance(BaseModel):
    """Generation provenance information."""

    provider: str = Field(..., description="e.g., 'openai', 'stability', 'unknown'")
    model: str
    date_generated: str = Field(..., description="ISO 8601 date string")
    settings: dict = Field(default_factory=dict, description="Generation settings")


class UniquenessEvidence(BaseModel):
    """Evidence of uniqueness for curated people."""

    constraints_summary: str
    deterministic_seed: Optional[int] = None
    notes: str


class PersonMetadata(BaseModel):
    """Full metadata for a synthetic person."""

    person_id: str
    version: str
    generated_with: Optional[str] = None
    character_details: Optional[CharacterDetails] = None
    # Legacy/optional fields
    tags: Optional[list[str]] = None
    demographics: Optional[Demographics] = None
    visible_traits: Optional[VisibleTraits] = None
    disabilities: list[Disability] = Field(default_factory=list)
    style_context: Optional[StyleContext] = None
    assets: Optional[list[Asset]] = None
    uniqueness_evidence: Optional[UniquenessEvidence] = None


class Person:
    """
    Represents a synthetic person with metadata and asset access.

    This is the main interface for working with OpenPeople data.
    """

    def __init__(self, metadata: PersonMetadata, data_dir: str):
        self._metadata = metadata
        self._data_dir = data_dir
        self._prompts: dict[str, Prompt] = {}

    @property
    def person_id(self) -> str:
        """Unique identifier for this person."""
        return self._metadata.person_id

    @property
    def metadata(self) -> dict:
        """Full metadata as a dictionary."""
        return self._metadata.model_dump()

    @property
    def demographics(self) -> Optional[Demographics]:
        """Demographic attributes."""
        # Check character_details first, then root level
        if (
            self._metadata.character_details
            and self._metadata.character_details.demographics
        ):
            return self._metadata.character_details.demographics
        return self._metadata.demographics

    @property
    def visible_traits(self) -> Optional[VisibleTraits]:
        """Visible traits."""
        # Check character_details first, then root level
        if (
            self._metadata.character_details
            and self._metadata.character_details.visible_traits
        ):
            return self._metadata.character_details.visible_traits
        return self._metadata.visible_traits

    @property
    def style_context(self) -> Optional[StyleContext]:
        """Style context."""
        return self._metadata.style_context

    @property
    def assets_dir(self) -> str:
        """Path to the assets directory."""
        import os

        return os.path.join(self._data_dir, "assets")

    def list_assets(self) -> list[str]:
        """
        List all available asset keys by scanning the assets directory.

        Returns:
            List of asset keys (filenames without extensions).
        """
        import os

        if not os.path.exists(self.assets_dir):
            return []

        asset_keys = []
        for filename in os.listdir(self.assets_dir):
            if filename.lower().endswith((".jpg", ".jpeg", ".png", ".webp")):
                # Extract key from filename (remove extension)
                key = os.path.splitext(filename)[0]
                asset_keys.append(key)

        return sorted(asset_keys)

    def asset_path(self, key: str) -> str:
        """
        Get the full path to an asset by key.

        Args:
            key: Asset key (e.g., 'studio_portrait', 'character_sheet')

        Returns:
            Full filesystem path to the asset file.

        Raises:
            KeyError: If the asset key doesn't exist.
        """
        import os

        if not os.path.exists(self.assets_dir):
            raise KeyError(
                f"No asset with key '{key}' found for person {self.person_id}"
            )

        # Look for file by key name in assets directory
        for filename in os.listdir(self.assets_dir):
            name, ext = os.path.splitext(filename)
            if name == key and ext.lower() in (".jpg", ".jpeg", ".png", ".webp"):
                return os.path.join(self.assets_dir, filename)

        raise KeyError(f"No asset with key '{key}' found for person {self.person_id}")

    def load_image(self, key: str):
        """
        Load an asset image using Pillow.

        Args:
            key: Asset key (e.g., 'studio_portrait', 'character_sheet')

        Returns:
            PIL.Image.Image object.

        Raises:
            ImportError: If Pillow is not installed.
            KeyError: If the asset key doesn't exist.
        """
        try:
            from PIL import Image
        except ImportError:
            raise ImportError(
                "Pillow is required for load_image(). "
                "Install it with: pip install openpeople[images]"
            )

        path = self.asset_path(key)
        return Image.open(path)

    def get_prompt(self, key: str) -> Optional[Prompt]:
        """Get the prompt used for a specific asset."""
        return self._prompts.get(key)

    def __repr__(self) -> str:
        return f"Person(id={self.person_id!r})"
