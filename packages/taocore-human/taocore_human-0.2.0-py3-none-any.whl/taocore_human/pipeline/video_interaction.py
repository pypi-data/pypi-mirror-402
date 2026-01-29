"""
VideoInteractionPipeline: Process video for interaction dynamics analysis.

Extends the photo pipeline with temporal analysis:
- Time-windowed analysis
- Interaction flow over time
- Turn-taking patterns (if audio)
- Temporal equilibrium
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union
import json

from taocore import Graph, Node, Edge
from taocore.metrics import BalanceMetric, FlowMetric, ClusterMetric, HubMetric
from taocore.solvers import EquilibriumSolver

from taocore_human.adapters import VideoAdapter
from taocore_human.extractors import StubExtractor
from taocore_human.extractors.base import FaceExtractor, PoseExtractor, SceneExtractor
from taocore_human.nodes import PersonNode, WindowNode, ContextNode
from taocore_human.nodes.person import PersonFeatures
from taocore_human.nodes.temporal import WindowFeatures
from taocore_human.reports import AnalysisReport, ReportGenerator


@dataclass
class VideoPipelineConfig:
    """Configuration for video pipeline."""

    # Window settings
    window_duration: float = 5.0  # seconds
    window_overlap: float = 1.0  # seconds

    # Sampling (for efficiency)
    sample_fps: float = 2.0  # process 2 frames per second

    # Minimum requirements
    min_coverage: float = 0.3
    min_confidence: float = 0.5
    min_duration: float = 10.0  # minimum video duration in seconds

    # Equilibrium
    max_iterations: int = 100
    tolerance: float = 1e-4

    # Interpretation strictness
    strict_mode: bool = True


@dataclass
class VideoResult:
    """Result from video pipeline."""

    # Per-window graphs
    window_graphs: List[Graph]
    window_nodes: List[WindowNode]

    # Aggregated graph
    aggregated_graph: Graph
    person_nodes: List[PersonNode]
    context_node: Optional[ContextNode]

    # Metrics
    balance_metrics: Optional[Dict] = None
    flow_metrics: Optional[Dict] = None
    cluster_metrics: Optional[Dict] = None
    hub_metrics: Optional[Dict] = None

    # Temporal patterns
    temporal_patterns: Dict = field(default_factory=dict)

    # Equilibrium
    equilibrium_converged: bool = False
    equilibrium_iterations: int = 0
    equilibrium_diagnostics: Dict = field(default_factory=dict)

    # Decisions
    interpretation_allowed: bool = False
    rejection_reasons: List[str] = field(default_factory=list)

    # Report
    report: Optional[AnalysisReport] = None


class VideoInteractionPipeline:
    """
    Process video for interaction dynamics analysis.

    Example:
        pipeline = VideoInteractionPipeline("/path/to/video.mp4")
        result = pipeline.run()
        print(result.report.summary)
    """

    def __init__(
        self,
        video_path: Union[str, Path],
        config: Optional[VideoPipelineConfig] = None,
        face_extractor: Optional[FaceExtractor] = None,
        pose_extractor: Optional[PoseExtractor] = None,
        scene_extractor: Optional[SceneExtractor] = None,
    ):
        self.video_path = Path(video_path)
        self.config = config or VideoPipelineConfig()

        # Use stub extractors if none provided
        stub = StubExtractor(seed=42)
        self.face_extractor = face_extractor or stub.face
        self.pose_extractor = pose_extractor or stub.pose
        self.scene_extractor = scene_extractor or stub.scene

    def run(self) -> VideoResult:
        """Run the full video pipeline."""

        with VideoAdapter(self.video_path) as video:
            metadata = video.metadata

            # Early rejection if too short
            if metadata.duration < self.config.min_duration:
                return VideoResult(
                    window_graphs=[],
                    window_nodes=[],
                    aggregated_graph=Graph(nodes=[], edges=[]),
                    person_nodes=[],
                    context_node=None,
                    interpretation_allowed=False,
                    rejection_reasons=[
                        f"Video too short: {metadata.duration:.1f}s < {self.config.min_duration}s"
                    ],
                )

            # Process each window
            window_nodes = []
            all_person_features: Dict[str, List[Dict]] = {}
            window_graphs = []

            for start_time, end_time, frames in video.get_windows(
                window_duration=self.config.window_duration,
                overlap=self.config.window_overlap,
            ):
                window_id = f"window_{len(window_nodes)}"

                # Extract features from window frames
                window_features, person_features = self._process_window(
                    frames, window_id
                )

                # Merge person features
                for track_id, features in person_features.items():
                    if track_id not in all_person_features:
                        all_person_features[track_id] = []
                    all_person_features[track_id].extend(features)

                # Create window node
                wn = WindowNode(
                    window_id=window_id,
                    features=window_features,
                    person_track_ids=list(person_features.keys()),
                )
                window_nodes.append(wn)

                # Create window graph
                wg = self._build_window_graph(person_features)
                window_graphs.append(wg)

            # Build aggregated person nodes
            total_frames = sum(len(wn.person_track_ids) for wn in window_nodes) or 1
            person_nodes = self._build_person_nodes(all_person_features, total_frames)

            # Build aggregated graph
            aggregated_graph = self._build_aggregated_graph(person_nodes, window_nodes)

            # Build context
            context_node = self._build_context_node(metadata)

            # Compute metrics
            balance_metrics = self._compute_balance(aggregated_graph)
            flow_metrics = self._compute_flow(window_graphs)
            cluster_metrics = self._compute_clusters(aggregated_graph)
            hub_metrics = self._compute_hubs(aggregated_graph)

            # Compute temporal patterns
            temporal_patterns = self._analyze_temporal_patterns(window_nodes)

            # Run equilibrium
            eq_result = self._run_equilibrium(aggregated_graph)

            # Apply decider
            interpretation_allowed, rejection_reasons = self._apply_decider(
                person_nodes, context_node, eq_result, temporal_patterns
            )

            result = VideoResult(
                window_graphs=window_graphs,
                window_nodes=window_nodes,
                aggregated_graph=aggregated_graph,
                person_nodes=person_nodes,
                context_node=context_node,
                balance_metrics=balance_metrics,
                flow_metrics=flow_metrics,
                cluster_metrics=cluster_metrics,
                hub_metrics=hub_metrics,
                temporal_patterns=temporal_patterns,
                equilibrium_converged=eq_result.get("converged", False),
                equilibrium_iterations=eq_result.get("iterations", 0),
                equilibrium_diagnostics=eq_result,
                interpretation_allowed=interpretation_allowed,
                rejection_reasons=rejection_reasons,
            )

            result.report = ReportGenerator.generate_video(result, self.config)

            return result

    def _process_window(
        self, frames: List, window_id: str
    ) -> tuple[WindowFeatures, Dict[str, List[Dict]]]:
        """Process frames in a window."""
        import numpy as np

        person_features: Dict[str, List[Dict]] = {}
        num_persons_list = []
        arousals = []
        valences = []

        for frame in frames:
            face_detections = self.face_extractor.extract(frame.data)
            num_persons_list.append(len(face_detections))

            for det in face_detections:
                track_id = det.track_id or f"unknown_{len(person_features)}"
                if track_id not in person_features:
                    person_features[track_id] = []

                person_features[track_id].append(
                    {
                        "timestamp": frame.timestamp,
                        "confidence": det.confidence,
                        "valence": det.valence,
                        "arousal": det.arousal,
                    }
                )

                if det.arousal is not None:
                    arousals.append(det.arousal)
                if det.valence is not None:
                    valences.append(det.valence)

        # Compute window features
        wf = WindowFeatures(
            start_time=frames[0].timestamp if frames else 0,
            end_time=frames[-1].timestamp if frames else 0,
            start_frame=frames[0].frame_index if frames else 0,
            end_frame=frames[-1].frame_index if frames else 0,
            num_frames=len(frames),
            avg_num_persons=float(np.mean(num_persons_list)) if num_persons_list else 0,
            max_num_persons=max(num_persons_list) if num_persons_list else 0,
        )

        if arousals:
            # Simple trend: compare second half to first half
            mid = len(arousals) // 2
            if mid > 0:
                wf.group_arousal_trend = float(
                    np.mean(arousals[mid:]) - np.mean(arousals[:mid])
                )

        if valences:
            mid = len(valences) // 2
            if mid > 0:
                wf.group_valence_trend = float(
                    np.mean(valences[mid:]) - np.mean(valences[:mid])
                )

        return wf, person_features

    def _build_window_graph(self, person_features: Dict[str, List[Dict]]) -> Graph:
        """Build a graph for a single window."""
        nodes = []
        for track_id, features in person_features.items():
            avg_conf = sum(f["confidence"] for f in features) / len(features)
            nodes.append(
                Node(
                    id=track_id,
                    features={"confidence": avg_conf, "num_observations": len(features)},
                )
            )

        # Edges between all co-occurring persons
        edges = []
        track_ids = list(person_features.keys())
        for i, t1 in enumerate(track_ids):
            for j, t2 in enumerate(track_ids):
                if i < j:
                    edges.append(Edge(source=t1, target=t2, weight=1.0))

        return Graph(nodes=nodes, edges=edges)

    def _build_person_nodes(
        self, all_features: Dict[str, List[Dict]], total_observations: int
    ) -> List[PersonNode]:
        """Build aggregated person nodes."""
        import numpy as np

        nodes = []
        for track_id, features in all_features.items():
            coverage = len(features) / max(total_observations, 1)
            avg_conf = sum(f["confidence"] for f in features) / len(features)

            valences = [f["valence"] for f in features if f.get("valence") is not None]
            arousals = [f["arousal"] for f in features if f.get("arousal") is not None]

            pf = PersonFeatures(
                face_detection_rate=coverage,
                overall_confidence=avg_conf,
                coverage_ratio=coverage,
            )

            if valences:
                pf.expression_valence_mean = float(np.mean(valences))
                pf.expression_valence_std = float(np.std(valences))

            if arousals:
                pf.expression_arousal_mean = float(np.mean(arousals))
                pf.expression_arousal_std = float(np.std(arousals))

            node = PersonNode(track_id=track_id, features=pf)
            nodes.append(node)

        return nodes

    def _build_aggregated_graph(
        self, person_nodes: List[PersonNode], window_nodes: List[WindowNode]
    ) -> Graph:
        """Build aggregated graph across all windows."""
        nodes = [pn.to_taocore_node() for pn in person_nodes]

        # Count co-occurrences across windows
        co_occurrence: Dict[tuple, int] = {}
        for wn in window_nodes:
            tracks = wn.person_track_ids
            for i, t1 in enumerate(tracks):
                for j, t2 in enumerate(tracks):
                    if i < j:
                        key = (min(t1, t2), max(t1, t2))
                        co_occurrence[key] = co_occurrence.get(key, 0) + 1

        # Create edges weighted by co-occurrence
        edges = []
        max_co = max(co_occurrence.values()) if co_occurrence else 1
        for (t1, t2), count in co_occurrence.items():
            edges.append(Edge(source=t1, target=t2, weight=count / max_co))

        return Graph(nodes=nodes, edges=edges)

    def _build_context_node(self, metadata) -> ContextNode:
        """Build context from video metadata."""
        from taocore_human.nodes.context import ContextFeatures

        cf = ContextFeatures()
        return ContextNode(
            context_id="video_context",
            features=cf,
            source_path=str(self.video_path),
            time_range=(0, metadata.duration),
        )

    def _compute_balance(self, graph: Graph) -> Optional[Dict]:
        if not graph.nodes:
            return None
        try:
            return BalanceMetric().compute(graph)
        except Exception:
            return None

    def _compute_flow(self, window_graphs: List[Graph]) -> Optional[Dict]:
        if len(window_graphs) < 2:
            return None
        try:
            return FlowMetric().compute_sequence(window_graphs)
        except Exception:
            return None

    def _compute_clusters(self, graph: Graph) -> Optional[Dict]:
        if not graph.nodes or len(graph.nodes) < 2:
            return None
        try:
            return ClusterMetric().compute(graph)
        except Exception:
            return None

    def _compute_hubs(self, graph: Graph) -> Optional[Dict]:
        if not graph.nodes:
            return None
        try:
            return HubMetric().compute(graph)
        except Exception:
            return None

    def _analyze_temporal_patterns(self, window_nodes: List[WindowNode]) -> Dict:
        """Analyze patterns across time windows."""
        import numpy as np

        if not window_nodes:
            return {}

        arousal_trends = [
            wn.features.group_arousal_trend
            for wn in window_nodes
            if wn.features.group_arousal_trend is not None
        ]

        valence_trends = [
            wn.features.group_valence_trend
            for wn in window_nodes
            if wn.features.group_valence_trend is not None
        ]

        patterns = {
            "num_windows": len(window_nodes),
            "avg_persons_per_window": float(
                np.mean([wn.features.avg_num_persons for wn in window_nodes])
            ),
        }

        if arousal_trends:
            patterns["overall_arousal_trend"] = float(np.mean(arousal_trends))
            patterns["arousal_volatility"] = float(np.std(arousal_trends))

        if valence_trends:
            patterns["overall_valence_trend"] = float(np.mean(valence_trends))
            patterns["valence_volatility"] = float(np.std(valence_trends))

        return patterns

    def _run_equilibrium(self, graph: Graph) -> Dict:
        if not graph.nodes:
            return {"converged": False, "reason": "no nodes"}
        try:
            solver = EquilibriumSolver(
                max_iterations=self.config.max_iterations,
                tolerance=self.config.tolerance,
            )
            result = solver.solve(graph)
            return {
                "converged": result.converged,
                "iterations": result.iterations,
                "final_residual": result.residual,
            }
        except Exception as e:
            return {"converged": False, "error": str(e)}

    def _apply_decider(
        self,
        person_nodes: List[PersonNode],
        context_node: Optional[ContextNode],
        eq_result: Dict,
        temporal_patterns: Dict,
    ) -> tuple[bool, List[str]]:
        """Apply decider rules."""
        reasons = []

        sufficient = [
            pn
            for pn in person_nodes
            if pn.has_sufficient_coverage(self.config.min_coverage)
            and pn.has_sufficient_confidence(self.config.min_confidence)
        ]

        if not sufficient:
            reasons.append("No persons with sufficient coverage and confidence")

        if not eq_result.get("converged", False):
            reasons.append("Equilibrium did not converge")

        # Check for high volatility (conflicting signals)
        if temporal_patterns.get("arousal_volatility", 0) > 0.5:
            reasons.append("High arousal volatility suggests mixed/conflicting signals")

        if self.config.strict_mode:
            interpretation_allowed = len(reasons) == 0
        else:
            interpretation_allowed = len(sufficient) > 0

        return interpretation_allowed, reasons

    def to_json(self, result: VideoResult) -> str:
        """Export result as JSON."""
        data = {
            "video": str(self.video_path),
            "num_windows": len(result.window_nodes),
            "num_persons": len(result.person_nodes),
            "interpretation_allowed": result.interpretation_allowed,
            "rejection_reasons": result.rejection_reasons,
            "temporal_patterns": result.temporal_patterns,
            "equilibrium": {
                "converged": result.equilibrium_converged,
                "iterations": result.equilibrium_iterations,
            },
        }

        if result.report:
            data["summary"] = result.report.summary

        return json.dumps(data, indent=2)
