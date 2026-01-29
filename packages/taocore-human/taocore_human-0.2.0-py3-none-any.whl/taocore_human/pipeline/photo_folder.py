"""
PhotoFolderPipeline: Process a folder of images into a behavioral analysis report.

This is the v0 minimal pipeline from RFC-4:
1. Load images from folder
2. Extract features (face, pose, scene)
3. Build PersonNodes and edges
4. Run TaoCore metrics (balance, clusters, hubs)
5. Run equilibrium solver for stabilized summary
6. Apply conservative decider rules
7. Output JSON + text summary
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Union
import json

from taocore import Graph, Edge
from taocore.metrics import BalanceMetric, ClusterMetric, HubMetric
from taocore.solvers import EquilibriumSolver

from taocore_human.adapters import ImageFolderAdapter
from taocore_human.extractors import StubExtractor
from taocore_human.extractors.base import FaceExtractor, PoseExtractor, SceneExtractor
from taocore_human.nodes import PersonNode, ContextNode
from taocore_human.nodes.person import PersonFeatures
from taocore_human.reports import AnalysisReport, ReportGenerator


@dataclass
class PipelineConfig:
    """Configuration for the photo folder pipeline."""

    # Minimum requirements for interpretation
    min_coverage: float = 0.3  # person must appear in 30% of images
    min_confidence: float = 0.5  # minimum detection confidence
    min_images: int = 3  # need at least 3 images

    # Edge construction
    co_occurrence_threshold: int = 2  # must co-occur in N images to create edge

    # Equilibrium solver
    max_iterations: int = 100
    tolerance: float = 1e-4

    # Interpretation strictness
    strict_mode: bool = True  # if True, refuse to interpret low-quality data


@dataclass
class PipelineResult:
    """Result from running the pipeline."""

    graph: Graph
    person_nodes: List[PersonNode]
    context_node: Optional[ContextNode]

    # Metrics
    balance_metrics: Optional[Dict] = None
    cluster_metrics: Optional[Dict] = None
    hub_metrics: Optional[Dict] = None

    # Equilibrium
    equilibrium_converged: bool = False
    equilibrium_iterations: int = 0
    equilibrium_diagnostics: Dict = field(default_factory=dict)

    # Decisions
    interpretation_allowed: bool = False
    rejection_reasons: List[str] = field(default_factory=list)

    # Report
    report: Optional[AnalysisReport] = None


class PhotoFolderPipeline:
    """
    Process a folder of images into behavioral analysis.

    Example:
        pipeline = PhotoFolderPipeline("/path/to/photos")
        result = pipeline.run()
        print(result.report.summary)
    """

    def __init__(
        self,
        folder: Union[str, Path],
        config: Optional[PipelineConfig] = None,
        face_extractor: Optional[FaceExtractor] = None,
        pose_extractor: Optional[PoseExtractor] = None,
        scene_extractor: Optional[SceneExtractor] = None,
    ):
        self.folder = Path(folder)
        self.config = config or PipelineConfig()

        # Use stub extractors if none provided
        stub = StubExtractor(seed=42)
        self.face_extractor = face_extractor or stub.face
        self.pose_extractor = pose_extractor or stub.pose
        self.scene_extractor = scene_extractor or stub.scene

        self._adapter: Optional[ImageFolderAdapter] = None

    def run(self) -> PipelineResult:
        """Run the full pipeline."""
        # Step 1: Load images
        self._adapter = ImageFolderAdapter(self.folder)
        num_images = len(self._adapter)

        # Early rejection if too few images
        if num_images < self.config.min_images:
            return PipelineResult(
                graph=Graph(nodes=[], edges=[]),
                person_nodes=[],
                context_node=None,
                interpretation_allowed=False,
                rejection_reasons=[
                    f"Insufficient images: {num_images} < {self.config.min_images}"
                ],
            )

        # Step 2: Extract features from all images
        person_features = self._extract_all_features()

        # Step 3: Build PersonNodes
        person_nodes = self._build_person_nodes(person_features, num_images)

        # Step 4: Build context node
        context_node = self._build_context_node()

        # Step 5: Build graph with edges
        graph = self._build_graph(person_nodes, num_images)

        # Step 6: Run metrics
        balance_metrics = self._compute_balance(graph)
        cluster_metrics = self._compute_clusters(graph)
        hub_metrics = self._compute_hubs(graph)

        # Step 7: Run equilibrium solver
        eq_result = self._run_equilibrium(graph)

        # Step 8: Apply decider rules
        interpretation_allowed, rejection_reasons = self._apply_decider(
            person_nodes, context_node, eq_result
        )

        # Step 9: Generate report
        result = PipelineResult(
            graph=graph,
            person_nodes=person_nodes,
            context_node=context_node,
            balance_metrics=balance_metrics,
            cluster_metrics=cluster_metrics,
            hub_metrics=hub_metrics,
            equilibrium_converged=eq_result.get("converged", False),
            equilibrium_iterations=eq_result.get("iterations", 0),
            equilibrium_diagnostics=eq_result,
            interpretation_allowed=interpretation_allowed,
            rejection_reasons=rejection_reasons,
        )

        result.report = ReportGenerator.generate(result, self.config)

        return result

    def _extract_all_features(self) -> Dict[str, List[Dict]]:
        """Extract features from all images, grouped by track_id."""
        person_features: Dict[str, List[Dict]] = {}

        for frame in self._adapter:
            # Extract faces
            face_detections = self.face_extractor.extract(frame.data)

            for det in face_detections:
                track_id = det.track_id or f"unknown_{len(person_features)}"
                if track_id not in person_features:
                    person_features[track_id] = []

                person_features[track_id].append(
                    {
                        "frame_index": frame.index,
                        "confidence": det.confidence,
                        "valence": det.valence,
                        "arousal": det.arousal,
                        "smile_intensity": det.smile_intensity,
                    }
                )

        return person_features

    def _build_person_nodes(
        self, person_features: Dict[str, List[Dict]], num_images: int
    ) -> List[PersonNode]:
        """Build PersonNodes from extracted features."""
        nodes = []

        for track_id, features_list in person_features.items():
            # Aggregate features
            coverage = len(features_list) / num_images
            avg_confidence = sum(f["confidence"] for f in features_list) / len(features_list)

            # Extract non-None values for each feature
            valences = [f["valence"] for f in features_list if f.get("valence") is not None]
            arousals = [f["arousal"] for f in features_list if f.get("arousal") is not None]
            smiles = [f["smile_intensity"] for f in features_list if f.get("smile_intensity") is not None]

            pf = PersonFeatures(
                face_detection_rate=coverage,
                overall_confidence=avg_confidence,
                coverage_ratio=coverage,
            )

            if valences:
                import numpy as np
                pf.expression_valence_mean = float(np.mean(valences))
                pf.expression_valence_std = float(np.std(valences))

            if arousals:
                import numpy as np
                pf.expression_arousal_mean = float(np.mean(arousals))
                pf.expression_arousal_std = float(np.std(arousals))

            if smiles:
                import numpy as np
                pf.smile_intensity_mean = float(np.mean(smiles))

            node = PersonNode(
                track_id=track_id,
                features=pf,
                frame_range=(
                    min(f["frame_index"] for f in features_list),
                    max(f["frame_index"] for f in features_list),
                ),
                total_frames_observed=len(features_list),
            )
            nodes.append(node)

        return nodes

    def _build_context_node(self) -> ContextNode:
        """Build context node from scene features."""
        from taocore_human.nodes.context import ContextFeatures
        import numpy as np

        illuminations = []
        blur_levels = []

        for frame in self._adapter:
            scene = self.scene_extractor.extract(frame.data)
            if scene.illumination is not None:
                illuminations.append(scene.illumination)
            if scene.blur_level is not None:
                blur_levels.append(scene.blur_level)

        cf = ContextFeatures()
        if illuminations:
            cf.avg_illumination = float(np.mean(illuminations))
            cf.illumination_variance = float(np.var(illuminations))
        if blur_levels:
            cf.frame_quality_mean = float(1 - np.mean(blur_levels))

        return ContextNode(
            context_id="scene_context",
            features=cf,
            source_path=str(self.folder),
        )

    def _build_graph(self, person_nodes: List[PersonNode], num_images: int) -> Graph:
        """Build TaoCore graph from person nodes with co-occurrence edges."""
        nodes = [pn.to_taocore_node() for pn in person_nodes]

        # Build edges based on co-occurrence
        edges = []
        for i, pn1 in enumerate(person_nodes):
            for j, pn2 in enumerate(person_nodes):
                if i >= j:
                    continue

                # Simple co-occurrence: both must have sufficient coverage
                if (
                    pn1.features.coverage_ratio > 0.1
                    and pn2.features.coverage_ratio > 0.1
                ):
                    # Weight by minimum coverage (conservative)
                    weight = min(pn1.features.coverage_ratio, pn2.features.coverage_ratio)
                    edges.append(
                        Edge(source=pn1.track_id, target=pn2.track_id, weight=weight)
                    )

        return Graph(nodes=nodes, edges=edges)

    def _compute_balance(self, graph: Graph) -> Optional[Dict]:
        """Compute balance metrics."""
        if not graph.nodes:
            return None
        try:
            metric = BalanceMetric()
            return metric.compute(graph)
        except Exception:
            return None

    def _compute_clusters(self, graph: Graph) -> Optional[Dict]:
        """Compute cluster metrics."""
        if not graph.nodes or len(graph.nodes) < 2:
            return None
        try:
            metric = ClusterMetric()
            return metric.compute(graph)
        except Exception:
            return None

    def _compute_hubs(self, graph: Graph) -> Optional[Dict]:
        """Compute hub metrics."""
        if not graph.nodes:
            return None
        try:
            metric = HubMetric()
            return metric.compute(graph)
        except Exception:
            return None

    def _run_equilibrium(self, graph: Graph) -> Dict:
        """Run equilibrium solver."""
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
    ) -> tuple[bool, List[str]]:
        """Apply decider rules to determine if interpretation is allowed."""
        reasons = []

        # Check if any persons have sufficient data
        sufficient_persons = [
            pn
            for pn in person_nodes
            if pn.has_sufficient_coverage(self.config.min_coverage)
            and pn.has_sufficient_confidence(self.config.min_confidence)
        ]

        if not sufficient_persons:
            reasons.append(
                f"No persons with sufficient coverage (>{self.config.min_coverage}) "
                f"and confidence (>{self.config.min_confidence})"
            )

        # Check context quality
        if context_node and context_node.should_reduce_confidence():
            reasons.append("Scene context suggests low data quality (illumination/blur)")

        # Check equilibrium
        if not eq_result.get("converged", False):
            reasons.append("Equilibrium solver did not converge (signals may be conflicting)")

        # In strict mode, any reason blocks interpretation
        if self.config.strict_mode:
            interpretation_allowed = len(reasons) == 0
        else:
            # In non-strict mode, only block if no sufficient persons
            interpretation_allowed = len(sufficient_persons) > 0

        return interpretation_allowed, reasons

    def to_json(self, result: PipelineResult) -> str:
        """Export result as JSON."""
        data = {
            "folder": str(self.folder),
            "num_persons": len(result.person_nodes),
            "interpretation_allowed": result.interpretation_allowed,
            "rejection_reasons": result.rejection_reasons,
            "equilibrium": {
                "converged": result.equilibrium_converged,
                "iterations": result.equilibrium_iterations,
            },
            "persons": [
                {
                    "track_id": pn.track_id,
                    "coverage": pn.features.coverage_ratio,
                    "confidence": pn.features.overall_confidence,
                    "features": pn.features.to_feature_dict(),
                }
                for pn in result.person_nodes
            ],
        }

        if result.report:
            data["summary"] = result.report.summary

        return json.dumps(data, indent=2)
