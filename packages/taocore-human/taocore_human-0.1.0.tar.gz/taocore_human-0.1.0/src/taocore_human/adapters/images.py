"""
Image adapters for loading and processing photos.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator, List, Optional, Union
import numpy as np


@dataclass
class ImageFrame:
    """A single image frame with metadata."""

    data: np.ndarray  # HxWxC uint8
    path: Path
    index: int

    @property
    def height(self) -> int:
        return self.data.shape[0]

    @property
    def width(self) -> int:
        return self.data.shape[1]

    @property
    def channels(self) -> int:
        return self.data.shape[2] if len(self.data.shape) > 2 else 1


class ImageAdapter:
    """Load and process a single image."""

    SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp", ".tiff"}

    def __init__(self, path: Union[str, Path]):
        self.path = Path(path)
        if not self.path.exists():
            raise FileNotFoundError(f"Image not found: {self.path}")
        if self.path.suffix.lower() not in self.SUPPORTED_EXTENSIONS:
            raise ValueError(f"Unsupported image format: {self.path.suffix}")

    def load(self) -> ImageFrame:
        """Load the image as a numpy array."""
        try:
            # Try PIL first (common, handles most formats)
            from PIL import Image

            img = Image.open(self.path).convert("RGB")
            data = np.array(img)
        except ImportError:
            # Fall back to opencv if available
            try:
                import cv2

                data = cv2.imread(str(self.path))
                if data is None:
                    raise ValueError(f"Failed to load image: {self.path}")
                data = cv2.cvtColor(data, cv2.COLOR_BGR2RGB)
            except ImportError:
                raise ImportError(
                    "Either PIL (pillow) or opencv-python is required for image loading"
                )

        return ImageFrame(data=data, path=self.path, index=0)


class ImageFolderAdapter:
    """Load and iterate over images in a folder."""

    def __init__(
        self,
        folder: Union[str, Path],
        extensions: Optional[set] = None,
        recursive: bool = False,
    ):
        self.folder = Path(folder)
        if not self.folder.is_dir():
            raise NotADirectoryError(f"Not a directory: {self.folder}")

        self.extensions = extensions or ImageAdapter.SUPPORTED_EXTENSIONS
        self.recursive = recursive
        self._image_paths: Optional[List[Path]] = None

    @property
    def image_paths(self) -> List[Path]:
        """Get sorted list of image paths."""
        if self._image_paths is None:
            if self.recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            paths = []
            for ext in self.extensions:
                paths.extend(self.folder.glob(f"{pattern}{ext}"))
                paths.extend(self.folder.glob(f"{pattern}{ext.upper()}"))

            self._image_paths = sorted(set(paths))

        return self._image_paths

    def __len__(self) -> int:
        return len(self.image_paths)

    def __iter__(self) -> Iterator[ImageFrame]:
        """Iterate over all images in the folder."""
        for i, path in enumerate(self.image_paths):
            adapter = ImageAdapter(path)
            frame = adapter.load()
            frame.index = i
            yield frame

    def load_all(self) -> List[ImageFrame]:
        """Load all images into memory. Use with caution for large folders."""
        return list(self)

    def sample(self, n: int, seed: Optional[int] = None) -> List[ImageFrame]:
        """Load a random sample of n images."""
        rng = np.random.default_rng(seed)
        paths = self.image_paths
        if n >= len(paths):
            return self.load_all()

        indices = rng.choice(len(paths), size=n, replace=False)
        indices = sorted(indices)

        frames = []
        for i in indices:
            adapter = ImageAdapter(paths[i])
            frame = adapter.load()
            frame.index = i
            frames.append(frame)

        return frames
