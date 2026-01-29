"""
ContextNode: Represents scene context (location, environment, etc.).
"""

from dataclasses import dataclass, field
from typing import Dict, Optional
from taocore import Node


@dataclass
class ContextFeatures:
    """Scene/environment context features."""

    # Scene type indicators (could be classifier outputs)
    indoor_probability: Optional[float] = None
    outdoor_probability: Optional[float] = None
    crowded_probability: Optional[float] = None

    # Environmental conditions
    avg_illumination: Optional[float] = None  # 0 to 1
    illumination_variance: Optional[float] = None  # stability
    noise_level: Optional[float] = None  # 0 to 1 (if audio)

    # Camera characteristics
    camera_motion_mean: Optional[float] = None
    camera_motion_variance: Optional[float] = None
    frame_quality_mean: Optional[float] = None  # blur, compression artifacts

    # Spatial layout (if detectable)
    scene_depth_estimate: Optional[float] = None
    open_space_ratio: Optional[float] = None

    def to_feature_dict(self) -> Dict[str, float]:
        """Convert to flat feature dict for TaoCore Node."""
        features = {}
        for key, value in self.__dict__.items():
            if value is not None:
                features[key] = float(value)
        return features


@dataclass
class ContextNode:
    """
    Represents scene context that may influence interpretation.

    Context affects how we should interpret behavioral signals:
    - Low illumination → lower confidence in expression detection
    - High camera motion → lower confidence in tracking
    - Crowded scene → more occlusions expected
    """

    context_id: str
    features: ContextFeatures = field(default_factory=ContextFeatures)

    # Metadata
    source_path: Optional[str] = None
    time_range: Optional[tuple[float, float]] = None

    def to_taocore_node(self) -> Node:
        """Convert to a TaoCore Node."""
        return Node(
            id=self.context_id,
            features=self.features.to_feature_dict(),
        )

    def should_reduce_confidence(self) -> bool:
        """Check if context suggests we should be less confident."""
        if self.features.avg_illumination is not None:
            if self.features.avg_illumination < 0.3:
                return True
        if self.features.camera_motion_mean is not None:
            if self.features.camera_motion_mean > 0.7:
                return True
        if self.features.frame_quality_mean is not None:
            if self.features.frame_quality_mean < 0.4:
                return True
        return False
