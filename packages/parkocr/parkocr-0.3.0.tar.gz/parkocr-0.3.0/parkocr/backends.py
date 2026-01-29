"""
Backend detection and abstraction for ParkOCR.

This module provides unified interfaces for OCR and object detection,
supporting both lite (ONNX) and full (PyTorch) backends.
"""

import logging
from abc import ABC, abstractmethod
from pathlib import Path

import cv2
import numpy as np

# Detect available backends
_HAS_EASYOCR = False
_HAS_RAPIDOCR = False
_HAS_ULTRALYTICS = False
_HAS_ONNXRUNTIME = False

try:
    import easyocr
    _HAS_EASYOCR = True
except ImportError:
    pass

try:
    from rapidocr_onnxruntime import RapidOCR
    _HAS_RAPIDOCR = True
except ImportError:
    pass

try:
    from ultralytics import YOLO
    _HAS_ULTRALYTICS = True
except ImportError:
    pass

try:
    import onnxruntime as ort
    _HAS_ONNXRUNTIME = True
except ImportError:
    pass


def get_available_backend() -> str:
    """
    Detect which backend is available.

    Returns:
        str: 'full' if PyTorch backend available, 'lite' if ONNX, 'none' if neither.
    """
    if _HAS_EASYOCR and _HAS_ULTRALYTICS:
        return "full"
    elif _HAS_RAPIDOCR and _HAS_ONNXRUNTIME:
        return "lite"
    elif _HAS_ULTRALYTICS:
        return "full"  # Has YOLO but not EasyOCR
    elif _HAS_ONNXRUNTIME:
        return "lite"  # Has ONNX but not RapidOCR
    return "none"


def check_backend_installed() -> None:
    """
    Check if at least one backend is installed and raise error if not.
    """
    backend = get_available_backend()
    if backend == "none":
        raise ImportError(
            "No backend installed. Install either:\n"
            "  pip install parkocr[lite]   # Lightweight ONNX backend (~90MB)\n"
            "  pip install parkocr[full]   # Full PyTorch backend (~950MB)"
        )


# =============================================================================
# OCR Backend Abstraction
# =============================================================================

class OCRBackend(ABC):
    """Abstract base class for OCR backends."""

    @abstractmethod
    def read(self, image: np.ndarray) -> list[tuple[list, str, float]]:
        """
        Read text from image.

        Args:
            image: Grayscale or BGR image as numpy array.

        Returns:
            List of (bbox, text, confidence) tuples.
            bbox is a list of 4 points [(x1,y1), (x2,y2), (x3,y3), (x4,y4)]
        """
        pass


class EasyOCRBackend(OCRBackend):
    """EasyOCR backend (PyTorch-based)."""

    def __init__(self, langs: list[str] = None):
        if not _HAS_EASYOCR:
            raise ImportError("EasyOCR not installed. Run: pip install parkocr[full]")
        langs = langs or ["en"]
        self._reader = easyocr.Reader(langs, verbose=False)

    def read(self, image: np.ndarray) -> list[tuple[list, str, float]]:
        results = self._reader.readtext(image, detail=1)
        return [(bbox, text, conf) for bbox, text, conf in results]


class RapidOCRBackend(OCRBackend):
    """RapidOCR backend (ONNX-based)."""

    def __init__(self, langs: list[str] = None):
        if not _HAS_RAPIDOCR:
            raise ImportError("RapidOCR not installed. Run: pip install parkocr[lite]")
        # RapidOCR doesn't use langs parameter the same way
        self._reader = RapidOCR()

    def read(self, image: np.ndarray) -> list[tuple[list, str, float]]:
        result, _ = self._reader(image)
        if result is None:
            return []

        # Convert RapidOCR format to EasyOCR-compatible format
        # RapidOCR returns: [[bbox, text, score], ...]
        # bbox is [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
        output = []
        for item in result:
            bbox = item[0]  # Already in correct format
            text = item[1]
            conf = item[2]
            output.append((bbox, text, conf))
        return output


def create_ocr_backend(langs: list[str] = None, prefer: str = None) -> OCRBackend:
    """
    Create OCR backend based on available libraries.

    Args:
        langs: Languages for OCR.
        prefer: Preferred backend ('lite' or 'full'). Auto-detects if None.

    Returns:
        OCRBackend instance.
    """
    if prefer == "lite" and _HAS_RAPIDOCR:
        return RapidOCRBackend(langs)
    elif prefer == "full" and _HAS_EASYOCR:
        return EasyOCRBackend(langs)
    elif _HAS_EASYOCR:
        logging.debug("Using EasyOCR backend (full)")
        return EasyOCRBackend(langs)
    elif _HAS_RAPIDOCR:
        logging.debug("Using RapidOCR backend (lite)")
        return RapidOCRBackend(langs)
    else:
        raise ImportError(
            "No OCR backend available. Install either:\n"
            "  pip install parkocr[lite]   # RapidOCR (ONNX)\n"
            "  pip install parkocr[full]   # EasyOCR (PyTorch)"
        )


# =============================================================================
# YOLO Backend Abstraction
# =============================================================================

YOLO_MODELS = {
    0: "yolov8n",  # nano
    1: "yolov8s",  # small
    2: "yolov8m",  # medium
    3: "yolov8l",  # large
    4: "yolov8x",  # xlarge
}


class YOLOBackend(ABC):
    """Abstract base class for YOLO backends."""

    @abstractmethod
    def detect(self, image: np.ndarray) -> list[tuple[int, int, int, int, float, int]]:
        """
        Detect objects in image.

        Args:
            image: BGR image as numpy array.

        Returns:
            List of (x1, y1, x2, y2, confidence, class_id) tuples.
        """
        pass


class UltralyticsYOLOBackend(YOLOBackend):
    """Ultralytics YOLO backend (PyTorch-based)."""

    def __init__(self, model_size: int = 0):
        if not _HAS_ULTRALYTICS:
            raise ImportError("Ultralytics not installed. Run: pip install parkocr[full]")

        import os
        os.environ["YOLO_VERBOSE"] = "False"
        from ultralytics import YOLO
        from ultralytics.engine.results import Results
        Results.print = lambda self: None
        logging.getLogger("ultralytics").setLevel(logging.WARNING)

        model_name = f"{YOLO_MODELS.get(model_size, 'yolov8n')}.pt"
        self._model = YOLO(model_name, verbose=False)

    def detect(self, image: np.ndarray) -> list[tuple[int, int, int, int, float, int]]:
        results = self._model(image, verbose=False)
        r = results[0]

        detections = []
        for *box, conf, cls in r.boxes.data.cpu().numpy():
            x1, y1, x2, y2 = map(int, box)
            detections.append((x1, y1, x2, y2, float(conf), int(cls)))

        return detections


class ONNXYOLOBackend(YOLOBackend):
    """ONNX Runtime YOLO backend (lightweight)."""

    def __init__(self, model_size: int = 0):
        if not _HAS_ONNXRUNTIME:
            raise ImportError("ONNX Runtime not installed. Run: pip install parkocr[lite]")

        model_name = YOLO_MODELS.get(model_size, "yolov8n")
        model_path = self._get_or_download_model(model_name)

        self._session = ort.InferenceSession(
            str(model_path),
            providers=['CPUExecutionProvider']
        )
        self._input_name = self._session.get_inputs()[0].name
        self._input_shape = self._session.get_inputs()[0].shape  # [1, 3, 640, 640]
        self._input_size = (self._input_shape[2], self._input_shape[3])

    def _get_or_download_model(self, model_name: str) -> Path:
        """Get ONNX model path from bundled models."""
        # Check in package data directory
        pkg_dir = Path(__file__).parent
        models_dir = pkg_dir / "models"

        model_path = models_dir / f"{model_name}.onnx"

        if not model_path.exists():
            # List available models
            available = []
            if models_dir.exists():
                available = [f.stem for f in models_dir.glob("*.onnx")]

            if available:
                raise FileNotFoundError(
                    f"Model '{model_name}' not found.\n"
                    f"Available models: {available}\n"
                    f"Use model_size=0 for 'yolov8n' (nano, recommended for lite version)."
                )
            else:
                raise FileNotFoundError(
                    f"No ONNX models found in {models_dir}.\n"
                    "The lite version requires pre-bundled ONNX models.\n"
                    "Try reinstalling: pip install --force-reinstall parkocr[lite]"
                )

        logging.debug(f"Using ONNX model: {model_path}")
        return model_path

    def _preprocess(self, image: np.ndarray) -> tuple[np.ndarray, float, float, int, int]:
        """Preprocess image for YOLO inference."""
        orig_h, orig_w = image.shape[:2]
        target_h, target_w = self._input_size

        # Calculate scale to fit image in input size
        scale = min(target_w / orig_w, target_h / orig_h)
        new_w = int(orig_w * scale)
        new_h = int(orig_h * scale)

        # Resize image
        resized = cv2.resize(image, (new_w, new_h))

        # Pad to target size
        pad_w = (target_w - new_w) // 2
        pad_h = (target_h - new_h) // 2

        padded = np.full((target_h, target_w, 3), 114, dtype=np.uint8)
        padded[pad_h:pad_h+new_h, pad_w:pad_w+new_w] = resized

        # Convert to float and normalize
        blob = padded.astype(np.float32) / 255.0
        blob = blob.transpose(2, 0, 1)  # HWC -> CHW
        blob = np.expand_dims(blob, 0)  # Add batch dimension

        return blob, scale, scale, pad_w, pad_h

    def _postprocess(
        self,
        outputs: np.ndarray,
        scale_x: float,
        scale_y: float,
        pad_x: int,
        pad_y: int,
        conf_thresh: float = 0.25,
        iou_thresh: float = 0.45
    ) -> list[tuple[int, int, int, int, float, int]]:
        """Postprocess YOLO outputs with NMS."""
        # YOLOv8 output shape: [1, 84, 8400] -> transpose to [8400, 84]
        predictions = outputs[0].transpose(1, 0)

        # Extract boxes and scores
        # First 4 values are box coordinates (cx, cy, w, h)
        # Remaining 80 values are class scores
        boxes = predictions[:, :4]
        scores = predictions[:, 4:]

        # Get max score and class for each detection
        max_scores = np.max(scores, axis=1)
        class_ids = np.argmax(scores, axis=1)

        # Filter by confidence
        mask = max_scores > conf_thresh
        boxes = boxes[mask]
        max_scores = max_scores[mask]
        class_ids = class_ids[mask]

        if len(boxes) == 0:
            return []

        # Convert from center format to corner format
        cx, cy, w, h = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        x1 = cx - w / 2
        y1 = cy - h / 2
        x2 = cx + w / 2
        y2 = cy + h / 2

        # Remove padding and scale back to original image
        x1 = (x1 - pad_x) / scale_x
        y1 = (y1 - pad_y) / scale_y
        x2 = (x2 - pad_x) / scale_x
        y2 = (y2 - pad_y) / scale_y

        # Apply NMS
        boxes_for_nms = np.stack([x1, y1, x2, y2], axis=1)
        indices = self._nms(boxes_for_nms, max_scores, iou_thresh)

        # Build result
        detections = []
        for i in indices:
            detections.append((
                int(x1[i]), int(y1[i]), int(x2[i]), int(y2[i]),
                float(max_scores[i]), int(class_ids[i])
            ))

        return detections

    def _nms(self, boxes: np.ndarray, scores: np.ndarray, iou_thresh: float) -> list[int]:
        """Non-maximum suppression."""
        x1, y1, x2, y2 = boxes[:, 0], boxes[:, 1], boxes[:, 2], boxes[:, 3]
        areas = (x2 - x1) * (y2 - y1)

        order = scores.argsort()[::-1]
        keep = []

        while len(order) > 0:
            i = order[0]
            keep.append(i)

            if len(order) == 1:
                break

            # Compute IoU with remaining boxes
            xx1 = np.maximum(x1[i], x1[order[1:]])
            yy1 = np.maximum(y1[i], y1[order[1:]])
            xx2 = np.minimum(x2[i], x2[order[1:]])
            yy2 = np.minimum(y2[i], y2[order[1:]])

            inter_w = np.maximum(0, xx2 - xx1)
            inter_h = np.maximum(0, yy2 - yy1)
            inter_area = inter_w * inter_h

            iou = inter_area / (areas[i] + areas[order[1:]] - inter_area)

            # Keep boxes with IoU below threshold
            mask = iou <= iou_thresh
            order = order[1:][mask]

        return keep

    def detect(self, image: np.ndarray) -> list[tuple[int, int, int, int, float, int]]:
        blob, scale_x, scale_y, pad_x, pad_y = self._preprocess(image)
        outputs = self._session.run(None, {self._input_name: blob})[0]
        return self._postprocess(outputs, scale_x, scale_y, pad_x, pad_y)


def create_yolo_backend(model_size: int = 0, prefer: str = None) -> YOLOBackend:
    """
    Create YOLO backend based on available libraries.

    Args:
        model_size: Model size index (0-4, nano to xlarge).
        prefer: Preferred backend ('lite' or 'full'). Auto-detects if None.

    Returns:
        YOLOBackend instance.
    """
    if prefer == "lite" and _HAS_ONNXRUNTIME:
        return ONNXYOLOBackend(model_size)
    elif prefer == "full" and _HAS_ULTRALYTICS:
        return UltralyticsYOLOBackend(model_size)
    elif _HAS_ULTRALYTICS:
        logging.debug("Using Ultralytics YOLO backend (full)")
        return UltralyticsYOLOBackend(model_size)
    elif _HAS_ONNXRUNTIME:
        logging.debug("Using ONNX YOLO backend (lite)")
        return ONNXYOLOBackend(model_size)
    else:
        raise ImportError(
            "No YOLO backend available. Install either:\n"
            "  pip install parkocr[lite]   # ONNX Runtime\n"
            "  pip install parkocr[full]   # Ultralytics"
        )
