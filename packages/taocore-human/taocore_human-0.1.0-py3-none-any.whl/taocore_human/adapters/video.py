"""
Video adapter for loading and processing video files.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Tuple, Union
import numpy as np


@dataclass
class VideoFrame:
    """A single video frame with metadata."""

    data: np.ndarray  # HxWxC uint8
    frame_index: int
    timestamp: float  # seconds

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]


@dataclass
class VideoMetadata:
    """Metadata about a video file."""

    path: Path
    duration: float  # seconds
    fps: float
    total_frames: int
    width: int
    height: int
    has_audio: bool = False


class VideoAdapter:
    """Load and process video files."""

    SUPPORTED_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".webm"}

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Video not found: {self.path}")
        if self.path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported video format: {self.path.suffix}")

        self._cap = None
        self._metadata: Optional[VideoMetadata] = None

    def _get_capture(self):
        """Get or create video capture object."""
        if self._cap is None:
            try:
                import cv2

                self._cap = cv2.VideoCapture(str(self.path))
                if not self._cap.isOpened():
                    raise ValueError(f"Failed to open video: {self.path}")
            except ImportError:
                raise ImportError("opencv-python is required for video processing")
        return self._cap

    @property
    def metadata(self) -> VideoMetadata:
        """Get video metadata."""
        if self._metadata is None:
            import cv2

            cap = self._get_capture()
            fps = cap.get(cv2.CAP_PROP_FPS)
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

            self._metadata = VideoMetadata(
                path=self.path,
                duration=total_frames / fps if fps > 0 else 0,
                fps=fps,
                total_frames=total_frames,
                width=width,
                height=height,
            )
        return self._metadata

    def __iter__(self) -> Iterator[VideoFrame]:
        """Iterate over all frames."""
        return self.iter_frames()

    def iter_frames(
        self,
        start_time: float = 0,
        end_time: Optional[float] = None,
        sample_fps: Optional[float] = None,
    ) -> Iterator[VideoFrame]:
        """
        Iterate over video frames.

        Args:
            start_time: Start time in seconds
            end_time: End time in seconds (None = end of video)
            sample_fps: Sample at this FPS (None = original FPS)
        """
        import cv2

        cap = self._get_capture()
        meta = self.metadata

        # Calculate frame range
        start_frame = int(start_time * meta.fps)
        end_frame = int(end_time * meta.fps) if end_time else meta.total_frames

        # Calculate frame step for sampling
        if sample_fps and sample_fps < meta.fps:
            frame_step = int(meta.fps / sample_fps)
        else:
            frame_step = 1

        cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)

        frame_idx = start_frame
        while frame_idx < end_frame:
            ret, frame = cap.read()
            if not ret:
                break

            # Convert BGR to RGB
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            timestamp = frame_idx / meta.fps

            yield VideoFrame(
                data=frame_rgb,
                frame_index=frame_idx,
                timestamp=timestamp,
            )

            # Skip frames if sampling
            if frame_step > 1:
                frame_idx += frame_step
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
            else:
                frame_idx += 1

    def get_frame(self, frame_index: int) -> VideoFrame:
        """Get a specific frame by index."""
        import cv2

        cap = self._get_capture()
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_index)

        ret, frame = cap.read()
        if not ret:
            raise ValueError(f"Failed to read frame {frame_index}")

        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        timestamp = frame_index / self.metadata.fps

        return VideoFrame(
            data=frame_rgb,
            frame_index=frame_index,
            timestamp=timestamp,
        )

    def get_windows(
        self,
        window_duration: float = 5.0,
        overlap: float = 0.0,
    ) -> Iterator[Tuple[float, float, List[VideoFrame]]]:
        """
        Get video in time windows.

        Args:
            window_duration: Duration of each window in seconds
            overlap: Overlap between windows in seconds

        Yields:
            (start_time, end_time, frames) for each window
        """
        meta = self.metadata
        step = window_duration - overlap
        current_time = 0

        while current_time < meta.duration:
            end_time = min(current_time + window_duration, meta.duration)
            frames = list(self.iter_frames(start_time=current_time, end_time=end_time))

            yield (current_time, end_time, frames)

            current_time += step

    def close(self):
        """Release video capture resources."""
        if self._cap is not None:
            self._cap.release()
            self._cap = None

    def __del__(self):
        self.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
