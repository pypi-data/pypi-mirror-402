"""Bundled papermill fork exposing `papermill_enhancement.papermill`."""

from importlib import import_module

# Re-export papermill module for convenience, mirroring historical usage.
papermill = import_module(".papermill", __name__)

__all__ = ["papermill"]
