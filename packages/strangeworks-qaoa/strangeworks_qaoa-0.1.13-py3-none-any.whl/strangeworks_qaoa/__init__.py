"""Strangeworks QAOA SDK Extension."""
import importlib.metadata

from strangeworks_qaoa.sdk import StrangeworksQAOA  # noqa: F401

__version__ = importlib.metadata.version("strangeworks-qaoa")
