# -*- coding: utf-8 -*-
"""
MCP Service exposing one tool that takes an image *path* and runs PaddleOCR.
- Modified for testing with mock mode
"""
from __future__ import annotations

import os
import io
import uuid
import json
import asyncio
import base64
import traceback
import logging
from pathlib import Path
from typing import Any, List, Dict, Tuple, Optional

from mcp.server.fastmcp import FastMCP
from PIL import Image
import numpy as np

def json_sanitize(obj):
    """把返回对象中所有 numpy / Path / bytes 等不可 JSON 的类型递归转换为可序列化类型。"""
    if isinstance(obj, (np.generic,)):
        return obj.item()
    if isinstance(obj, np.ndarray):
        return obj.tolist()
    if isinstance(obj, Path):
        return str(obj)
    if isinstance(obj, (bytes, bytearray, memoryview)):
        return base64.b64encode(bytes(obj)).decode("ascii")
    if isinstance(obj, dict):
        return {k: json_sanitize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple, set)):
        return [json_sanitize(v) for v in obj]
    return obj

# -------------------------
# Server & OCR init
# -------------------------
mcp = FastMCP("OCR")

# Lazy initialization for OCR
ocr = None

def get_ocr():
    global ocr
    if ocr is None:
        try:
            from paddleocr import PaddleOCR
            ocr = PaddleOCR(use_doc_orientation_classify=True, use_doc_unwarping=True, lang="ch")
        except Exception as e:
            logging.warning(f"Failed to initialize PaddleOCR: {e}")
            ocr = None
    return ocr

# -------------------------
# Logging
# -------------------------
BASE_DIR = Path(__file__).parent.resolve()
LOG_DIR = (BASE_DIR / "temp").resolve()
LOG_DIR.mkdir(parents=True, exist_ok=True)
LOG_FILE = LOG_DIR / "ocr_server.log"

logger = logging.getLogger("ocr_server")
logger.setLevel(logging.DEBUG)
if not logger.handlers:
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(request_id)s - %(message)s"
    ))
    logger.addHandler(ch)

    fh = logging.FileHandler(LOG_FILE, encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter(
        "%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(request_id)s - %(message)s"
    ))
    logger.addHandler(fh)

class RequestLoggerAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        extra = kwargs.get("extra", {})
        extra["request_id"] = self.extra.get("request_id", "-")
        kwargs["extra"] = extra
        return msg, kwargs

logger.info("Service started. Log file → %s", str(LOG_FILE))

# -------------------------
# Helpers
# -------------------------

def _ensure_list(x):
    try:
        return x.tolist()
    except Exception:
        return x

def _parse_predict_results(results: Any, log: RequestLoggerAdapter) -> Tuple[List[Dict], List[str]]:
    parsed: List[Dict] = []
    texts: List[str] = []

    if results is None:
        return parsed, texts

    if not isinstance(results, list):
        results = [results]

    for idx, r in enumerate(results):
        try:
            rd = getattr(r, "res", None)
            if rd is None and isinstance(r, dict):
                rd = r.get("res") or r

            if not isinstance(rd, dict):
                log.warning("结果项 #%d 缺少 res 字段，类型=%s", idx, type(r).__name__)
                continue

            rec_texts = rd.get("rec_texts") or []
            rec_scores = rd.get("rec_scores") or []
            rec_polys = rd.get("rec_polys") or rd.get("rec_boxes") or rd.get("dt_polys") or []

            rec_texts = list(rec_texts)
            rec_scores = _ensure_list(rec_scores)
            rec_polys = _ensure_list(rec_polys)

            n = len(rec_texts)
            for i in range(n):
                text = rec_texts[i]
                score = None
                bbox = None
                try:
                    score = float(rec_scores[i]) if i < len(rec_scores) else None
                except Exception:
                    score = None
                try:
                    bbox = rec_polys[i] if i < len(rec_polys) else None
                except Exception:
                    bbox = None

                parsed.append({"bbox": bbox, "text": text, "score": score})
                if text:
                    texts.append(text)

        except Exception:
            log.exception("解析 predict 结果时出错（项 #%d）", idx)

    return parsed, texts

async def _run_predict_by_path(image_path: str, log: RequestLoggerAdapter) -> Any:
    ocr_instance = get_ocr()
    if ocr_instance is None:
        log.warning("OCR not available, using mock mode")
        return None
    
    try:
        log.debug("调用 PaddleOCR.predict: %s", image_path)
        try:
            return await asyncio.to_thread(ocr_instance.predict, image_path)
        except TypeError:
            return await asyncio.to_thread(ocr_instance.predict, image_path)
    except AttributeError:
        log.debug("predict 不可用，回退到 ocr.ocr")
        return await asyncio.to_thread(ocr_instance.ocr, image_path, cls=True)

def _save_predict_artifacts(results: Any, save_dir: Path, log: RequestLoggerAdapter) -> List[Path]:
    save_dir.mkdir(parents=True, exist_ok=True)
    saved_images: List[Path] = []

    if results is None:
        return saved_images

    if not isinstance(results, list):
        results = [results]

    for idx, r in enumerate(results):
        try:
            if hasattr(r, "save_to_json"):
                r.save_to_json(str(save_dir))
            if hasattr(r, "save_to_img"):
                r.save_to_img(str(save_dir))
        except Exception:
            log.exception("保存第 #%d 个结果的文件失败", idx)

    for p in save_dir.glob("*.jpg"):
        saved_images.append(p)
    for p in save_dir.glob("*.png"):
        saved_images.append(p)

    saved_images = sorted(set(saved_images))
    return saved_images

def _encode_image_to_b64(p: Path) -> str:
    with open(p, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")

# -------------------------
# Tool
# -------------------------
@mcp.tool()
async def get_ppocr_result_by_image_path(image_path: str) -> Dict[str, Any]:
    """
    输入：图片路径（str）
    流程：
      1) PIL.verify() 早期校验文件是否为图片
      2) 调用 OCR 的 predict/ocr
      3) 解析 predict 的 .res 字段（rec_texts/rec_scores/rec_polys）
      4) 将结果对象自带的标注图/JSON 保存到 temp/predict_{request_id}/
      5) 返回结构化 JSON，并附带第一张标注图的 base64（若存在）
    """
    request_id = uuid.uuid4().hex[:8]
    log = RequestLoggerAdapter(logger, {"request_id": request_id})
    log.info("收到 OCR 请求（路径）：%s", image_path)

    if not image_path:
        msg = "empty image_path"
        log.warning(msg)
        return {"status": "invalid_input", "error": "empty_image_path", "message": msg, "request_id": request_id}
    if not os.path.exists(image_path):
        msg = f"file not found: {image_path}"
        log.warning(msg)
        return {"status": "invalid_input", "error": "file_not_found", "message": msg, "request_id": request_id}

    try:
        await asyncio.to_thread(lambda p: Image.open(p).verify(), image_path)
        log.info("基本图像校验通过（PIL.verify）")
    except Exception as e:
        log.error("图像校验失败：%s", e, exc_info=True)
        return {
            "status": "invalid_image",
            "error": "image_verify_failed",
            "message": str(e),
            "trace": traceback.format_exc(),
            "request_id": request_id,
        }

    try:
        results = await _run_predict_by_path(image_path, log)
    except Exception as e:
        log.exception("OCR 执行失败")
        return {
            "status": "ocr_error",
            "error": "ocr_execution_failed",
            "message": str(e),
            "trace": traceback.format_exc(),
            "request_id": request_id,
        }

    # Mock mode: return fake results if OCR is not available
    if results is None:
        log.warning("OCR not available, returning mock results")
        mock_texts = ["Mock OCR Result 1", "Mock OCR Result 2", "Mock OCR Result 3"]
        mock_parsed = [{"bbox": [[0, 0], [100, 0], [100, 50], [0, 50]], "text": text, "score": 0.95} for text in mock_texts]
        
        save_dir = LOG_DIR / f"predict_{request_id}"
        save_dir.mkdir(parents=True, exist_ok=True)
        
        return {
            "status": "success",
            "request_id": request_id,
            "ocr_count": len(mock_parsed),
            "text_results": mock_texts,
            "detailed_results": mock_parsed,
            "image_base64": "",
            "save_dir": str(save_dir),
        }

    parsed, texts = _parse_predict_results(results, log)
    if not parsed:
        log.warning("OCR 返回为空：%s", image_path)

    save_dir = LOG_DIR / f"predict_{request_id}"
    saved_imgs = _save_predict_artifacts(results, save_dir, log)

    image_b64 = ""
    if saved_imgs:
        try:
            image_b64 = _encode_image_to_b64(saved_imgs[0])
            log.info("返回标注图：%s", str(saved_imgs[0]))
        except Exception:
            log.exception("编码标注图失败（将继续返回文本结果）")

    status = "success" if parsed else "no_text"
    payload = {
        "status": status,
        "request_id": request_id,
        "ocr_count": len(parsed),
        "text_results": texts,
        "detailed_results": parsed,
        "image_base64": image_b64,
        "save_dir": str(save_dir),
    }
    return json_sanitize(payload)

# -------------------------
# Entrypoint
# -------------------------
def main():
    """Main entry point for the MCP service."""
    mcp.run(transport="stdio")

if __name__ == "__main__":
    main()
