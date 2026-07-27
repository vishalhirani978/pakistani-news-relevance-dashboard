import os
from typing import Optional
import cv2
from PIL import Image
import numpy as np

# Minimum size to filter out logos/placeholders
MIN_IMAGE_BYTES = 5000


def dhash(image: Image.Image, hash_size: int = 8) -> list:
    """
    Difference Hash (dhash) implementation in pure Python using Pillow.
    Faster and more robust to scale/aspect ratio changes than average hash.
    """
    # Resize the image to (hash_size + 1, hash_size) as grayscale
    resample = getattr(Image, "Resampling", Image).LANCZOS
    img = image.convert("L").resize((hash_size + 1, hash_size), resample)
    pixels = list(img.getdata())

    difference = []
    for row in range(hash_size):
        for col in range(hash_size):
            pixel_left = pixels[row * (hash_size + 1) + col]
            pixel_right = pixels[row * (hash_size + 1) + col + 1]
            difference.append(pixel_left > pixel_right)
    return difference


def dhash_similarity(img1: Image.Image, img2: Image.Image) -> float:
    """Calculate similarity (0.0 to 1.0) based on dhash Hamming distance."""
    hash1 = dhash(img1)
    hash2 = dhash(img2)
    hamming_dist = sum(el1 != el2 for el1, el2 in zip(hash1, hash2))
    return 1.0 - (hamming_dist / len(hash1))


def histogram_similarity(img1_path: str, img2_path: str) -> float:
    """Compute color histogram similarity in HSV space using OpenCV."""
    try:
        img1 = cv2.imread(img1_path)
        img2 = cv2.imread(img2_path)
        if img1 is None or img2 is None:
            return 0.0
        hsv1 = cv2.cvtColor(img1, cv2.COLOR_BGR2HSV)
        hsv2 = cv2.cvtColor(img2, cv2.COLOR_BGR2HSV)

        # Calculate 2D histogram on Hue and Saturation
        hist1 = cv2.calcHist([hsv1], [0, 1], None, [180, 256], [0, 180, 0, 256])
        hist2 = cv2.calcHist([hsv2], [0, 1], None, [180, 256], [0, 180, 0, 256])

        cv2.normalize(hist1, hist1, 0, 1, cv2.NORM_MINMAX)
        cv2.normalize(hist2, hist2, 0, 1, cv2.NORM_MINMAX)

        sim = cv2.compareHist(hist1, hist2, cv2.HISTCMP_CORREL)

        # Scale correlation from [-1, 1] to [0, 1]
        return max(0.0, (sim + 1.0) / 2.0)
    except Exception:
        return 0.0


def calculate_image_similarity(image1_path: str, image2_path: str) -> float:
    """
    Compute a robust image similarity score (0–1) between two article images
    using color histograms and difference hashing.

    1. Filters out small/missing/invalid images (logos/placeholders).
    2. Computes structural similarity via perceptual difference hash.
    3. Computes color similarity via HSV histogram correlation.
    4. Combines both metrics (50% structure, 50% color).
    """
    for path in (image1_path, image2_path):
        if not path:
            return 0.0
        if not os.path.exists(path):
            return 0.0
        if os.path.getsize(path) < MIN_IMAGE_BYTES:
            return 0.0  # Filter out logos/placeholders

    try:
        # Load Pillow images for hashing
        img1 = Image.open(image1_path)
        img2 = Image.open(image2_path)

        # Structural similarity
        h_sim = dhash_similarity(img1, img2)

        # Color similarity
        c_sim = histogram_similarity(image1_path, image2_path)

        # Combine: 50% structural hash, 50% color histogram
        combined = 0.50 * h_sim + 0.50 * c_sim
        return round(float(combined), 3)
    except Exception:
        return 0.0
