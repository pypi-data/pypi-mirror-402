"""
Report generation with carefully phrased, uncertainty-aware language.

All outputs use bounded claims:
- "signals suggest" not "this person is"
- "patterns observed" not "definitely happening"
- "interpretation ambiguous" when appropriate
"""

from taocore_human.reports.generator import ReportGenerator, AnalysisReport

__all__ = ["ReportGenerator", "AnalysisReport"]
