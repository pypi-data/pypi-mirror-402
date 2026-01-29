"""
taocore-human: Image & Video Pipelines for Human Behavior and Emotion Signals

This package processes photos/videos into interpretable, bounded claims about
behavior/emotion signals and interaction dynamics, using TaoCore's framework.

Key principles:
- Outputs are "signals" and "patterns", not definitive judgments
- Uncertainty is always explicit
- Non-convergence is meaningful (signals conflict or are ambiguous)
- Conservative by default for human/emotion inference
"""

from taocore_human.nodes import PersonNode, FrameNode, WindowNode, ContextNode
from taocore_human.pipeline import PhotoFolderPipeline, VideoInteractionPipeline

__version__ = "0.1.0"

__all__ = [
    "PersonNode",
    "FrameNode",
    "WindowNode",
    "ContextNode",
    "PhotoFolderPipeline",
    "VideoInteractionPipeline",
]
