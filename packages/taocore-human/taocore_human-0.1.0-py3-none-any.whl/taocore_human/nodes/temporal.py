"""
Temporal nodes: FrameNode and WindowNode for time-slice analysis.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional
from taocore import Node


@dataclass
class FrameFeatures:
    """Features extracted from a single frame."""

    timestamp: float = 0.0
    frame_index: int = 0

    # Scene-level features
    num_persons_detected: int = 0
    avg_face_confidence: float = 0.0
    avg_pose_confidence: float = 0.0

    # Group dynamics (if multiple persons)
    avg_proximity: Optional[float] = None  # normalized distance
    attention_alignment: Optional[float] = None  # how aligned are gazes/orientations
    group_arousal_mean: Optional[float] = None
    group_valence_mean: Optional[float] = None

    # Scene context
    illumination_level: Optional[float] = None  # 0 to 1
    camera_motion_level: Optional[float] = None  # 0 to 1

    def to_feature_dict(self) -> Dict[str, float]:
        """Convert to flat feature dict for TaoCore Node."""
        features = {"timestamp": self.timestamp, "frame_index": float(self.frame_index)}
        for key, value in self.__dict__.items():
            if key not in ("timestamp", "frame_index") and value is not None:
                features[key] = float(value)
        return features


@dataclass
class FrameNode:
    """
    Represents a single frame for fine-grained temporal analysis.
    """

    frame_id: str
    features: FrameFeatures = field(default_factory=FrameFeatures)
    person_track_ids: List[str] = field(default_factory=list)

    def to_taocore_node(self) -> Node:
        """Convert to a TaoCore Node."""
        return Node(
            id=self.frame_id,
            features=self.features.to_feature_dict(),
        )


@dataclass
class WindowFeatures:
    """Features aggregated over a time window (multiple frames)."""

    start_time: float = 0.0
    end_time: float = 0.0
    start_frame: int = 0
    end_frame: int = 0
    num_frames: int = 0

    # Aggregated scene features
    avg_num_persons: float = 0.0
    max_num_persons: int = 0
    person_turnover: float = 0.0  # how many persons enter/exit

    # Aggregated dynamics
    avg_proximity_mean: Optional[float] = None
    attention_alignment_mean: Optional[float] = None
    attention_alignment_std: Optional[float] = None

    # Group emotional trajectory
    group_arousal_trend: Optional[float] = None  # positive = increasing
    group_valence_trend: Optional[float] = None

    # Activity level
    movement_energy_mean: Optional[float] = None
    movement_energy_std: Optional[float] = None

    # Speaking dynamics (if audio)
    num_speakers: Optional[int] = None
    turn_taking_rate: Optional[float] = None  # turns per minute
    overlap_ratio: Optional[float] = None  # simultaneous speech

    def to_feature_dict(self) -> Dict[str, float]:
        """Convert to flat feature dict for TaoCore Node."""
        features = {
            "start_time": self.start_time,
            "end_time": self.end_time,
            "duration": self.end_time - self.start_time,
            "num_frames": float(self.num_frames),
        }
        for key, value in self.__dict__.items():
            if key not in features and value is not None:
                if isinstance(value, (int, float)):
                    features[key] = float(value)
        return features


@dataclass
class WindowNode:
    """
    Represents a time window (segment) for coarser temporal analysis.
    """

    window_id: str
    features: WindowFeatures = field(default_factory=WindowFeatures)
    person_track_ids: List[str] = field(default_factory=list)

    def to_taocore_node(self) -> Node:
        """Convert to a TaoCore Node."""
        return Node(
            id=self.window_id,
            features=self.features.to_feature_dict(),
        )
