"""
NeuralkAI SDK for tabular machine learning.

This module provides sklearn-compatible classifiers for using Neuralk's
In-Context Learning models, both via the cloud API and on-premise deployments.
"""

from pathlib import Path

from ._api import NeuralkAPI
from ._classifier import Classifier, NICLClassifier, OnPremiseClassifier
from .exceptions import NeuralkException
from .neuralk import get_access_token

VERSION_PATH = Path(__file__).resolve().parent / "VERSION.txt"
__version__ = VERSION_PATH.read_text(encoding="utf-8").strip()


__all__ = [
    # API client
    "NeuralkAPI",
    # Classifiers
    "NICLClassifier",
    "Classifier",  # Deprecated, use NICLClassifier
    "OnPremiseClassifier",  # Deprecated, use NICLClassifier(host="...")
    # Exceptions
    "NeuralkException",
    # Utilities
    "get_access_token",
]
