"""
PersonNode: Represents a tracked individual across time.
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from taocore import Node


@dataclass
class PersonFeatures:
    """Aggregated features for a person across frames/windows."""

    # Face/expression signals (all optional, with confidence)
    face_detection_rate: float = 0.0  # proportion of frames with face detected
    expression_valence_mean: Optional[float] = None  # -1 to 1
    expression_valence_std: Optional[float] = None
    expression_arousal_mean: Optional[float] = None  # 0 to 1
    expression_arousal_std: Optional[float] = None
    smile_intensity_mean: Optional[float] = None  # 0 to 1

    # Body/pose signals
    pose_detection_rate: float = 0.0
    posture_openness_mean: Optional[float] = None  # 0 to 1
    movement_energy_mean: Optional[float] = None  # normalized

    # Attention signals
    gaze_detection_rate: float = 0.0
    head_orientation_variance: Optional[float] = None

    # Audio signals (if applicable)
    speaking_time_ratio: Optional[float] = None  # 0 to 1
    speech_energy_mean: Optional[float] = None

    # Confidence/uncertainty
    overall_confidence: float = 0.0  # average detection confidence
    coverage_ratio: float = 0.0  # frames with any detection / total frames

    def to_feature_dict(self) -> Dict[str, float]:
        """Convert to flat feature dict for TaoCore Node."""
        features = {}
        for key, value in self.__dict__.items():
            if value is not None:
                features[key] = float(value)
        return features


@dataclass
class PersonNode:
    """
    Represents a tracked individual across time.

    Maps to a taocore.Node with aggregated behavioral features.
    Identity is anonymous by default (track_id only).
    """

    track_id: str
    features: PersonFeatures = field(default_factory=PersonFeatures)

    # Metadata (not used in TaoCore features)
    frame_range: tuple[int, int] = (0, 0)  # first and last frame seen
    total_frames_observed: int = 0

    # Optional identity (must be explicitly enabled)
    identity_label: Optional[str] = None

    def to_taocore_node(self) -> Node:
        """Convert to a TaoCore Node for graph analysis."""
        return Node(
            id=self.track_id,
            features=self.features.to_feature_dict(),
        )

    def has_sufficient_coverage(self, min_coverage: float = 0.3) -> bool:
        """Check if we have enough data to make interpretations."""
        return self.features.coverage_ratio >= min_coverage

    def has_sufficient_confidence(self, min_confidence: float = 0.5) -> bool:
        """Check if detection confidence is high enough."""
        return self.features.overall_confidence >= min_confidence
