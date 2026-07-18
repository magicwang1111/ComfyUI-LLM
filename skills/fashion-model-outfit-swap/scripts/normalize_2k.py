#!/usr/bin/env python3
"""Normalize a generated image to the base ratio inside a 2048x2048 canvas."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def centered_crop_to_ratio(image: Image.Image, target_ratio: float) -> Image.Image:
    width, height = image.size
    current_ratio = width / height
    if abs(current_ratio - target_ratio) < 1e-9:
        return image
    if current_ratio > target_ratio:
        new_width = max(1, round(height * target_ratio))
        left = (width - new_width) // 2
        return image.crop((left, 0, left + new_width, height))
    new_height = max(1, round(width / target_ratio))
    top = (height - new_height) // 2
    return image.crop((0, top, width, top + new_height))


def target_size(base_size: tuple[int, int], long_edge: int) -> tuple[int, int]:
    width, height = base_size
    if width >= height:
        return long_edge, max(1, round(long_edge * height / width))
    return max(1, round(long_edge * width / height)), long_edge


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--long-edge", type=int, default=2048)
    args = parser.parse_args()

    if args.long_edge <= 0:
        raise SystemExit("--long-edge must be positive")

    with Image.open(args.base) as base_image:
        base_size = base_image.size
    target_ratio = base_size[0] / base_size[1]
    final_size = target_size(base_size, args.long_edge)

    with Image.open(args.input) as source:
        source.load()
        normalized = centered_crop_to_ratio(source, target_ratio)
        normalized = normalized.resize(final_size, Image.Resampling.LANCZOS)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        normalized.save(args.output)

    with Image.open(args.output) as check:
        if check.size != final_size:
            raise SystemExit(f"unexpected output size: {check.size}, expected {final_size}")
    print(f"base={base_size[0]}x{base_size[1]} output={final_size[0]}x{final_size[1]}")


if __name__ == "__main__":
    main()
