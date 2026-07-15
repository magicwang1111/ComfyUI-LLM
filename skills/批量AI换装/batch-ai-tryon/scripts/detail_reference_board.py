#!/usr/bin/env python3
"""Create a temporary faithful detail reference board for difficult garment references."""

from __future__ import annotations

import argparse
import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageOps, ImageStat


SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Build a temporary board with originals, faithful light-enhancement views, and high-detail crops "
            "to help identify low-contrast decorations during AI try-on without exaggerating them."
        )
    )
    parser.add_argument("--input", nargs="+", required=True, help="One or more garment reference images.")
    parser.add_argument("--out", required=True, help="Output board path, usually outside the final output folder.")
    parser.add_argument("--crop-count", type=int, default=4, help="High-detail crops per input image.")
    parser.add_argument(
        "--enhance",
        choices=["faithful", "none"],
        default="faithful",
        help="Use faithful light enhancement or no enhancement. Avoid strong enhancement that changes detail density.",
    )
    parser.add_argument("--tile-width", type=int, default=420, help="Tile width in pixels.")
    parser.add_argument("--tile-height", type=int, default=520, help="Tile height in pixels.")
    return parser.parse_args()


def open_image(path: Path) -> Image.Image:
    if path.suffix.lower() not in SUPPORTED_EXTENSIONS:
        raise ValueError(f"unsupported file format: {path}")
    return Image.open(path).convert("RGB")


def fit_tile(image: Image.Image, size: tuple[int, int], fill: tuple[int, int, int] = (245, 245, 245)) -> Image.Image:
    fitted = ImageOps.contain(image, size, Image.Resampling.LANCZOS)
    tile = Image.new("RGB", size, fill)
    tile.paste(fitted, ((size[0] - fitted.width) // 2, (size[1] - fitted.height) // 2))
    return tile


def enhanced(image: Image.Image, mode: str = "faithful") -> Image.Image:
    if mode == "none":
        return image.copy()
    image = ImageOps.autocontrast(image, cutoff=0.2)
    return image.filter(ImageFilter.UnsharpMask(radius=1.0, percent=70, threshold=4))


def crop_score(image: Image.Image) -> float:
    gray = ImageOps.grayscale(image)
    edges = gray.filter(ImageFilter.FIND_EDGES)
    edge_stat = ImageStat.Stat(edges)
    gray_stat = ImageStat.Stat(gray)
    return float(edge_stat.mean[0]) + float(gray_stat.stddev[0]) * 0.8


def overlaps(a: tuple[int, int, int, int], b: tuple[int, int, int, int]) -> bool:
    ax1, ay1, ax2, ay2 = a
    bx1, by1, bx2, by2 = b
    intersection_w = max(0, min(ax2, bx2) - max(ax1, bx1))
    intersection_h = max(0, min(ay2, by2) - max(ay1, by1))
    if intersection_w == 0 or intersection_h == 0:
        return False
    intersection = intersection_w * intersection_h
    smaller = min((ax2 - ax1) * (ay2 - ay1), (bx2 - bx1) * (by2 - by1))
    return intersection / max(smaller, 1) > 0.35


def high_detail_crops(image: Image.Image, count: int, enhance_mode: str) -> list[Image.Image]:
    width, height = image.size
    if width < 80 or height < 80 or count <= 0:
        return []

    crop_size = int(min(width, height) * 0.42)
    crop_size = max(80, min(crop_size, width, height))
    step_x = max(1, (width - crop_size) // 4)
    step_y = max(1, (height - crop_size) // 4)

    candidates: list[tuple[float, tuple[int, int, int, int]]] = []
    for y in range(0, max(1, height - crop_size + 1), step_y):
        for x in range(0, max(1, width - crop_size + 1), step_x):
            box = (x, y, x + crop_size, y + crop_size)
            candidates.append((crop_score(image.crop(box)), box))

    candidates.sort(reverse=True, key=lambda item: item[0])
    selected: list[tuple[int, int, int, int]] = []
    for _, box in candidates:
        if all(not overlaps(box, chosen) for chosen in selected):
            selected.append(box)
        if len(selected) >= count:
            break

    return [enhanced(image.crop(box), enhance_mode) for box in selected]


def label(draw: ImageDraw.ImageDraw, xy: tuple[int, int], text: str) -> None:
    x, y = xy
    draw.rectangle((x, y, x + 390, y + 26), fill=(255, 255, 255))
    draw.text((x + 6, y + 6), text, fill=(0, 0, 0))


def board_note(draw: ImageDraw.ImageDraw, width: int) -> None:
    note = "Reference aid only: identify details; do not increase decoration size, brightness, density, or regularity."
    draw.rectangle((0, 0, width, 34), fill=(255, 255, 255))
    draw.text((12, 10), note, fill=(0, 0, 0))


def main() -> int:
    args = parse_args()
    inputs = [Path(item).expanduser().resolve() for item in args.input]
    out = Path(args.out).expanduser().resolve()

    tiles: list[tuple[str, Image.Image]] = []
    for index, path in enumerate(inputs, start=1):
        image = open_image(path)
        tiles.append((f"{index} original", image))
        tiles.append((f"{index} faithful enhanced", enhanced(image, args.enhance)))
        for crop_index, crop in enumerate(high_detail_crops(image, args.crop_count, args.enhance), start=1):
            tiles.append((f"{index} detail crop {crop_index}", crop))

    tile_size = (args.tile_width, args.tile_height)
    columns = 3 if len(tiles) > 2 else 2
    rows = math.ceil(len(tiles) / columns)
    margin = 18
    label_height = 30
    note_height = 34
    board = Image.new(
        "RGB",
        (
            columns * tile_size[0] + (columns + 1) * margin,
            note_height + rows * (tile_size[1] + label_height) + (rows + 1) * margin,
        ),
        (235, 235, 235),
    )
    draw = ImageDraw.Draw(board)
    board_note(draw, board.width)

    for idx, (name, image) in enumerate(tiles):
        col = idx % columns
        row = idx // columns
        x = margin + col * (tile_size[0] + margin)
        y = note_height + margin + row * (tile_size[1] + label_height + margin)
        board.paste(fit_tile(image, tile_size), (x, y + label_height))
        label(draw, (x, y), name)

    out.parent.mkdir(parents=True, exist_ok=True)
    board.save(out, quality=92)
    print(out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
