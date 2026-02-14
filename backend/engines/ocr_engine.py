"""PaddleOCR engine for text extraction."""

import os
import cv2
import numpy as np
from PIL import Image
from typing import List

# Fix PaddlePaddle PIR/oneDNN crash: "ConvertPirAttribute2RuntimeAttribute not support"
os.environ.setdefault("FLAGS_enable_pir_api", "0")
os.environ.setdefault("FLAGS_enable_pir_in_executor", "0")

try:
    import torch
    HAS_GPU = torch.cuda.is_available()
except Exception:
    HAS_GPU = False

from models import BoundingBox, OCRRegion


class PaddleOCREngine:
    """PaddleOCR wrapper - supports both old and new API."""

    _instance = None

    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._init = False
        return cls._instance

    def __init__(self, lang: str = "en"):
        if self._init:
            return
        from paddleocr import PaddleOCR

        # PaddleOCR v3.x changed parameter names
        try:
            self.ocr = PaddleOCR(
                lang=lang,
                use_textline_orientation=True,
                use_gpu=HAS_GPU,
            )
            self._use_new_api = True
        except Exception:
            # Fallback for older PaddleOCR
            try:
                self.ocr = PaddleOCR(
                    lang=lang,
                    use_angle_cls=True,
                    use_gpu=HAS_GPU,
                    show_log=False,
                )
                self._use_new_api = False
            except Exception:
                self.ocr = PaddleOCR(lang=lang)
                self._use_new_api = hasattr(self.ocr, "predict")
        if not hasattr(self, '_use_new_api'):
            self._use_new_api = hasattr(self.ocr, "predict")
        self._init = True
        print(f"  PaddleOCR ready (API: {'predict()' if self._use_new_api else 'ocr()'}, GPU: {HAS_GPU})")

    def _to_cv2(self, image):
        if isinstance(image, str):
            return cv2.imread(image)
        elif isinstance(image, Image.Image):
            arr = np.array(image)
            if len(arr.shape) == 3:
                return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
            return arr
        return image

    def extract(self, image, page_num: int = 0) -> List[OCRRegion]:
        img_cv2 = self._to_cv2(image)
        regions = []

        # Try predict() API first (PaddleOCR v3+), fall back to ocr() if it crashes
        for attempt, use_predict in enumerate([self._use_new_api, not self._use_new_api]):
            try:
                if use_predict:
                    result = self.ocr.predict(img_cv2)
                    if result and len(result) > 0:
                        data = result[0]
                        texts = data.get("rec_texts", [])
                        scores = data.get("rec_scores", [])
                        polys = data.get("rec_polys", [])
                        for text, score, poly in zip(texts, scores, polys):
                            coords = poly.tolist() if hasattr(poly, "tolist") else poly
                            xs = [float(p[0]) for p in coords]
                            ys = [float(p[1]) for p in coords]
                            bbox = BoundingBox(x1=min(xs), y1=min(ys), x2=max(xs), y2=max(ys), page=page_num)
                            regions.append(OCRRegion(text=str(text), bbox=bbox, confidence=float(score), page_num=page_num))
                else:
                    result = self.ocr.ocr(img_cv2, cls=True)
                    if result and result[0]:
                        for line in result[0]:
                            if line is None:
                                continue
                            polygon = line[0]
                            text = line[1][0]
                            confidence = float(line[1][1])
                            xs = [float(p[0]) for p in polygon]
                            ys = [float(p[1]) for p in polygon]
                            bbox = BoundingBox(x1=min(xs), y1=min(ys), x2=max(xs), y2=max(ys), page=page_num)
                            regions.append(OCRRegion(text=str(text), bbox=bbox, confidence=confidence, page_num=page_num))

                if regions:
                    break  # Success — no need to retry
                if attempt == 0 and not regions:
                    # First attempt got 0 results, try the other API
                    print(f"    OCR API {'predict()' if use_predict else 'ocr()'} returned 0 regions, trying fallback...")
                    continue
                break
            except Exception as e:
                print(f"    OCR {'predict()' if use_predict else 'ocr()'} error: {e}")
                if attempt == 0:
                    print(f"    Retrying with {'ocr()' if use_predict else 'predict()'} API...")
                    continue
                break

        return regions
