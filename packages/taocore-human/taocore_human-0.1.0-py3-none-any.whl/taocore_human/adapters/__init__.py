"""
Adapters for loading and processing media.

These handle the conversion from raw media (images, video) into
frames that can be processed by feature extractors.
"""

from taocore_human.adapters.images import ImageAdapter, ImageFolderAdapter
from taocore_human.adapters.video import VideoAdapter

__all__ = ["ImageAdapter", "ImageFolderAdapter", "VideoAdapter"]
