"""
Feature extractor interfaces.

These define the contracts for pluggable models that extract features
from images/video frames. Implementations can use any ML framework.
"""

from taocore_human.extractors.base import (
    FeatureExtractor,
    FaceExtractor,
    PoseExtractor,
    GazeExtractor,
    AudioExtractor,
    SceneExtractor,
)
from taocore_human.extractors.stub import StubExtractor

__all__ = [
    "FeatureExtractor",
    "FaceExtractor",
    "PoseExtractor",
    "GazeExtractor",
    "AudioExtractor",
    "SceneExtractor",
    "StubExtractor",
]
