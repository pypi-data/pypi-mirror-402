"""Cosmux dev module - Zero-config development server for HTML/CSS projects."""

from .vite_config import generate_vite_config
from .runner import DevRunner

__all__ = ["generate_vite_config", "DevRunner"]
