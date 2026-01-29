# OpenPeople

**Dataset of synthetic people for testing generative image/video pipelines at scale.**

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.9+](https://img.shields.io/badge/python-3.9+-blue.svg)](https://www.python.org/downloads/)



## What is OpenPeople?

OpenPeople provides a curated set of **synthetic "people"** designed for testing generative image and video pipelines. All people in this library are entirely synthetic. They do not represent real individuals (any similarity is purely coincidental).

### Why use synthetic people?

- **Safe testing**: Test your pipelines without using real people's images
- **Consistent subjects**: Stable, reproducible characters across runs
- **Prompt provenance**: Every image includes the prompts used to generate it
- **Diversity by design**: Curated dataset covers various demographics


## How was this dataset created?

Each synthetic person is generated through a **multi-stage pipeline** that ensures visual consistency across all assets.

### 1. Character Definition

Each person starts with a structured `metadata.json` defining their characteristics. These are **randomly generated** to ensure diversity:

**Demographics** are randomized across:
- **Age ranges**: `18-25`, `25-35`, `35-45`, `45-55`, `55-65`, `65+`
- **Sex**: `male`, `female`
- **Ethnicity**: Mixed heritage with weighted percentages (e.g., `"14% Western Asian, 50% European, 36% African"`)
- **Skin tone**: Fitzpatrick scale I–VI

**Visible traits** include randomized:
- **Hair**: texture, length, color, style (e.g., `"Very long, thick, naturally wavy curls"`)
- **Body type**: `slim`, `athletic`, `average`, `curvy`, `large`
- **Height**: `short`, `average`, `tall`

**Additional traits** add unique details like jawline, eyebrows, hairline, and other distinguishing features.

```json
{
  "person_id": "P050",
  "character_details": {
    "demographics": {
      "age_range": "18-25",
      "sex": "male",
      "ethnicity": "14% Western Asian, 50% European, 36% African",
      "skin_tone": "Fitzpatrick III"
    },
    "visible_traits": {
      "hair": { "description": "Very long, thick, naturally wavy curls cascading over the shoulders." },
      "body_type": "large",
      "height": "average"
    },
    "additional_traits": {
      "hairline": "Center-parted hair with a neat hairline",
      "hands": "Long, slender fingers resting gently on the chin."
    }
  }
}
```

### 2. Multi-Stage Image Generation

Images are generated in a specific order, where each stage uses previous outputs as reference to maintain identity consistency:

```
┌─────────────────┐
│ Character JSON  │
└────────┬────────┘
         ▼
┌─────────────────┐
│    Preview      │  Temp full-body preview
└────────┬────────┘
         ▼
┌─────────────────┐
│ Studio Portrait │  Professional headshot
└────────┬────────┘
         ▼
┌─────────────────┐
│ Studio Posture  │──────────────┐  Full-body studio shot
└────────┬────────┘              |
         ▼                       ▼
┌─────────────────┐     ┌─────────────────┐
│ Character Sheet │     │ Emotions Sheet  │  Reference sheets
└────────┬────────┘     └────────┬────────┘
         │                       │
         └───────────┬───────────┘
                     ▼
         ┌─────────────────────┐
         │   Amateur Photos    │  Casual photos
         └─────────────────────┘
```

### 3. Reference Chaining

The key to consistency is **reference chaining** — each generation stage receives images from previous stages:

- **Studio Portrait**: Uses the preview image to establish facial features
- **Studio Posture**: Uses the portrait to maintain face consistency in full-body shot  
- **Character Sheet**: Combines portrait + posture with a layout template
- **Emotions Sheet**: Uses portrait with an emotions grid template
- **Amateur Photos**: Use the character/emotions sheets as reference for varied contexts

### 4. Generation Model

All images in the curated dataset are generated using **Gemini 3 Pro** image generation with carefully crafted prompts for each asset type. The prompts emphasize analytical photography, visible imperfections, and consistent styling.


## Installation

```bash
pip install openpeople
```


## Quick Start

```python
import openpeople

# List all curated people
people = openpeople.curated.list()
print(f"Found {len(people)} synthetic people")

# Get a specific person
person = openpeople.curated.get("P001")

# Get a random person (non-deterministic)
random_person = openpeople.curated.random()

# Get a random person (deterministic with seed)
seeded_person = openpeople.curated.random(seed=42)

# Sample multiple people without replacement
sample = openpeople.curated.sample(n=3, seed=1234)
```



## Working with Assets

Each person comes with multiple image assets:

| Asset Key | Description |
|-----------|-------------|
| `character_sheet` | Full-body multi-angle reference sheet |
| `emotions_sheet` | Facial expressions grid |
| `studio_selfie` | Portrait in studio setting |
| `studio_posture` | Full body in studio setting |
| `amateur_selfie` | Portrait in casual setting |
| `amateur_posture` | Full body in casual setting |

```python
person = openpeople.curated.get("P001")

# Get path to an asset
path = person.asset_path("studio_selfie")
print(path)

# Load image directly (requires openpeople[images])
image = person.load_image("studio_selfie")
image.show()
```

## ⚠️ Disclaimer

> **Please verify on your own before usage.**
>
> These synthetic people are provided for testing and development purposes only. OpenPeople contains:
> - No names or personal identifiers
> - No real individuals
> - No data suitable for identification purposes
>
> Users are responsible for ensuring their use complies with applicable laws and ethical guidelines.


## License

MIT License - see [LICENSE](LICENSE) for details.


## Contributing

Contributions are welcome! Please ensure:

1. All synthetic people remain entirely fictional
2. No names or real-person references
3. Used prompts must be documented
4. Tests pass before submitting PRs

---

*Built with 💜 by [Prompt Haus](https://github.com/Prompt-Haus)*
