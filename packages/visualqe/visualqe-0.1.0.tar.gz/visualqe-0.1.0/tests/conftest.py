"""Shared pytest fixtures for VisualQE tests."""

import tempfile
from pathlib import Path
from typing import Generator

import pytest
from PIL import Image


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_image() -> Image.Image:
    """Create a simple test image."""
    img = Image.new("RGB", (100, 100), color="white")
    # Add some features
    for x in range(20, 80):
        for y in range(20, 80):
            img.putpixel((x, y), (0, 100, 200))
    return img


@pytest.fixture
def sample_image_modified() -> Image.Image:
    """Create a modified version of the test image."""
    img = Image.new("RGB", (100, 100), color="white")
    # Add features in different positions/colors
    for x in range(30, 90):
        for y in range(30, 90):
            img.putpixel((x, y), (200, 100, 0))
    return img


@pytest.fixture
def sample_image_identical(sample_image: Image.Image) -> Image.Image:
    """Create an identical copy of the test image."""
    return sample_image.copy()


@pytest.fixture
def sample_image_slightly_different(sample_image: Image.Image) -> Image.Image:
    """Create a slightly different version (anti-aliasing simulation)."""
    img = sample_image.copy()
    # Add minor differences
    for x in range(20, 22):
        for y in range(20, 80):
            r, g, b = img.getpixel((x, y))
            img.putpixel((x, y), (r + 1, g, b))
    return img


@pytest.fixture
def real_webpage_image() -> Image.Image:
    """Create a more realistic webpage-like test image."""
    img = Image.new("RGB", (1920, 1080), color=(255, 255, 255))

    # Header (dark blue)
    for x in range(1920):
        for y in range(80):
            img.putpixel((x, y), (30, 60, 114))

    # Sidebar (light gray)
    for x in range(250):
        for y in range(80, 1080):
            img.putpixel((x, y), (245, 245, 245))

    # Content area (white with some elements)
    # Button simulation
    for x in range(300, 450):
        for y in range(150, 190):
            img.putpixel((x, y), (59, 130, 246))

    return img
