from PIL import Image
import io
import numpy as np

# Tunables (adjust once, then forget)
MIN_IMAGE_KB = 10
GRAY_RATIO_THRESHOLD = 0.55
GRAY_MIN = 90
GRAY_MAX = 210
GRAY_DELTA = 4

def validate_image_gray_area(image_bytes: bytes) -> bool:
    print(len(image_bytes))
    # ---- Stage 1: size check (O(1)) ----
    if len(image_bytes) < (MIN_IMAGE_KB * 1024):
        return False

    # ---- Stage 2: structural integrity (cheap) ----
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img.verify()
    except Exception:
        return False

    # ---- Stage 3: partial pixel decode (cropped, fast) ----
    try:
        with Image.open(io.BytesIO(image_bytes)) as img:
            img = img.convert("RGB")

            w, h = img.size
            if w == 0 or h == 0:
                return False

            # Sample bottom 35% where corruption usually appears
            crop_y = int(h * 0.65)
            img_crop = img.crop((0, crop_y, w, h))

            # Downscale aggressively (huge speedup)
            img_small = img_crop.resize((w // 8, h // 8))

            arr = np.asarray(img_small, dtype=np.uint8)

            r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

            gray_mask = (
                (np.abs(r - g) < GRAY_DELTA) &
                (np.abs(r - b) < GRAY_DELTA) &
                (r > GRAY_MIN) & (r < GRAY_MAX)
            )

            gray_ratio = gray_mask.mean()
            return gray_ratio < GRAY_RATIO_THRESHOLD

    except Exception:
        return False