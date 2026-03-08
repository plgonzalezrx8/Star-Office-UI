#!/usr/bin/env python3
"""Batch convert PNG assets to WebP with sane defaults."""

from __future__ import annotations

import os
from PIL import Image

FRONTEND_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "frontend")
STATIC_DIR = FRONTEND_DIR

# Lossless conversion for sprite sheets and alpha-sensitive assets.
LOSSLESS_FILES = [
    "star-idle-spritesheet.png",
    "star-researching-spritesheet.png",
    "star-working-spritesheet.png",
    "sofa-busy-spritesheet.png",
    "plants-spritesheet.png",
    "posters-spritesheet.png",
    "coffee-machine-spritesheet.png",
    "serverroom-spritesheet.png",
]

# Lossy conversion for flat/large backgrounds.
LOSSY_FILES = [
    "office_bg.png",
    "sofa-idle.png",
    "desk.png",
]


def convert_to_webp(input_path: str, output_path: str, lossless: bool = True, quality: int = 85) -> bool:
    """Convert a single PNG file to WebP and print size delta."""
    try:
        image = Image.open(input_path)
        if lossless:
            image.save(output_path, "WebP", lossless=True, method=6)
        else:
            image.save(output_path, "WebP", quality=quality, method=6)

        old_size = os.path.getsize(input_path)
        new_size = os.path.getsize(output_path)
        savings = (1 - (new_size / old_size)) * 100

        print(f"Converted: {os.path.basename(input_path)} -> {os.path.basename(output_path)}")
        print(f"  Size: {old_size/1024:.1f}KB -> {new_size/1024:.1f}KB ({savings:.1f}% saved)")
        return True
    except Exception as exc:
        print(f"Conversion failed for {os.path.basename(input_path)}: {exc}")
        return False


def main() -> None:
    print("=" * 60)
    print("PNG -> WebP Converter")
    print("=" * 60)

    if not os.path.exists(STATIC_DIR):
        print(f"Directory not found: {STATIC_DIR}")
        return

    ok = 0
    fail = 0

    print("\nStarting conversion pass...\n")
    print("Lossless files:")
    for filename in LOSSLESS_FILES:
        source = os.path.join(STATIC_DIR, filename)
        if not os.path.exists(source):
            print(f"  Missing file, skipped: {filename}")
            continue
        target = os.path.join(STATIC_DIR, filename.replace(".png", ".webp"))
        if convert_to_webp(source, target, lossless=True):
            ok += 1
        else:
            fail += 1

    print("\nLossy files (quality=85):")
    for filename in LOSSY_FILES:
        source = os.path.join(STATIC_DIR, filename)
        if not os.path.exists(source):
            print(f"  Missing file, skipped: {filename}")
            continue
        target = os.path.join(STATIC_DIR, filename.replace(".png", ".webp"))
        if convert_to_webp(source, target, lossless=False, quality=85):
            ok += 1
        else:
            fail += 1

    print("\n" + "=" * 60)
    print(f"Done. Success: {ok}, Failed: {fail}")
    print("=" * 60)
    print("Notes:")
    print("  - Original PNG files are preserved.")
    print("  - Update frontend references if you want to force WebP paths.")


if __name__ == "__main__":
    main()
