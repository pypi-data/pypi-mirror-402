"""
MediaPipe-based feature extractors.

Uses Google's MediaPipe Tasks API for face detection and pose estimation.
Lightweight, runs on CPU, good accuracy for most use cases.
"""

import os
import urllib.request
from pathlib import Path
from typing import List, Optional
import numpy as np

from taocore_human.extractors.base import (
    FaceExtractor,
    PoseExtractor,
    FaceDetection,
    PoseDetection,
)

# Model URLs from MediaPipe
FACE_DETECTOR_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_detector/blaze_face_short_range/float16/1/blaze_face_short_range.tflite"
FACE_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/face_landmarker/face_landmarker/float16/1/face_landmarker.task"
POSE_LANDMARKER_MODEL_URL = "https://storage.googleapis.com/mediapipe-models/pose_landmarker/pose_landmarker_lite/float16/1/pose_landmarker_lite.task"


def get_model_path(model_url: str, cache_dir: Optional[str] = None) -> str:
    """Download model if not cached, return local path."""
    if cache_dir is None:
        cache_dir = os.path.join(Path.home(), ".cache", "taocore-human", "models")

    os.makedirs(cache_dir, exist_ok=True)

    model_name = os.path.basename(model_url)
    local_path = os.path.join(cache_dir, model_name)

    if not os.path.exists(local_path):
        print(f"Downloading model: {model_name}...")
        urllib.request.urlretrieve(model_url, local_path)
        print(f"Model saved to: {local_path}")

    return local_path


class MediaPipeFaceExtractor(FaceExtractor):
    """
    Face detection and landmark extraction using MediaPipe Tasks API.

    Detects faces and extracts 478 face mesh landmarks.
    Estimates head pose from landmarks.
    Does NOT estimate emotions (that would require a separate model).
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
        max_num_faces: int = 10,
    ):
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence
        self._max_num_faces = max_num_faces
        self._face_landmarker = None
        self._face_detector = None

    def _ensure_initialized(self):
        """Lazy initialization of MediaPipe."""
        if self._face_landmarker is None:
            try:
                import mediapipe as mp
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision

                # Download model if needed
                model_path = get_model_path(FACE_LANDMARKER_MODEL_URL)

                # Create face landmarker
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.FaceLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    num_faces=self._max_num_faces,
                    min_face_detection_confidence=self._min_detection_confidence,
                    min_face_presence_confidence=self._min_tracking_confidence,
                    min_tracking_confidence=self._min_tracking_confidence,
                    output_face_blendshapes=True,
                )
                self._face_landmarker = vision.FaceLandmarker.create_from_options(options)
                self._mp = mp

            except ImportError:
                raise ImportError(
                    "MediaPipe is required for MediaPipeFaceExtractor. "
                    "Install it with: pip install mediapipe"
                )

    @property
    def name(self) -> str:
        return "mediapipe_face"

    def extract(self, frame: np.ndarray) -> List[FaceDetection]:
        """
        Extract face detections from a frame.

        Args:
            frame: RGB image as numpy array (H, W, 3)

        Returns:
            List of FaceDetection objects
        """
        self._ensure_initialized()

        detections = []
        h, w = frame.shape[:2]

        # Convert to MediaPipe Image
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=frame)

        # Run face landmarker
        result = self._face_landmarker.detect(mp_image)

        if result.face_landmarks:
            for idx, face_landmarks in enumerate(result.face_landmarks):
                # Extract landmarks as Nx2 array (normalized coordinates)
                landmarks = np.array([
                    [lm.x, lm.y] for lm in face_landmarks
                ])

                # Calculate bounding box from landmarks
                x_coords = landmarks[:, 0]
                y_coords = landmarks[:, 1]
                x_min, x_max = x_coords.min(), x_coords.max()
                y_min, y_max = y_coords.min(), y_coords.max()
                bbox = (float(x_min), float(y_min), float(x_max - x_min), float(y_max - y_min))

                # Estimate head pose from key landmarks
                head_yaw, head_pitch, head_roll = self._estimate_head_pose(landmarks)

                # Extract all blendshapes and derive features
                blendshapes_dict = None
                smile_intensity = None
                left_eye_openness = None
                right_eye_openness = None
                mouth_openness = None
                jaw_open = None

                if result.face_blendshapes and idx < len(result.face_blendshapes):
                    blendshapes = result.face_blendshapes[idx]
                    blendshapes_dict = {bs.category_name: bs.score for bs in blendshapes}

                    # Smile: average of left and right mouth smile
                    smile_left = blendshapes_dict.get("mouthSmileLeft", 0)
                    smile_right = blendshapes_dict.get("mouthSmileRight", 0)
                    smile_intensity = (smile_left + smile_right) / 2

                    # Eye openness: inverse of blink (1 - blink = openness)
                    blink_left = blendshapes_dict.get("eyeBlinkLeft", 0)
                    blink_right = blendshapes_dict.get("eyeBlinkRight", 0)
                    left_eye_openness = 1.0 - blink_left
                    right_eye_openness = 1.0 - blink_right

                    # Mouth openness: combine jaw open and mouth open
                    jaw_open = blendshapes_dict.get("jawOpen", 0)
                    mouth_funnel = blendshapes_dict.get("mouthFunnel", 0)
                    mouth_openness = max(jaw_open, mouth_funnel)

                # Estimate gaze direction from iris landmarks
                gaze_direction = self._estimate_gaze_direction(landmarks)

                detection = FaceDetection(
                    confidence=0.9,  # MediaPipe doesn't provide per-face confidence in landmarker
                    bounding_box=bbox,
                    track_id=f"face_{idx}",
                    landmarks=landmarks,
                    head_yaw=head_yaw,
                    head_pitch=head_pitch,
                    head_roll=head_roll,
                    smile_intensity=smile_intensity,
                    valence=None,
                    arousal=None,
                    emotion_probs=None,
                    blendshapes=blendshapes_dict,
                    left_eye_openness=left_eye_openness,
                    right_eye_openness=right_eye_openness,
                    gaze_direction=gaze_direction,
                    mouth_openness=mouth_openness,
                    jaw_open=jaw_open,
                )
                detections.append(detection)

        return detections

    def _estimate_head_pose(
        self, landmarks: np.ndarray
    ) -> tuple[Optional[float], Optional[float], Optional[float]]:
        """
        Estimate head pose (yaw, pitch, roll) from face landmarks.
        Returns angles in radians.
        """
        try:
            # MediaPipe face mesh landmark indices (478 landmarks)
            # Nose tip: 1, Chin: 152, Left eye: 33, Right eye: 263
            nose = landmarks[1]
            chin = landmarks[152] if len(landmarks) > 152 else landmarks[-1]
            left_eye = landmarks[33] if len(landmarks) > 33 else landmarks[0]
            right_eye = landmarks[263] if len(landmarks) > 263 else landmarks[-1]

            # Yaw: rotation around vertical axis
            eye_center_x = (left_eye[0] + right_eye[0]) / 2
            yaw = (nose[0] - eye_center_x) * np.pi

            # Pitch: rotation around horizontal axis
            vertical_dist = chin[1] - nose[1]
            pitch = (0.5 - vertical_dist) * np.pi

            # Roll: rotation around depth axis
            eye_diff = right_eye - left_eye
            roll = float(np.arctan2(eye_diff[1], eye_diff[0]))

            return float(yaw), float(pitch), roll
        except Exception:
            return None, None, None

    def _estimate_gaze_direction(
        self, landmarks: np.ndarray
    ) -> Optional[tuple[float, float]]:
        """
        Estimate gaze direction from eye/iris landmarks.
        Returns (x, y) offset where (0, 0) is looking straight.
        Positive x = looking right, positive y = looking down.
        """
        try:
            # MediaPipe face mesh iris landmarks:
            # Left iris: 468-472 (center at 468)
            # Right iris: 473-477 (center at 473)
            # Left eye corners: inner=133, outer=33
            # Right eye corners: inner=362, outer=263

            if len(landmarks) < 478:  # Need full face mesh
                return None

            # Left eye
            left_iris_center = landmarks[468]
            left_eye_inner = landmarks[133]
            left_eye_outer = landmarks[33]
            left_eye_center = (left_eye_inner + left_eye_outer) / 2
            left_eye_width = abs(left_eye_outer[0] - left_eye_inner[0])

            # Right eye
            right_iris_center = landmarks[473]
            right_eye_inner = landmarks[362]
            right_eye_outer = landmarks[263]
            right_eye_center = (right_eye_inner + right_eye_outer) / 2
            right_eye_width = abs(right_eye_outer[0] - right_eye_inner[0])

            # Calculate iris offset from eye center, normalized by eye width
            if left_eye_width > 0 and right_eye_width > 0:
                left_gaze_x = (left_iris_center[0] - left_eye_center[0]) / left_eye_width
                right_gaze_x = (right_iris_center[0] - right_eye_center[0]) / right_eye_width

                # Average both eyes
                gaze_x = (left_gaze_x + right_gaze_x) / 2

                # Y direction (up/down) - use vertical offset
                left_eye_height = abs(landmarks[159][1] - landmarks[145][1])  # upper/lower lid
                right_eye_height = abs(landmarks[386][1] - landmarks[374][1])

                if left_eye_height > 0 and right_eye_height > 0:
                    left_gaze_y = (left_iris_center[1] - left_eye_center[1]) / left_eye_height
                    right_gaze_y = (right_iris_center[1] - right_eye_center[1]) / right_eye_height
                    gaze_y = (left_gaze_y + right_gaze_y) / 2
                else:
                    gaze_y = 0.0

                return (float(gaze_x), float(gaze_y))

            return None
        except Exception:
            return None


class MediaPipePoseExtractor(PoseExtractor):
    """
    Body pose estimation using MediaPipe Pose Landmarker.
    Detects 33 body landmarks.
    """

    def __init__(
        self,
        min_detection_confidence: float = 0.5,
        min_tracking_confidence: float = 0.5,
    ):
        self._min_detection_confidence = min_detection_confidence
        self._min_tracking_confidence = min_tracking_confidence
        self._pose_landmarker = None

    def _ensure_initialized(self):
        """Lazy initialization of MediaPipe."""
        if self._pose_landmarker is None:
            try:
                import mediapipe as mp
                from mediapipe.tasks import python
                from mediapipe.tasks.python import vision

                # Download model if needed
                model_path = get_model_path(POSE_LANDMARKER_MODEL_URL)

                # Create pose landmarker
                base_options = python.BaseOptions(model_asset_path=model_path)
                options = vision.PoseLandmarkerOptions(
                    base_options=base_options,
                    running_mode=vision.RunningMode.IMAGE,
                    min_pose_detection_confidence=self._min_detection_confidence,
                    min_tracking_confidence=self._min_tracking_confidence,
                )
                self._pose_landmarker = vision.PoseLandmarker.create_from_options(options)
                self._mp = mp

                # Landmark names
                self._landmark_names = [
                    'nose', 'left_eye_inner', 'left_eye', 'left_eye_outer',
                    'right_eye_inner', 'right_eye', 'right_eye_outer',
                    'left_ear', 'right_ear', 'mouth_left', 'mouth_right',
                    'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                    'left_wrist', 'right_wrist', 'left_pinky', 'right_pinky',
                    'left_index', 'right_index', 'left_thumb', 'right_thumb',
                    'left_hip', 'right_hip', 'left_knee', 'right_knee',
                    'left_ankle', 'right_ankle', 'left_heel', 'right_heel',
                    'left_foot_index', 'right_foot_index'
                ]

            except ImportError:
                raise ImportError(
                    "MediaPipe is required for MediaPipePoseExtractor. "
                    "Install it with: pip install mediapipe"
                )

    @property
    def name(self) -> str:
        return "mediapipe_pose"

    def extract(self, frame: np.ndarray) -> List[PoseDetection]:
        """
        Extract pose detections from a frame.
        """
        self._ensure_initialized()

        # Convert to MediaPipe Image
        mp_image = self._mp.Image(image_format=self._mp.ImageFormat.SRGB, data=frame)

        # Run pose landmarker
        result = self._pose_landmarker.detect(mp_image)

        if not result.pose_landmarks:
            return []

        detections = []
        for idx, pose_landmarks in enumerate(result.pose_landmarks):
            # Convert to keypoints dict
            keypoints = {}
            for i, name in enumerate(self._landmark_names):
                if i < len(pose_landmarks):
                    lm = pose_landmarks[i]
                    keypoints[name] = (lm.x, lm.y, lm.visibility if hasattr(lm, 'visibility') else 1.0)

            # Calculate bounding box
            visible_points = [(lm.x, lm.y) for lm in pose_landmarks]
            if visible_points:
                xs, ys = zip(*visible_points)
                bbox = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
            else:
                bbox = None

            # Estimate posture openness
            posture_openness = self._estimate_openness(keypoints)

            detection = PoseDetection(
                confidence=0.9,
                bounding_box=bbox,
                track_id=f"pose_{idx}",
                keypoints=keypoints,
                posture_openness=posture_openness,
                movement_energy=None,
            )
            detections.append(detection)

        return detections

    def _estimate_openness(self, keypoints: dict) -> Optional[float]:
        """Estimate posture openness from arm positions."""
        try:
            left_shoulder = keypoints.get('left_shoulder')
            right_shoulder = keypoints.get('right_shoulder')
            left_wrist = keypoints.get('left_wrist')
            right_wrist = keypoints.get('right_wrist')

            if not all([left_shoulder, right_shoulder, left_wrist, right_wrist]):
                return None

            shoulder_width = abs(right_shoulder[0] - left_shoulder[0])
            wrist_spread = abs(right_wrist[0] - left_wrist[0])

            if shoulder_width > 0:
                openness = min(1.0, wrist_spread / (shoulder_width * 2))
                return float(openness)
            return None
        except Exception:
            return None


class MediaPipeExtractor:
    """
    Combined MediaPipe extractor providing face and pose detection.

    Usage:
        extractor = MediaPipeExtractor()
        faces = extractor.face.extract(image)
        poses = extractor.pose.extract(image)
    """

    def __init__(
        self,
        face_min_confidence: float = 0.5,
        pose_min_confidence: float = 0.5,
        max_faces: int = 10,
    ):
        self.face = MediaPipeFaceExtractor(
            min_detection_confidence=face_min_confidence,
            max_num_faces=max_faces,
        )
        self.pose = MediaPipePoseExtractor(
            min_detection_confidence=pose_min_confidence,
        )
