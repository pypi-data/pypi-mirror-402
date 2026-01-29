"""
Base interfaces for feature extractors.

All extractors must provide:
- raw outputs
- confidence scores
- failure modes (no detection, occlusion, etc.)
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
import numpy as np


@dataclass
class Detection:
    """Base class for all detections with confidence and bounds."""

    confidence: float
    bounding_box: Optional[tuple[float, float, float, float]] = None  # x, y, w, h normalized
    track_id: Optional[str] = None

    def is_confident(self, threshold: float = 0.5) -> bool:
        return self.confidence >= threshold


@dataclass
class FaceDetection(Detection):
    """Face detection with expression features."""

    # Landmarks (optional, normalized coordinates)
    landmarks: Optional[np.ndarray] = None  # Nx2 array

    # Expression signals (all optional, models differ)
    valence: Optional[float] = None  # -1 to 1 (negative to positive)
    arousal: Optional[float] = None  # 0 to 1 (calm to excited)
    smile_intensity: Optional[float] = None  # 0 to 1

    # Discrete emotion probabilities (if model provides)
    emotion_probs: Optional[Dict[str, float]] = None  # e.g., {"happy": 0.7, "neutral": 0.2}

    # Head orientation
    head_yaw: Optional[float] = None  # radians
    head_pitch: Optional[float] = None
    head_roll: Optional[float] = None


@dataclass
class PoseDetection(Detection):
    """Body pose detection with keypoints."""

    # Keypoints: dict of joint_name -> (x, y, confidence)
    keypoints: Dict[str, tuple[float, float, float]] = field(default_factory=dict)

    # Derived features
    posture_openness: Optional[float] = None  # 0 to 1
    movement_energy: Optional[float] = None  # computed from frame diff


@dataclass
class GazeDetection(Detection):
    """Gaze/attention detection."""

    gaze_direction: Optional[tuple[float, float, float]] = None  # unit vector
    gaze_target_point: Optional[tuple[float, float]] = None  # where looking in frame
    attention_target_track_id: Optional[str] = None  # who they're looking at (if detected)


@dataclass
class AudioSegment:
    """Audio features for a time segment."""

    start_time: float
    end_time: float
    speaker_id: Optional[str] = None

    # Features
    is_speech: bool = False
    speech_confidence: float = 0.0
    energy: Optional[float] = None
    pitch_mean: Optional[float] = None
    pitch_variance: Optional[float] = None

    # Sentiment (if model provides)
    sentiment_valence: Optional[float] = None  # -1 to 1
    sentiment_confidence: Optional[float] = None


@dataclass
class SceneFeatures:
    """Scene-level features from a frame."""

    # Detection confidence
    confidence: float = 0.0

    # Scene characteristics
    illumination: Optional[float] = None  # 0 to 1
    blur_level: Optional[float] = None  # 0 to 1
    camera_motion: Optional[float] = None  # 0 to 1

    # Scene classification (if model provides)
    scene_type_probs: Optional[Dict[str, float]] = None  # e.g., {"indoor": 0.8}


class FeatureExtractor(ABC):
    """Base interface for all feature extractors."""

    @abstractmethod
    def extract(self, frame: np.ndarray) -> Any:
        """Extract features from a single frame."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Name of this extractor."""
        pass

    @property
    def requires_gpu(self) -> bool:
        """Whether this extractor benefits from GPU."""
        return False


class FaceExtractor(FeatureExtractor):
    """Interface for face detection and expression analysis."""

    @abstractmethod
    def extract(self, frame: np.ndarray) -> List[FaceDetection]:
        """Extract face detections from a frame."""
        pass


class PoseExtractor(FeatureExtractor):
    """Interface for body pose estimation."""

    @abstractmethod
    def extract(self, frame: np.ndarray) -> List[PoseDetection]:
        """Extract pose detections from a frame."""
        pass


class GazeExtractor(FeatureExtractor):
    """Interface for gaze/attention estimation."""

    @abstractmethod
    def extract(
        self, frame: np.ndarray, face_detections: Optional[List[FaceDetection]] = None
    ) -> List[GazeDetection]:
        """Extract gaze detections, optionally using face detections."""
        pass


class AudioExtractor(FeatureExtractor):
    """Interface for audio feature extraction."""

    @abstractmethod
    def extract(self, audio: np.ndarray, sample_rate: int) -> List[AudioSegment]:
        """Extract audio segments with features."""
        pass

    def extract_frame(self, frame: np.ndarray) -> Any:
        """Not applicable for audio."""
        raise NotImplementedError("AudioExtractor works on audio, not frames")


class SceneExtractor(FeatureExtractor):
    """Interface for scene-level feature extraction."""

    @abstractmethod
    def extract(self, frame: np.ndarray) -> SceneFeatures:
        """Extract scene-level features from a frame."""
        pass
