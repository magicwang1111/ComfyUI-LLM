#!/usr/bin/env python3
"""Prepare a batch AI try-on job without writing manifests or logs."""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover
    raise SystemExit("Pillow is required to inspect images. Install pillow or use a Python runtime that includes it.") from exc


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
DEFAULT_TARGET_WIDTH = 3072
DEFAULT_TARGET_HEIGHT = 4096


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scan clothing images, validate basic image properties, and plan clean output filenames."
    )
    parser.add_argument("--clothing-dir", required=True, help="Folder containing clothing images.")
    parser.add_argument("--model-image", required=True, help="Reference model image.")
    parser.add_argument("--output-dir", help="Final output folder. Defaults to a timestamped Desktop folder.")
    parser.add_argument("--recursive", action="store_true", help="Include images in subfolders.")
    parser.add_argument("--target-width", type=int, default=DEFAULT_TARGET_WIDTH, help="Final output width.")
    parser.add_argument("--target-height", type=int, default=DEFAULT_TARGET_HEIGHT, help="Final output height.")
    parser.add_argument(
        "--output-format",
        choices=["png", "jpg", "jpeg", "webp"],
        default="png",
        help="Planned final image format.",
    )
    return parser.parse_args()


def default_output_dir() -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return Path.home() / "Desktop" / f"批量AI换装结果_{timestamp}"


def inspect_image(path: Path) -> dict:
    try:
        with Image.open(path) as image:
            image.verify()
        with Image.open(path) as image:
            width, height = image.size
            mode = image.mode
            fmt = image.format
    except Exception as exc:
        return {
            "openable": False,
            "width": None,
            "height": None,
            "format": None,
            "mode": None,
            "reason": f"unreadable image: {exc}",
        }

    return {
        "openable": True,
        "width": width,
        "height": height,
        "format": fmt,
        "mode": mode,
        "reason": None,
    }


def safe_stem(path: Path) -> str:
    stem = re.sub(r"[^\w.-]+", "_", path.stem, flags=re.UNICODE).strip("._-")
    return stem or "image"


def planned_name(index: int, path: Path, output_format: str, used_names: set[str]) -> str:
    ext = "jpg" if output_format == "jpeg" else output_format
    base = f"{index:03d}_{safe_stem(path)}_tryon"
    candidate = f"{base}.{ext}"
    suffix = 2
    while candidate.lower() in used_names:
        candidate = f"{base}_{suffix}.{ext}"
        suffix += 1
    used_names.add(candidate.lower())
    return candidate


def classify_clothing(path: Path, target_width: int, target_height: int) -> tuple[str, str | None]:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return "skipped", "unsupported file format"

    info = inspect_image(path)
    if not info["openable"]:
        return "skipped", info["reason"]

    width = int(info["width"])
    height = int(info["height"])
    short_side = min(width, height)

    if short_side < 256:
        return "skipped", f"image is too small for reliable try-on ({width}x{height})"
    if short_side < 512:
        return "review", f"low resolution; visually confirm garment is still clear ({width}x{height})"

    if target_width <= 0 or target_height <= 0:
        return "skipped", "target dimensions must be positive"

    return "ready", None


def validate_model(path: Path) -> dict:
    if not path.exists():
        return {"status": "blocked", "reason": "model image does not exist"}
    if not path.is_file():
        return {"status": "blocked", "reason": "model image path is not a file"}
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        return {"status": "blocked", "reason": "unsupported model image format"}

    info = inspect_image(path)
    if not info["openable"]:
        return {"status": "blocked", "reason": info["reason"]}

    width = int(info["width"])
    height = int(info["height"])
    if min(width, height) < 256:
        return {"status": "blocked", "reason": f"model image is too small ({width}x{height})"}

    status = "ready"
    reason = None
    if min(width, height) < 512:
        status = "review"
        reason = f"model image is low resolution; visually confirm the body is clear ({width}x{height})"

    return {
        "status": status,
        "reason": reason,
        "width": width,
        "height": height,
        "format": info["format"],
    }


def iter_files(clothing_dir: Path, recursive: bool) -> list[Path]:
    pattern = "**/*" if recursive else "*"
    return sorted(path for path in clothing_dir.glob(pattern) if path.is_file())


def main() -> int:
    args = parse_args()

    clothing_dir = Path(args.clothing_dir).expanduser().resolve()
    model_image = Path(args.model_image).expanduser().resolve()
    output_dir = Path(args.output_dir).expanduser().resolve() if args.output_dir else default_output_dir().resolve()

    if not clothing_dir.exists() or not clothing_dir.is_dir():
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": "clothing directory does not exist or is not a directory",
                    "clothing_dir": str(clothing_dir),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    model_status = validate_model(model_image)
    if model_status["status"] == "blocked":
        print(
            json.dumps(
                {
                    "status": "blocked",
                    "reason": model_status["reason"],
                    "model_image": str(model_image),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
        return 2

    output_dir.mkdir(parents=True, exist_ok=True)

    used_names: set[str] = set()
    items = []
    candidate_index = 1

    for path in iter_files(clothing_dir, args.recursive):
        status, reason = classify_clothing(path, args.target_width, args.target_height)
        record = {
            "source_path": str(path),
            "filename": path.name,
            "status": status,
            "reason": reason,
            "planned_output_path": None,
        }

        if status in {"ready", "review"}:
            name = planned_name(candidate_index, path, args.output_format, used_names)
            record["planned_output_path"] = str(output_dir / name)
            candidate_index += 1

        items.append(record)

    summary = {
        "status": "ready",
        "clothing_dir": str(clothing_dir),
        "model_image": str(model_image),
        "model_status": model_status,
        "output_dir": str(output_dir),
        "recursive": bool(args.recursive),
        "target": {
            "width": args.target_width,
            "height": args.target_height,
            "aspect_ratio": f"{args.target_width}:{args.target_height}",
            "orientation": "vertical" if args.target_height >= args.target_width else "horizontal",
            "format": args.output_format,
        },
        "counts": {
            "detected_files": len(items),
            "ready": sum(1 for item in items if item["status"] == "ready"),
            "review": sum(1 for item in items if item["status"] == "review"),
            "skipped_basic": sum(1 for item in items if item["status"] == "skipped"),
        },
        "items": items,
    }

    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
