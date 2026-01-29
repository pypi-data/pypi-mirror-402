"""
End-to-end pipelines for processing media.

These orchestrate the full flow from media → features → graphs → metrics → reports.
"""

from taocore_human.pipeline.photo_folder import PhotoFolderPipeline
from taocore_human.pipeline.video_interaction import VideoInteractionPipeline

__all__ = ["PhotoFolderPipeline", "VideoInteractionPipeline"]
