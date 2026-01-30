"""Embedding data points into the color space."""

import contextlib
import importlib.metadata

with contextlib.suppress(importlib.metadata.PackageNotFoundError):
    __version__ = importlib.metadata.version(__package__)
