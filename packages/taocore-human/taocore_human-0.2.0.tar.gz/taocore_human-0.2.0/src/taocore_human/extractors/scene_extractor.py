"""
Scene classification extractor using CLIP.

Uses OpenAI's CLIP model for zero-shot scene classification.
Can identify scene types, indoor/outdoor, and general context.
"""

from typing import Dict, List, Optional
import numpy as np

from taocore_human.extractors.base import SceneExtractor, SceneFeatures


# Default scene categories for classification
DEFAULT_SCENE_CATEGORIES = [
    # Indoor locations
    "bedroom",
    "living room",
    "kitchen",
    "bathroom",
    "office",
    "restaurant",
    "cafe",
    "bar",
    "gym",
    "hospital",
    "classroom",
    "library",
    "store",
    "mall",
    # Outdoor locations
    "beach",
    "mountain",
    "forest",
    "park",
    "garden",
    "street",
    "city",
    "countryside",
    "lake",
    "river",
    "ocean",
    "desert",
    "snow",
    # Activities/contexts
    "wedding",
    "party",
    "concert",
    "sports event",
    "graduation",
    "birthday",
    # General
    "selfie",
    "group photo",
    "portrait",
    "landscape",
]

# Indoor vs outdoor categories
INDOOR_OUTDOOR_CATEGORIES = ["indoor", "outdoor"]

# Time of day categories
TIME_OF_DAY_CATEGORIES = ["daytime", "nighttime", "sunset", "sunrise"]


class CLIPSceneExtractor(SceneExtractor):
    """
    Scene classification using CLIP (Contrastive Language-Image Pre-training).

    Uses zero-shot classification to identify scene types from images.
    """

    def __init__(
        self,
        scene_categories: Optional[List[str]] = None,
        model_name: str = "openai/clip-vit-base-patch32",
    ):
        """
        Initialize CLIP scene extractor.

        Args:
            scene_categories: List of scene categories to classify.
                            If None, uses DEFAULT_SCENE_CATEGORIES.
            model_name: HuggingFace model name for CLIP.
        """
        self._scene_categories = scene_categories or DEFAULT_SCENE_CATEGORIES
        self._model_name = model_name
        self._model = None
        self._processor = None

    def _ensure_initialized(self):
        """Lazy initialization of CLIP model."""
        if self._model is None:
            try:
                from transformers import CLIPProcessor, CLIPModel
                import torch

                self._model = CLIPModel.from_pretrained(self._model_name)
                self._processor = CLIPProcessor.from_pretrained(self._model_name)
                self._torch = torch

                # Move to GPU if available
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
                self._model = self._model.to(self._device)
                self._model.eval()

            except ImportError:
                raise ImportError(
                    "transformers and torch are required for CLIPSceneExtractor. "
                    "Install with: pip install transformers torch"
                )

    @property
    def name(self) -> str:
        return "clip_scene"

    def extract(self, frame: np.ndarray) -> SceneFeatures:
        """
        Extract scene features from a frame.

        Args:
            frame: RGB image as numpy array (H, W, 3)

        Returns:
            SceneFeatures with scene classification results
        """
        self._ensure_initialized()

        from PIL import Image

        # Convert numpy array to PIL Image
        if frame.dtype != np.uint8:
            frame = (frame * 255).astype(np.uint8)
        pil_image = Image.fromarray(frame)

        # Classify scene types
        scene_probs = self._classify(pil_image, self._scene_categories)

        # Classify indoor/outdoor
        indoor_outdoor_probs = self._classify(pil_image, INDOOR_OUTDOOR_CATEGORIES)

        # Classify time of day
        time_probs = self._classify(pil_image, TIME_OF_DAY_CATEGORIES)

        # Get top scene
        top_scene = max(scene_probs.items(), key=lambda x: x[1])

        # Estimate illumination from time of day
        illumination = 0.7  # Default
        if time_probs.get("nighttime", 0) > 0.5:
            illumination = 0.3
        elif time_probs.get("sunset", 0) > 0.3 or time_probs.get("sunrise", 0) > 0.3:
            illumination = 0.5

        return SceneFeatures(
            confidence=top_scene[1],
            illumination=illumination,
            blur_level=None,  # CLIP doesn't estimate blur
            camera_motion=None,
            scene_type_probs={
                **scene_probs,
                "indoor_outdoor": indoor_outdoor_probs,
                "time_of_day": time_probs,
            },
        )

    def _classify(self, image, categories: List[str]) -> Dict[str, float]:
        """
        Classify image into given categories using CLIP.

        Returns:
            Dict mapping category names to probabilities
        """
        # Prepare text prompts
        text_prompts = [f"a photo of {cat}" for cat in categories]

        # Process inputs
        inputs = self._processor(
            text=text_prompts,
            images=image,
            return_tensors="pt",
            padding=True,
        )

        # Move to device
        inputs = {k: v.to(self._device) for k, v in inputs.items()}

        # Get predictions
        with self._torch.no_grad():
            outputs = self._model(**inputs)
            logits_per_image = outputs.logits_per_image
            probs = logits_per_image.softmax(dim=1)

        # Convert to dict
        probs_np = probs.cpu().numpy()[0]
        return {cat: float(prob) for cat, prob in zip(categories, probs_np)}

    def classify_custom(
        self, frame: np.ndarray, categories: List[str]
    ) -> Dict[str, float]:
        """
        Classify image using custom categories.

        Useful for specific classification tasks like:
        - ["happy moment", "sad moment", "neutral moment"]
        - ["formal event", "casual event"]
        - ["alone", "with others"]

        Args:
            frame: RGB image as numpy array
            categories: List of custom categories to classify

        Returns:
            Dict mapping category names to probabilities
        """
        self._ensure_initialized()

        from PIL import Image

        if frame.dtype != np.uint8:
            frame = (frame * 255).astype(np.uint8)
        pil_image = Image.fromarray(frame)

        return self._classify(pil_image, categories)
