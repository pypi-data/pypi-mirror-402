import os
import re
import cv2
import time
import logging
import numpy as np
import threading
from datetime import datetime

from .backends import (
    check_backend_installed,
    create_ocr_backend,
    create_yolo_backend,
    get_available_backend,
)

_PLATE_RE = re.compile(r"^[A-Z]{3}[0-9][0-9A-Z][0-9]{2}$")


class Detector:
    """
    License plate reader using YOLO to locate regions and OCR to read the text.

    Supports two backends:
        - 'lite': ONNX Runtime + RapidOCR (~90MB install)
        - 'full': PyTorch + EasyOCR (~950MB install)

    Features:
        - Filters by ROI (quadrant) defined with frame coordinates (x1, y1, x2, y2)
        - `headless=True`: runs without creating a window or drawing overlays
        - Prevents freezing on the same consecutively repeated plate
        - Optional FIFO output for inter-process communication
        - Optional screenshot saving ("full" = whole frame, "roi" = only ROI, None = disabled)
        - Async processing with threading to prevent blocking
        - Camera buffer clearing to reduce latency
        - Frame downscaling for faster inference

    Args:
        rtsp_url (str): The RTSP URL or video source (e.g., RTSP stream, file path, webcam index).
        model_size (int, optional): Index of YOLO model size to use (0-4: nano to xlarge).
        conf_thresh (float, optional): Minimum YOLO detection confidence threshold.
        roi (tuple[int, int, int, int] | None, optional): Region of interest as (x1, y1, x2, y2).
        headless (bool, optional): If True, disables window display and overlays.
        window_size (tuple[int, int], optional): Display window size (width, height).
        process_interval_s (float, optional): Seconds between detection cycles.
        freeze_seconds (float, optional): Seconds to display detection result (non-blocking).
        ocr_langs (list[str], optional): Languages to use for OCR.
        on_detect (callable, optional): Callback invoked with the detected plate.
        min_ocr_conf (float, optional): Minimum OCR confidence required to accept text.
        fifo_output (str | None, optional): Path to FIFO file. If set, detected plates will be written there.
        screenshot (str | None, optional): Screenshot mode.
            None = disabled,
            "full" = save whole frame,
            "roi" = save only the ROI region.
        inference_scale (float, optional): Scale factor for frame downscaling before YOLO (0.0-1.0).
            Lower values = faster but less accurate. Default 0.5 (50% size).
        buffer_clear_frames (int, optional): Number of frames to skip from camera buffer before processing.
            Helps reduce latency. Default 2.
        enable_performance_logging (bool, optional): Enable detailed performance timing logs.
        backend (str | None, optional): Force specific backend ('lite' or 'full').
            If None, auto-detects based on installed packages.
    """

    def __init__(
        self,
        rtsp_url: str,
        model_size: int = 0,
        conf_thresh: float = 0.5,
        roi: tuple[int, int, int, int] | None = None,
        headless: bool = False,
        window_size: tuple[int, int] = (1280, 720),
        process_interval_s: float = 1.0,
        freeze_seconds: float = 0.5,
        ocr_langs: list[str] = None,
        on_detect=None,
        min_ocr_conf: float = 0.30,
        fifo_output: str | None = None,
        screenshot: str | None = None,
        inference_scale: float = 0.5,
        buffer_clear_frames: int = 2,
        enable_performance_logging: bool = False,
        backend: str | None = None
    ):
        # Check backend availability
        check_backend_installed()

        self.rtsp_url = rtsp_url
        self.conf_thresh = conf_thresh
        self.roi = roi
        self.headless = headless
        self.window_width, self.window_height = window_size
        self.process_interval_s = process_interval_s
        self.freeze_seconds = freeze_seconds
        self.on_detect = on_detect
        self.min_ocr_conf = min_ocr_conf
        self.fifo_output = fifo_output
        self.screenshot = screenshot
        self.inference_scale = max(0.1, min(1.0, inference_scale))
        self.buffer_clear_frames = max(0, buffer_clear_frames)
        self.enable_performance_logging = enable_performance_logging
        self.backend = backend or get_available_backend()

        if self.screenshot not in (None, "full", "roi"):
            raise ValueError("screenshot must be None, 'full', or 'roi'")
        if self.screenshot is not None:
            os.makedirs("plates", exist_ok=True)
        if self.fifo_output and not os.path.exists(self.fifo_output):
            os.mkfifo(self.fifo_output)

        # Initialize backends
        ocr_langs = ocr_langs or ["en"]
        self._yolo = create_yolo_backend(model_size, prefer=self.backend)
        self._ocr = create_ocr_backend(ocr_langs, prefer=self.backend)

        logging.info(f"ParkOCR initialized with '{self.backend}' backend")

        self._last_process_time = 0.0
        self._last_plate = None

        # Threading state
        self._processing_lock = threading.Lock()
        self._is_processing = False
        self._detection_result = None
        self._detection_frame = None
        self._detection_timestamp = 0.0

    def _open_fifo(self):
        if not self.fifo_output:
            return None
        if not os.path.exists(self.fifo_output):
            os.mkfifo(self.fifo_output)
        try:
            return os.open(self.fifo_output, os.O_WRONLY | os.O_NONBLOCK)
        except OSError:
            return None

    def _write_fifo(self, fd, plate: str):
        if fd is None:
            return
        try:
            os.write(fd, (plate + "\n").encode())
        except OSError:
            pass

    def _save_screenshot(self, frame):
        if self.screenshot is None:
            return
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = os.path.join("plates", f"{self._last_plate}_{timestamp}.jpg")
        if self.screenshot == "full":
            img_to_save = frame
        elif self.screenshot == "roi":
            x1, y1, x2, y2 = self.roi
            img_to_save = frame[y1:y2, x1:x2]
        else:
            return
        cv2.imwrite(filename, img_to_save)
        logging.info(f"Screenshot saved: {filename}")

    def _clear_camera_buffer(self, cap):
        """Skip old frames from camera buffer to reduce latency."""
        for _ in range(self.buffer_clear_frames):
            cap.grab()

    def _process_frame_async(self, frame, roi, fifo_fd):
        """Process frame in background thread."""
        start_time = time.time()
        det = self._detect_and_read(frame, roi)

        with self._processing_lock:
            if det is not None:
                plate_text, bbox = det
                if plate_text != self._last_plate:
                    self._last_plate = plate_text
                    self._detection_result = (plate_text, bbox)
                    self._detection_frame = frame.copy()
                    self._detection_timestamp = time.time()

                    # Execute callbacks and outputs
                    if callable(self.on_detect):
                        try:
                            self.on_detect(plate_text)
                        except Exception:
                            logging.exception("on_detect callback error")
                    else:
                        logging.info(f"Plate: {plate_text}")

                    self._write_fifo(fifo_fd, plate_text)
                    self._save_screenshot(frame)

            self._is_processing = False

        if self.enable_performance_logging:
            elapsed = time.time() - start_time
            logging.info(f"Detection cycle took {elapsed:.3f}s")

    def run(self):
        cap = cv2.VideoCapture(self.rtsp_url)
        if not cap.isOpened():
            raise RuntimeError(f"Cant open stream on: {self.rtsp_url}")
        ok, frame = cap.read()
        if not ok:
            raise RuntimeError("Error reading initial frame")
        logging.info(f"Video stream started: {self.rtsp_url} | headless={self.headless}")
        fifo_fd = self._open_fifo()
        if self.roi is None:
            self.roi = self._default_center_square_roi(frame)
        if not self.headless:
            cv2.namedWindow("LPR", cv2.WINDOW_NORMAL)
            cv2.resizeWindow("LPR", self.window_width, self.window_height)

        try:
            while True:
                # Clear buffer and get fresh frame
                self._clear_camera_buffer(cap)
                ok, frame = cap.read()
                if not ok:
                    time.sleep(0.03)
                    continue

                now = time.time()

                # Start async processing if interval elapsed and not already processing
                if (now - self._last_process_time) >= self.process_interval_s:
                    with self._processing_lock:
                        if not self._is_processing:
                            self._is_processing = True
                            self._last_process_time = now
                            # Launch processing in background thread
                            thread = threading.Thread(
                                target=self._process_frame_async,
                                args=(frame.copy(), self.roi, fifo_fd),
                                daemon=True
                            )
                            thread.start()

                # Display frame with detection overlay if available
                display_frame = frame.copy()

                # Check if we should show detection result
                with self._processing_lock:
                    if (self._detection_result is not None and
                        (now - self._detection_timestamp) < self.freeze_seconds):
                        plate_text, bbox = self._detection_result
                        if not self.headless:
                            self._draw_polygon(display_frame, bbox, color=(0, 0, 255), thickness=2)
                            px, py = bbox[0]
                            cv2.putText(display_frame, plate_text, (px, py - 10),
                                        cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 0, 255), 2)
                    elif (self._detection_result is not None and
                          (now - self._detection_timestamp) >= self.freeze_seconds):
                        # Clear result after freeze period
                        self._detection_result = None
                        self._detection_frame = None

                if not self.headless:
                    self._draw_ruler_and_roi(display_frame, self.roi)
                    disp = cv2.resize(display_frame, (self.window_width, self.window_height))
                    cv2.imshow("LPR", disp)
                    if cv2.waitKey(1) & 0xFF == ord('q'):
                        break

                time.sleep(0.01)

        except KeyboardInterrupt:
            print("\nShutting down…")
        finally:
            cap.release()
            if fifo_fd:
                os.close(fifo_fd)
            if not self.headless:
                cv2.destroyAllWindows()

    def _detect_and_read(self, frame, roi):
        """Detect and read license plates with optimizations."""
        t0 = time.time() if self.enable_performance_logging else None

        # Downscale frame for faster YOLO inference
        orig_h, orig_w = frame.shape[:2]
        if self.inference_scale < 1.0:
            scaled_w = int(orig_w * self.inference_scale)
            scaled_h = int(orig_h * self.inference_scale)
            inference_frame = cv2.resize(frame, (scaled_w, scaled_h))
            scale_x = orig_w / scaled_w
            scale_y = orig_h / scaled_h
        else:
            inference_frame = frame
            scale_x = scale_y = 1.0

        t1 = time.time() if self.enable_performance_logging else None

        # Run YOLO detection using backend abstraction
        detections = self._yolo.detect(inference_frame)

        t2 = time.time() if self.enable_performance_logging else None

        # Process detections
        for x1, y1, x2, y2, conf, _cls in detections:
            if conf < self.conf_thresh:
                continue

            # Scale coordinates back to original frame
            x1 = int(x1 * scale_x)
            y1 = int(y1 * scale_y)
            x2 = int(x2 * scale_x)
            y2 = int(y2 * scale_y)

            # Extract region from original frame
            region = frame[y1:y2, x1:x2]
            if region.size == 0:
                continue

            gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)

            t3 = time.time() if self.enable_performance_logging else None

            # Run OCR using backend abstraction
            ocr_results = self._ocr.read(gray)

            t4 = time.time() if self.enable_performance_logging else None

            for bbox, text, conf_ocr in ocr_results:
                if conf_ocr < self.min_ocr_conf:
                    continue

                original_text = (text or "").strip().upper()
                clean = re.sub(r"[^A-Z0-9]", "", original_text)

                if _PLATE_RE.match(clean):
                    bbox_global = [(int(pt[0] + x1), int(pt[1] + y1)) for pt in bbox]
                    cx = sum(p[0] for p in bbox_global) // 4
                    cy = sum(p[1] for p in bbox_global) // 4
                    rx1, ry1, rx2, ry2 = roi

                    if (rx1 <= cx <= rx2) and (ry1 <= cy <= ry2):
                        if self.enable_performance_logging:
                            logging.info(
                                f"Timing - Resize: {(t1-t0)*1000:.1f}ms, "
                                f"YOLO: {(t2-t1)*1000:.1f}ms, "
                                f"Prep: {(t3-t2)*1000:.1f}ms, "
                                f"OCR: {(t4-t3)*1000:.1f}ms"
                            )
                        # Early exit: return first valid plate
                        return (clean, bbox_global)

        return None

    @staticmethod
    def _default_center_square_roi(frame, frac: float = 0.2, aspect_ratio: float = 3.07):
        h, w = frame.shape[:2]
        roi_w = int(w * frac)
        roi_h = int(roi_w / aspect_ratio)
        cx, cy = w // 2, h // 2
        x1 = max(0, cx - roi_w // 2)
        y1 = max(0, cy - roi_h // 2)
        x2 = min(w - 1, x1 + roi_w)
        y2 = min(h - 1, y1 + roi_h)
        return (x1, y1, x2, y2)

    @staticmethod
    def _draw_polygon(frame, pts, color=(0, 0, 255), thickness=2):
        arr = np.array([pts], dtype=np.int32)
        cv2.polylines(frame, arr, isClosed=True, color=color, thickness=thickness)

    @staticmethod
    def _draw_ruler_and_roi(frame, roi, step: int = 100):
        if frame is None:
            return
        h, w = frame.shape[:2]
        for x in range(0, w, step):
            cv2.line(frame, (x, 0), (x, 10), (255, 255, 255), 1)
            cv2.putText(frame, str(x), (x+2, 20),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        for y in range(0, h, step):
            cv2.line(frame, (0, y), (10, y), (255, 255, 255), 1)
            cv2.putText(frame, str(y), (15, y+5),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.4, (255, 255, 255), 1)
        x1, y1, x2, y2 = roi
        cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
        cv2.putText(frame, "x1,y1", (x1+5, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
        cv2.putText(frame, "x2,y1", (x2-55, y1-5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
        cv2.putText(frame, "x1,y2", (x1+5, y2+15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
        cv2.putText(frame, "x2,y2", (x2-55, y2+15),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,255,0), 1)
