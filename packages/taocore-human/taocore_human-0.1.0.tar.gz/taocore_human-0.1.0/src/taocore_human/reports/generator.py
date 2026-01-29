"""
Report generation with uncertainty-aware, carefully phrased language.

Key principles:
- Use "signals" and "patterns", not definitive statements
- Always acknowledge uncertainty and limitations
- Refuse to over-interpret when data quality is low
- Make the basis for claims explicit
"""

from dataclasses import dataclass
from typing import Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from taocore_human.pipeline.photo_folder import PipelineResult, PipelineConfig
    from taocore_human.pipeline.video_interaction import VideoResult, VideoPipelineConfig


@dataclass
class AnalysisReport:
    """Structured analysis report."""

    # Machine-readable
    interpretation_allowed: bool
    confidence_level: str  # "high", "moderate", "low", "insufficient"
    num_persons_analyzed: int
    coverage_summary: Dict[str, float]  # track_id -> coverage

    # Human-readable
    summary: str
    observations: List[str]
    limitations: List[str]
    recommendations: List[str]

    # Structural findings (always available)
    structural_summary: Optional[str] = None

    # Emotional/behavioral findings (only if allowed)
    behavioral_summary: Optional[str] = None


class ReportGenerator:
    """Generate carefully-phrased reports from pipeline results."""

    # Phrasing templates that emphasize uncertainty
    SIGNAL_PHRASES = [
        "Observed signals suggest",
        "Patterns in the data indicate",
        "The available evidence points toward",
        "Based on detected features,",
    ]

    UNCERTAINTY_PHRASES = [
        "with moderate confidence",
        "though uncertainty remains",
        "subject to the limitations noted below",
        "pending further observation",
    ]

    REFUSAL_PHRASES = [
        "Insufficient data for reliable interpretation.",
        "Signal quality too low for meaningful analysis.",
        "Conflicting patterns prevent clear interpretation.",
        "System recommends human review before drawing conclusions.",
    ]

    @classmethod
    def generate(cls, result: "PipelineResult", config: "PipelineConfig") -> AnalysisReport:
        """Generate report for photo folder analysis."""
        # Determine confidence level
        if not result.interpretation_allowed:
            confidence = "insufficient"
        elif result.equilibrium_converged and len(result.person_nodes) >= 2:
            avg_coverage = sum(
                pn.features.coverage_ratio for pn in result.person_nodes
            ) / len(result.person_nodes)
            if avg_coverage > 0.6:
                confidence = "moderate"
            else:
                confidence = "low"
        else:
            confidence = "low"

        # Build coverage summary
        coverage_summary = {
            pn.track_id: pn.features.coverage_ratio for pn in result.person_nodes
        }

        # Generate observations
        observations = cls._generate_observations(result)

        # Generate limitations
        limitations = cls._generate_limitations(result, config)

        # Generate summary
        if result.interpretation_allowed:
            summary = cls._generate_allowed_summary(result, confidence)
        else:
            summary = cls._generate_refused_summary(result)

        # Structural summary (always available if we have data)
        structural_summary = cls._generate_structural_summary(result)

        # Behavioral summary (only if allowed)
        behavioral_summary = None
        if result.interpretation_allowed and confidence != "insufficient":
            behavioral_summary = cls._generate_behavioral_summary(result)

        return AnalysisReport(
            interpretation_allowed=result.interpretation_allowed,
            confidence_level=confidence,
            num_persons_analyzed=len(result.person_nodes),
            coverage_summary=coverage_summary,
            summary=summary,
            observations=observations,
            limitations=limitations,
            recommendations=cls._generate_recommendations(result, confidence),
            structural_summary=structural_summary,
            behavioral_summary=behavioral_summary,
        )

    @classmethod
    def generate_video(
        cls, result: "VideoResult", config: "VideoPipelineConfig"
    ) -> AnalysisReport:
        """Generate report for video analysis."""
        # Similar logic adapted for video
        if not result.interpretation_allowed:
            confidence = "insufficient"
        elif result.equilibrium_converged:
            confidence = "moderate"
        else:
            confidence = "low"

        coverage_summary = {
            pn.track_id: pn.features.coverage_ratio for pn in result.person_nodes
        }

        observations = cls._generate_video_observations(result)
        limitations = cls._generate_video_limitations(result, config)

        if result.interpretation_allowed:
            summary = cls._generate_video_allowed_summary(result, confidence)
        else:
            summary = cls._generate_refused_summary_video(result)

        structural_summary = cls._generate_video_structural_summary(result)

        behavioral_summary = None
        if result.interpretation_allowed and confidence != "insufficient":
            behavioral_summary = cls._generate_video_behavioral_summary(result)

        return AnalysisReport(
            interpretation_allowed=result.interpretation_allowed,
            confidence_level=confidence,
            num_persons_analyzed=len(result.person_nodes),
            coverage_summary=coverage_summary,
            summary=summary,
            observations=observations,
            limitations=limitations,
            recommendations=cls._generate_video_recommendations(result, confidence),
            structural_summary=structural_summary,
            behavioral_summary=behavioral_summary,
        )

    @classmethod
    def _generate_observations(cls, result: "PipelineResult") -> List[str]:
        """Generate list of observations from photo analysis."""
        obs = []

        obs.append(f"Analyzed {len(result.person_nodes)} tracked individuals across images.")

        if result.equilibrium_converged:
            obs.append(
                f"Equilibrium analysis converged after {result.equilibrium_iterations} iterations, "
                "suggesting stable signal patterns."
            )
        else:
            obs.append(
                "Equilibrium analysis did not converge, indicating potentially "
                "conflicting or unstable signal patterns."
            )

        # Hub observations
        if result.hub_metrics:
            top_hubs = result.hub_metrics.get("top_hubs", [])
            if top_hubs:
                obs.append(
                    f"Structural analysis identifies {len(top_hubs)} hub node(s) "
                    "with high connectivity (structural importance, not behavioral judgment)."
                )

        # Cluster observations
        if result.cluster_metrics:
            num_clusters = result.cluster_metrics.get("num_clusters", 0)
            if num_clusters > 1:
                obs.append(
                    f"Detected {num_clusters} potential subgroups based on "
                    "co-occurrence patterns."
                )

        return obs

    @classmethod
    def _generate_limitations(
        cls, result: "PipelineResult", config: "PipelineConfig"
    ) -> List[str]:
        """Generate list of limitations."""
        lims = []

        # Always include general limitations
        lims.append(
            "Expression and emotion signals are probabilistic estimates, "
            "not ground truth about internal states."
        )

        # Specific limitations from result
        for reason in result.rejection_reasons:
            lims.append(reason)

        # Context limitations
        if result.context_node and result.context_node.should_reduce_confidence():
            lims.append(
                "Scene conditions (lighting, image quality) may affect detection accuracy."
            )

        # Coverage limitations
        low_coverage = [
            pn.track_id
            for pn in result.person_nodes
            if pn.features.coverage_ratio < config.min_coverage
        ]
        if low_coverage:
            lims.append(
                f"{len(low_coverage)} individual(s) have low coverage and "
                "should be interpreted with extra caution."
            )

        return lims

    @classmethod
    def _generate_allowed_summary(cls, result: "PipelineResult", confidence: str) -> str:
        """Generate summary when interpretation is allowed."""
        parts = []

        parts.append(
            f"Analysis of {len(result.person_nodes)} individuals completed "
            f"with {confidence} confidence."
        )

        if result.equilibrium_converged:
            parts.append("Signal patterns show convergent stability.")
        else:
            parts.append("Signal patterns show some variability.")

        parts.append(
            "See observations below for structural patterns. "
            "Behavioral interpretations should be treated as hypotheses, not conclusions."
        )

        return " ".join(parts)

    @classmethod
    def _generate_refused_summary(cls, result: "PipelineResult") -> str:
        """Generate summary when interpretation is refused."""
        reasons = result.rejection_reasons[:2]  # Top 2 reasons
        reason_text = "; ".join(reasons) if reasons else "insufficient data quality"

        return (
            f"Interpretation declined due to: {reason_text}. "
            "Structural metrics (clusters, hubs) may still provide useful patterns. "
            "Behavioral/emotional interpretations are not recommended for this data."
        )

    @classmethod
    def _generate_structural_summary(cls, result: "PipelineResult") -> Optional[str]:
        """Generate structural-only summary (always safe to report)."""
        if not result.person_nodes:
            return None

        parts = []
        parts.append(f"Graph contains {len(result.person_nodes)} nodes.")

        if result.hub_metrics:
            parts.append("Hub analysis complete.")

        if result.cluster_metrics:
            num = result.cluster_metrics.get("num_clusters", 1)
            parts.append(f"Identified {num} cluster(s).")

        return " ".join(parts)

    @classmethod
    def _generate_behavioral_summary(cls, result: "PipelineResult") -> Optional[str]:
        """Generate behavioral summary (only when interpretation allowed)."""
        if not result.interpretation_allowed:
            return None

        # Aggregate behavioral signals
        valences = [
            pn.features.expression_valence_mean
            for pn in result.person_nodes
            if pn.features.expression_valence_mean is not None
        ]

        if not valences:
            return "Insufficient expression data for behavioral summary."

        import numpy as np

        avg_valence = np.mean(valences)

        if avg_valence > 0.3:
            tone = "generally positive valence signals"
        elif avg_valence < -0.3:
            tone = "generally negative valence signals"
        else:
            tone = "mixed or neutral valence signals"

        return (
            f"Observed signals suggest {tone} across the analyzed individuals. "
            "This reflects detected expression patterns, not confirmed emotional states."
        )

    @classmethod
    def _generate_recommendations(cls, result: "PipelineResult", confidence: str) -> List[str]:
        """Generate recommendations."""
        recs = []

        if confidence == "insufficient":
            recs.append("Consider collecting more data or using higher-quality images.")
            recs.append("Review rejection reasons before drawing any conclusions.")
        elif confidence == "low":
            recs.append("Treat all findings as preliminary hypotheses.")
            recs.append("Human review recommended before any decisions based on this analysis.")
        else:
            recs.append("Findings may inform further investigation but should not be treated as definitive.")

        recs.append("Never use these signals for high-stakes decisions without human oversight.")

        return recs

    # Video-specific methods follow similar patterns

    @classmethod
    def _generate_video_observations(cls, result: "VideoResult") -> List[str]:
        obs = []
        obs.append(
            f"Analyzed {len(result.window_nodes)} time windows "
            f"containing {len(result.person_nodes)} tracked individuals."
        )

        patterns = result.temporal_patterns
        if "overall_arousal_trend" in patterns:
            trend = patterns["overall_arousal_trend"]
            if trend > 0.1:
                obs.append("Arousal signals show increasing trend over time.")
            elif trend < -0.1:
                obs.append("Arousal signals show decreasing trend over time.")
            else:
                obs.append("Arousal signals remain relatively stable over time.")

        if result.flow_metrics:
            obs.append("Flow analysis completed across time windows.")

        return obs

    @classmethod
    def _generate_video_limitations(
        cls, result: "VideoResult", config: "VideoPipelineConfig"
    ) -> List[str]:
        lims = [
            "Video analysis aggregates across time windows; momentary variations may be smoothed.",
            "Tracking may lose individuals during occlusions or rapid movement.",
        ]
        lims.extend(result.rejection_reasons)
        return lims

    @classmethod
    def _generate_video_allowed_summary(
        cls, result: "VideoResult", confidence: str
    ) -> str:
        return (
            f"Video analysis of {len(result.person_nodes)} individuals across "
            f"{len(result.window_nodes)} windows completed with {confidence} confidence. "
            "Temporal patterns have been extracted. See observations for details."
        )

    @classmethod
    def _generate_refused_summary_video(cls, result: "VideoResult") -> str:
        return (
            "Interpretation declined for this video. "
            f"Reasons: {'; '.join(result.rejection_reasons[:2])}. "
            "Structural and temporal metrics may still be informative."
        )

    @classmethod
    def _generate_video_structural_summary(cls, result: "VideoResult") -> Optional[str]:
        if not result.window_nodes:
            return None
        return (
            f"Processed {len(result.window_nodes)} time windows. "
            f"Aggregated graph contains {len(result.person_nodes)} person nodes."
        )

    @classmethod
    def _generate_video_behavioral_summary(cls, result: "VideoResult") -> Optional[str]:
        if not result.interpretation_allowed:
            return None

        patterns = result.temporal_patterns
        parts = []

        if "overall_valence_trend" in patterns:
            trend = patterns["overall_valence_trend"]
            if abs(trend) > 0.1:
                direction = "increasing" if trend > 0 else "decreasing"
                parts.append(f"Group valence signals show {direction} trend.")

        if "valence_volatility" in patterns:
            vol = patterns["valence_volatility"]
            if vol > 0.3:
                parts.append("High variability in emotional signals across windows.")

        if not parts:
            parts.append("No strong temporal trends detected in behavioral signals.")

        return " ".join(parts) + " These are observed patterns, not confirmed states."

    @classmethod
    def _generate_video_recommendations(
        cls, result: "VideoResult", confidence: str
    ) -> List[str]:
        recs = []
        if confidence in ("insufficient", "low"):
            recs.append("Consider longer video or more controlled recording conditions.")
        recs.append("Temporal patterns should be validated with additional context.")
        recs.append("Never use these signals for high-stakes decisions without human oversight.")
        return recs
