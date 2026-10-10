import sys
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from rembg import remove


BASE_DIR = Path(__file__).resolve().parent.parent
INPUT_FILE = BASE_DIR / "assets" / "image.png"
OUTPUT_FILE = BASE_DIR / "assets" / "source-prepped.png"


def prepare_photo():
    if not INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Source photo not found: {INPUT_FILE}"
        )

    print("Removing photo background...")

    image = Image.open(INPUT_FILE).convert("RGBA")
    foreground = remove(image)

    rgba = np.array(foreground)

    rgb = rgba[:, :, :3]
    alpha = rgba[:, :, 3]

    # Composite the subject onto a white background.
    alpha_float = alpha[:, :, None].astype(np.float32) / 255.0

    white = np.full_like(rgb, 255)

    composited = (
        rgb.astype(np.float32) * alpha_float
        + white.astype(np.float32) * (1 - alpha_float)
    ).astype(np.uint8)

    print("Converting to grayscale...")

    gray = cv2.cvtColor(
        composited,
        cv2.COLOR_RGB2GRAY
    )

    print("Improving local contrast...")

    clahe = cv2.createCLAHE(
        clipLimit=2.0,
        tileGridSize=(8, 8)
    )

    enhanced = clahe.apply(gray)

    # Preserve a clean white background.
    result = Image.fromarray(enhanced).convert("RGB")

    OUTPUT_FILE.parent.mkdir(
        parents=True,
        exist_ok=True
    )

    result.save(OUTPUT_FILE)

    print(f"Prepared image saved to: {OUTPUT_FILE}")


if __name__ == "__main__":
    try:
        prepare_photo()
    except Exception as error:
        print(f"Photo preparation failed: {error}")
        sys.exit(1)
