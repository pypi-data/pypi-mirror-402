"""Tests for feature extractors."""

import pytest
import numpy as np

from taocore_human.extractors import StubExtractor
from taocore_human.extractors.stub import (
    StubFaceExtractor,
    StubPoseExtractor,
    StubGazeExtractor,
    StubSceneExtractor,
)
from taocore_human.extractors.base import (
    FaceDetection,
    PoseDetection,
    GazeDetection,
    SceneFeatures,
)


@pytest.fixture
def sample_frame():
    """Create a sample frame (random RGB image)."""
    return np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)


class TestStubFaceExtractor:
    """Tests for StubFaceExtractor."""

    def test_extract_returns_list(self, sample_frame):
        """Test that extract returns a list of FaceDetection."""
        extractor = StubFaceExtractor(seed=42)
        detections = extractor.extract(sample_frame)

        assert isinstance(detections, list)
        for det in detections:
            assert isinstance(det, FaceDetection)

    def test_extract_has_confidence(self, sample_frame):
        """Test that all detections have confidence scores."""
        extractor = StubFaceExtractor(num_faces_range=(1, 3), seed=42)
        detections = extractor.extract(sample_frame)

        for det in detections:
            assert 0 <= det.confidence <= 1

    def test_extract_has_expression_features(self, sample_frame):
        """Test that detections include expression features."""
        extractor = StubFaceExtractor(num_faces_range=(1, 1), seed=42)
        detections = extractor.extract(sample_frame)

        if detections:
            det = detections[0]
            assert det.valence is not None
            assert det.arousal is not None
            assert -1 <= det.valence <= 1
            assert 0 <= det.arousal <= 1

    def test_deterministic_with_seed(self, sample_frame):
        """Test that same seed produces same results."""
        ext1 = StubFaceExtractor(seed=123)
        ext2 = StubFaceExtractor(seed=123)

        det1 = ext1.extract(sample_frame)
        det2 = ext2.extract(sample_frame)

        assert len(det1) == len(det2)
        if det1:
            assert det1[0].confidence == det2[0].confidence

    def test_name_property(self):
        """Test that extractor has a name."""
        extractor = StubFaceExtractor()
        assert extractor.name == "stub_face"


class TestStubPoseExtractor:
    """Tests for StubPoseExtractor."""

    def test_extract_returns_list(self, sample_frame):
        """Test that extract returns a list of PoseDetection."""
        extractor = StubPoseExtractor(seed=42)
        detections = extractor.extract(sample_frame)

        assert isinstance(detections, list)
        for det in detections:
            assert isinstance(det, PoseDetection)

    def test_extract_has_keypoints(self, sample_frame):
        """Test that detections include keypoints."""
        extractor = StubPoseExtractor(num_poses_range=(1, 1), seed=42)
        detections = extractor.extract(sample_frame)

        if detections:
            det = detections[0]
            assert det.keypoints is not None
            assert len(det.keypoints) > 0
            # Check keypoint structure
            for name, (x, y, conf) in det.keypoints.items():
                assert isinstance(name, str)
                assert 0 <= x <= 1
                assert 0 <= y <= 1
                assert 0 <= conf <= 1

    def test_extract_has_posture_features(self, sample_frame):
        """Test that detections include posture features."""
        extractor = StubPoseExtractor(num_poses_range=(1, 1), seed=42)
        detections = extractor.extract(sample_frame)

        if detections:
            det = detections[0]
            assert det.posture_openness is not None
            assert 0 <= det.posture_openness <= 1


class TestStubGazeExtractor:
    """Tests for StubGazeExtractor."""

    def test_extract_with_face_detections(self, sample_frame):
        """Test that extract uses face detections."""
        face_ext = StubFaceExtractor(num_faces_range=(2, 2), seed=42)
        gaze_ext = StubGazeExtractor(seed=42)

        faces = face_ext.extract(sample_frame)
        gazes = gaze_ext.extract(sample_frame, face_detections=faces)

        assert len(gazes) == len(faces)
        for gaze in gazes:
            assert isinstance(gaze, GazeDetection)

    def test_extract_without_faces_returns_empty(self, sample_frame):
        """Test that extract without faces returns empty list."""
        extractor = StubGazeExtractor(seed=42)
        gazes = extractor.extract(sample_frame, face_detections=None)

        assert gazes == []

    def test_gaze_has_direction(self, sample_frame):
        """Test that gaze detections have direction."""
        face_ext = StubFaceExtractor(num_faces_range=(1, 1), seed=42)
        gaze_ext = StubGazeExtractor(seed=42)

        faces = face_ext.extract(sample_frame)
        gazes = gaze_ext.extract(sample_frame, face_detections=faces)

        if gazes:
            gaze = gazes[0]
            assert gaze.gaze_direction is not None
            # Direction should be roughly unit vector
            direction = np.array(gaze.gaze_direction)
            assert 0.9 <= np.linalg.norm(direction) <= 1.1


class TestStubSceneExtractor:
    """Tests for StubSceneExtractor."""

    def test_extract_returns_scene_features(self, sample_frame):
        """Test that extract returns SceneFeatures."""
        extractor = StubSceneExtractor(seed=42)
        features = extractor.extract(sample_frame)

        assert isinstance(features, SceneFeatures)

    def test_extract_has_illumination(self, sample_frame):
        """Test that scene features include illumination."""
        extractor = StubSceneExtractor(seed=42)
        features = extractor.extract(sample_frame)

        assert features.illumination is not None
        assert 0 <= features.illumination <= 1

    def test_extract_has_blur_level(self, sample_frame):
        """Test that scene features include blur level."""
        extractor = StubSceneExtractor(seed=42)
        features = extractor.extract(sample_frame)

        assert features.blur_level is not None
        assert 0 <= features.blur_level <= 1


class TestStubExtractor:
    """Tests for StubExtractor convenience class."""

    def test_has_all_extractors(self):
        """Test that StubExtractor bundles all extractors."""
        stub = StubExtractor(seed=42)

        assert hasattr(stub, "face")
        assert hasattr(stub, "pose")
        assert hasattr(stub, "gaze")
        assert hasattr(stub, "scene")

    def test_extractors_work(self, sample_frame):
        """Test that all bundled extractors work."""
        stub = StubExtractor(seed=42)

        faces = stub.face.extract(sample_frame)
        poses = stub.pose.extract(sample_frame)
        gazes = stub.gaze.extract(sample_frame, face_detections=faces)
        scene = stub.scene.extract(sample_frame)

        assert isinstance(faces, list)
        assert isinstance(poses, list)
        assert isinstance(gazes, list)
        assert isinstance(scene, SceneFeatures)
