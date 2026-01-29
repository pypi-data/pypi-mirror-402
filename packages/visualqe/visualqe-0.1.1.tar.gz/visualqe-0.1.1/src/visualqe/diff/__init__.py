"""Image diff algorithms."""

from visualqe.diff.base import DiffAlgorithm
from visualqe.diff.pixel import PixelDiff
from visualqe.diff.ssim import SSIMDiff

__all__ = ["DiffAlgorithm", "PixelDiff", "SSIMDiff"]
