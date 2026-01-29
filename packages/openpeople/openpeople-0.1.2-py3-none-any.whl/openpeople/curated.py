"""
Curated synthetic people dataset.

This module provides access to a small, curated set of synthetic people
designed for testing generative image/video pipelines.
"""

from __future__ import annotations

import random as _random
from typing import Optional, List

from openpeople.types import Person
from openpeople.io import get_curated_dir, list_person_dirs, load_person


# Cache for loaded persons
_cache: dict[str, Person] = {}
_all_loaded: bool = False


def _load_all() -> None:
    """Load all curated persons into cache."""
    global _all_loaded
    if _all_loaded:
        return

    curated_dir = get_curated_dir()
    for person_dir in list_person_dirs(curated_dir):
        person = load_person(person_dir)
        _cache[person.person_id] = person

    _all_loaded = True


def list() -> List[Person]:
    """
    List all curated synthetic people.

    Returns:
        List of all Person objects in the curated dataset,
        sorted by person_id.

    Example:
        >>> people = openpeople.curated.list()
        >>> for person in people:
        ...     print(person.person_id)
    """
    _load_all()
    return sorted(_cache.values(), key=lambda p: p.person_id)


def get(person_id: str) -> Person:
    """
    Get a specific curated person by ID.

    Args:
        person_id: The unique identifier (e.g., 'P001').

    Returns:
        The Person object.

    Raises:
        KeyError: If no person with that ID exists.

    Example:
        >>> person = openpeople.curated.get('P001')
        >>> print(person.demographics.ethnicity)
    """
    _load_all()
    if person_id not in _cache:
        raise KeyError(f"No curated person with id '{person_id}'")
    return _cache[person_id]


def random(seed: Optional[int] = None) -> Person:
    """
    Get a random curated person.

    Args:
        seed: Optional random seed for deterministic selection.
              If provided, the same seed always returns the same person.

    Returns:
        A randomly selected Person object.

    Raises:
        ValueError: If no curated people are available.

    Example:
        >>> person = openpeople.curated.random()  # random each time
        >>> person = openpeople.curated.random(seed=42)  # deterministic
    """
    _load_all()
    if not _cache:
        raise ValueError("No curated people available")

    rng = _random.Random(seed)
    people = list()
    return rng.choice(people)


def sample(n: int, seed: Optional[int] = None) -> List[Person]:
    """
    Get a sample of n curated people without replacement.

    Args:
        n: Number of people to sample.
        seed: Optional random seed for deterministic selection.
              If provided, the same seed always returns the same sample
              in the same order.

    Returns:
        List of n Person objects (no duplicates).

    Raises:
        ValueError: If n is greater than the number of available people,
                   or if no curated people are available.

    Example:
        >>> people = openpeople.curated.sample(3)  # random 3
        >>> people = openpeople.curated.sample(3, seed=42)  # deterministic
    """
    _load_all()
    if not _cache:
        raise ValueError("No curated people available")

    people = list()
    if n > len(people):
        raise ValueError(f"Cannot sample {n} people; only {len(people)} available")

    rng = _random.Random(seed)
    return rng.sample(people, n)


def count() -> int:
    """
    Get the number of curated people available.

    Returns:
        Number of people in the curated dataset.
    """
    _load_all()
    return len(_cache)
