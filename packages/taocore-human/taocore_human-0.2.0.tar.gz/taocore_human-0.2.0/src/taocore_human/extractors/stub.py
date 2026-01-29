"""
Stub extractors for testing and demonstration.

These generate plausible random data without requiring ML models.
Useful for testing the pipeline and understanding output formats.
"""

from typing import List, Optional
import numpy as np

from taocore_human.extractors.base import (
    FaceExtractor,
    PoseExtractor,
    GazeExtractor,
    SceneExtractor,
    FaceDetection,
    PoseDetection,
    GazeDetection,
    SceneFeatures,
)


class StubFaceExtractor(FaceExtractor):
    """Generates random face detections for testing."""

    def __init__(self, num_faces_range: tuple[int, int] = (0, 3), seed: Optional[int] = None):
        self.num_faces_range = num_faces_range
        self.rng = np.random.default_rng(seed)

    @property
    def name(self) -> str:
        return "stub_face"

    def extract(self, frame: np.ndarray) -> List[FaceDetection]:
        num_faces = self.rng.integers(self.num_faces_range[0], self.num_faces_range[1] + 1)
        detections = []

        for i in range(num_faces):
            detection = FaceDetection(
                confidence=self.rng.uniform(0.5, 0.99),
                bounding_box=(
                    self.rng.uniform(0.1, 0.7),  # x
                    self.rng.uniform(0.1, 0.5),  # y
                    self.rng.uniform(0.1, 0.3),  # w
                    self.rng.uniform(0.15, 0.4),  # h
                ),
                track_id=f"person_{i}",
                valence=self.rng.uniform(-0.5, 0.8),
                arousal=self.rng.uniform(0.2, 0.7),
                smile_intensity=self.rng.uniform(0, 0.6),
                head_yaw=self.rng.uniform(-0.5, 0.5),
                head_pitch=self.rng.uniform(-0.3, 0.3),
                head_roll=self.rng.uniform(-0.2, 0.2),
            )
            detections.append(detection)

        return detections


class StubPoseExtractor(PoseExtractor):
    """Generates random pose detections for testing."""

    KEYPOINT_NAMES = [
        "nose", "left_eye", "right_eye", "left_ear", "right_ear",
        "left_shoulder", "right_shoulder", "left_elbow", "right_elbow",
        "left_wrist", "right_wrist", "left_hip", "right_hip",
        "left_knee", "right_knee", "left_ankle", "right_ankle",
    ]

    def __init__(self, num_poses_range: tuple[int, int] = (0, 3), seed: Optional[int] = None):
        self.num_poses_range = num_poses_range
        self.rng = np.random.default_rng(seed)

    @property
    def name(self) -> str:
        return "stub_pose"

    def extract(self, frame: np.ndarray) -> List[PoseDetection]:
        num_poses = self.rng.integers(self.num_poses_range[0], self.num_poses_range[1] + 1)
        detections = []

        for i in range(num_poses):
            keypoints = {}
            base_x = self.rng.uniform(0.2, 0.8)
            base_y = self.rng.uniform(0.2, 0.6)

            for j, name in enumerate(self.KEYPOINT_NAMES):
                keypoints[name] = (
                    base_x + self.rng.uniform(-0.15, 0.15),
                    base_y + j * 0.03 + self.rng.uniform(-0.02, 0.02),
                    self.rng.uniform(0.5, 0.99),  # confidence
                )

            detection = PoseDetection(
                confidence=self.rng.uniform(0.6, 0.95),
                track_id=f"person_{i}",
                keypoints=keypoints,
                posture_openness=self.rng.uniform(0.3, 0.8),
                movement_energy=self.rng.uniform(0.1, 0.5),
            )
            detections.append(detection)

        return detections


class StubGazeExtractor(GazeExtractor):
    """Generates random gaze detections for testing."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    @property
    def name(self) -> str:
        return "stub_gaze"

    def extract(
        self, frame: np.ndarray, face_detections: Optional[List[FaceDetection]] = None
    ) -> List[GazeDetection]:
        if face_detections is None:
            return []

        detections = []
        for face in face_detections:
            # Random gaze direction (unit vector)
            theta = self.rng.uniform(0, 2 * np.pi)
            phi = self.rng.uniform(0, np.pi / 2)
            direction = (
                np.sin(phi) * np.cos(theta),
                np.sin(phi) * np.sin(theta),
                np.cos(phi),
            )

            detection = GazeDetection(
                confidence=face.confidence * self.rng.uniform(0.7, 1.0),
                track_id=face.track_id,
                gaze_direction=direction,
                gaze_target_point=(self.rng.uniform(0, 1), self.rng.uniform(0, 1)),
            )
            detections.append(detection)

        return detections


class StubSceneExtractor(SceneExtractor):
    """Generates random scene features for testing."""

    def __init__(self, seed: Optional[int] = None):
        self.rng = np.random.default_rng(seed)

    @property
    def name(self) -> str:
        return "stub_scene"

    def extract(self, frame: np.ndarray) -> SceneFeatures:
        return SceneFeatures(
            confidence=self.rng.uniform(0.7, 0.99),
            illumination=self.rng.uniform(0.4, 0.9),
            blur_level=self.rng.uniform(0.0, 0.3),
            camera_motion=self.rng.uniform(0.0, 0.2),
            scene_type_probs={
                "indoor": self.rng.uniform(0.3, 0.8),
                "outdoor": self.rng.uniform(0.1, 0.5),
            },
        )


class StubExtractor:
    """Convenience class bundling all stub extractors."""

    def __init__(self, seed: Optional[int] = None):
        self.face = StubFaceExtractor(seed=seed)
        self.pose = StubPoseExtractor(seed=seed)
        self.gaze = StubGazeExtractor(seed=seed)
        self.scene = StubSceneExtractor(seed=seed)
