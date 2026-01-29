"""Tests for report generation."""

from taocore_human.reports import ReportGenerator, AnalysisReport


class TestAnalysisReport:
    """Tests for AnalysisReport dataclass."""

    def test_create_report(self):
        """Test basic report creation."""
        report = AnalysisReport(
            interpretation_allowed=True,
            confidence_level="moderate",
            num_persons_analyzed=3,
            coverage_summary={"person_1": 0.8, "person_2": 0.6},
            summary="Test summary",
            observations=["Observation 1"],
            limitations=["Limitation 1"],
            recommendations=["Recommendation 1"],
        )

        assert report.interpretation_allowed
        assert report.confidence_level == "moderate"
        assert report.num_persons_analyzed == 3

    def test_report_has_required_fields(self):
        """Test that report has all required fields."""
        report = AnalysisReport(
            interpretation_allowed=False,
            confidence_level="insufficient",
            num_persons_analyzed=0,
            coverage_summary={},
            summary="No data",
            observations=[],
            limitations=["Not enough data"],
            recommendations=["Collect more data"],
        )

        assert hasattr(report, "interpretation_allowed")
        assert hasattr(report, "confidence_level")
        assert hasattr(report, "summary")
        assert hasattr(report, "observations")
        assert hasattr(report, "limitations")
        assert hasattr(report, "recommendations")


class TestReportLanguage:
    """Tests for uncertainty-aware language in reports."""

    def test_signal_phrases_exist(self):
        """Test that signal phrases are defined."""
        assert len(ReportGenerator.SIGNAL_PHRASES) > 0
        for phrase in ReportGenerator.SIGNAL_PHRASES:
            # Should not contain definitive language
            assert "definitely" not in phrase.lower()
            assert "certainly" not in phrase.lower()

    def test_uncertainty_phrases_exist(self):
        """Test that uncertainty phrases are defined."""
        assert len(ReportGenerator.UNCERTAINTY_PHRASES) > 0

    def test_refusal_phrases_exist(self):
        """Test that refusal phrases are defined."""
        assert len(ReportGenerator.REFUSAL_PHRASES) > 0
        for phrase in ReportGenerator.REFUSAL_PHRASES:
            # Refusal should be clear but not harsh
            assert len(phrase) > 10
