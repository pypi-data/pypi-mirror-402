"""Tests for node types."""

from taocore_human.nodes import PersonNode, FrameNode, WindowNode, ContextNode
from taocore_human.nodes.person import PersonFeatures
from taocore_human.nodes.temporal import FrameFeatures, WindowFeatures
from taocore_human.nodes.context import ContextFeatures


class TestPersonNode:
    """Tests for PersonNode."""

    def test_create_person_node(self):
        """Test basic PersonNode creation."""
        node = PersonNode(track_id="person_1")
        assert node.track_id == "person_1"
        assert node.features.coverage_ratio == 0.0

    def test_person_features_to_dict(self):
        """Test converting PersonFeatures to dict."""
        features = PersonFeatures(
            face_detection_rate=0.8,
            expression_valence_mean=0.5,
            overall_confidence=0.75,
            coverage_ratio=0.8,
        )
        d = features.to_feature_dict()
        assert d["face_detection_rate"] == 0.8
        assert d["expression_valence_mean"] == 0.5
        assert d["overall_confidence"] == 0.75

    def test_person_to_taocore_node(self):
        """Test conversion to TaoCore Node."""
        features = PersonFeatures(
            coverage_ratio=0.7,
            overall_confidence=0.8,
        )
        person = PersonNode(track_id="test_person", features=features)
        taocore_node = person.to_taocore_node()

        assert taocore_node.id == "test_person"
        assert "coverage_ratio" in taocore_node.features

    def test_has_sufficient_coverage(self):
        """Test coverage check."""
        low_coverage = PersonNode(
            track_id="low",
            features=PersonFeatures(coverage_ratio=0.2),
        )
        high_coverage = PersonNode(
            track_id="high",
            features=PersonFeatures(coverage_ratio=0.5),
        )

        assert not low_coverage.has_sufficient_coverage(min_coverage=0.3)
        assert high_coverage.has_sufficient_coverage(min_coverage=0.3)

    def test_has_sufficient_confidence(self):
        """Test confidence check."""
        low_conf = PersonNode(
            track_id="low",
            features=PersonFeatures(overall_confidence=0.3),
        )
        high_conf = PersonNode(
            track_id="high",
            features=PersonFeatures(overall_confidence=0.7),
        )

        assert not low_conf.has_sufficient_confidence(min_confidence=0.5)
        assert high_conf.has_sufficient_confidence(min_confidence=0.5)


class TestFrameNode:
    """Tests for FrameNode."""

    def test_create_frame_node(self):
        """Test basic FrameNode creation."""
        features = FrameFeatures(
            timestamp=1.5,
            frame_index=45,
            num_persons_detected=2,
        )
        node = FrameNode(frame_id="frame_45", features=features)

        assert node.frame_id == "frame_45"
        assert node.features.timestamp == 1.5
        assert node.features.num_persons_detected == 2

    def test_frame_to_taocore_node(self):
        """Test conversion to TaoCore Node."""
        features = FrameFeatures(timestamp=2.0, frame_index=60)
        node = FrameNode(frame_id="frame_60", features=features)
        taocore_node = node.to_taocore_node()

        assert taocore_node.id == "frame_60"
        assert taocore_node.features["timestamp"] == 2.0


class TestWindowNode:
    """Tests for WindowNode."""

    def test_create_window_node(self):
        """Test basic WindowNode creation."""
        features = WindowFeatures(
            start_time=0.0,
            end_time=5.0,
            num_frames=150,
            avg_num_persons=2.5,
        )
        node = WindowNode(
            window_id="window_0",
            features=features,
            person_track_ids=["person_1", "person_2"],
        )

        assert node.window_id == "window_0"
        assert node.features.num_frames == 150
        assert len(node.person_track_ids) == 2

    def test_window_features_duration(self):
        """Test that duration is computed correctly."""
        features = WindowFeatures(start_time=10.0, end_time=15.0)
        d = features.to_feature_dict()
        assert d["duration"] == 5.0


class TestContextNode:
    """Tests for ContextNode."""

    def test_create_context_node(self):
        """Test basic ContextNode creation."""
        features = ContextFeatures(
            avg_illumination=0.7,
            frame_quality_mean=0.8,
        )
        node = ContextNode(context_id="scene", features=features)

        assert node.context_id == "scene"
        assert node.features.avg_illumination == 0.7

    def test_should_reduce_confidence_low_illumination(self):
        """Test confidence reduction for low illumination."""
        low_light = ContextNode(
            context_id="dark",
            features=ContextFeatures(avg_illumination=0.2),
        )
        good_light = ContextNode(
            context_id="bright",
            features=ContextFeatures(avg_illumination=0.7),
        )

        assert low_light.should_reduce_confidence()
        assert not good_light.should_reduce_confidence()

    def test_should_reduce_confidence_high_motion(self):
        """Test confidence reduction for high camera motion."""
        shaky = ContextNode(
            context_id="shaky",
            features=ContextFeatures(camera_motion_mean=0.8),
        )
        stable = ContextNode(
            context_id="stable",
            features=ContextFeatures(camera_motion_mean=0.2),
        )

        assert shaky.should_reduce_confidence()
        assert not stable.should_reduce_confidence()
