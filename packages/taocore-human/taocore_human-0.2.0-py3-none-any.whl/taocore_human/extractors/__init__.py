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

# MediaPipe extractors (optional, requires mediapipe package)
try:
    from taocore_human.extractors.mediapipe_extractor import (
        MediaPipeExtractor,
        MediaPipeFaceExtractor,
        MediaPipePoseExtractor,
    )
    _MEDIAPIPE_AVAILABLE = True
except ImportError:
    _MEDIAPIPE_AVAILABLE = False
    MediaPipeExtractor = None
    MediaPipeFaceExtractor = None
    MediaPipePoseExtractor = None

# CLIP scene extractor (optional, requires transformers and torch)
try:
    from taocore_human.extractors.scene_extractor import CLIPSceneExtractor
    _CLIP_AVAILABLE = True
except ImportError:
    _CLIP_AVAILABLE = False
    CLIPSceneExtractor = None

__all__ = [
    "FeatureExtractor",
    "FaceExtractor",
    "PoseExtractor",
    "GazeExtractor",
    "AudioExtractor",
    "SceneExtractor",
    "StubExtractor",
    "MediaPipeExtractor",
    "MediaPipeFaceExtractor",
    "MediaPipePoseExtractor",
    "CLIPSceneExtractor",
]
