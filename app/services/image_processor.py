import io
import hashlib
from typing import Tuple
from PIL import Image
import cv2
import numpy as np
import imagehash
from app.config import settings


class ImageQualityError(Exception):
    """Raised when image quality is insufficient."""
    pass


class ImageProcessor:
    """Handles image validation, quality checks, and preprocessing."""

    ALLOWED_FORMATS = {'JPEG', 'PNG', 'WEBP'}
    ALLOWED_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.webp'}

    @staticmethod
    def validate_image(image_bytes: bytes, filename: str = "") -> None:
        """
        Validate basic image properties.

        Args:
            image_bytes: Raw image bytes
            filename: Original filename for extension check

        Raises:
            ImageQualityError: If validation fails
        """
        # Check file size
        size_bytes = len(image_bytes)
        min_size = 50 * 1024  # 50KB
        max_size = settings.max_image_size_mb * 1024 * 1024

        if size_bytes < min_size:
            raise ImageQualityError(f"Image too small: {size_bytes} bytes (minimum: {min_size} bytes)")

        if size_bytes > max_size:
            raise ImageQualityError(f"Image too large: {size_bytes} bytes (maximum: {max_size} bytes)")

        # Try to open image
        try:
            image = Image.open(io.BytesIO(image_bytes))
        except Exception as e:
            raise ImageQualityError(f"Invalid image file: {str(e)}")

        # Check format
        if image.format not in ImageProcessor.ALLOWED_FORMATS:
            raise ImageQualityError(f"Unsupported format: {image.format}. Allowed: {ImageProcessor.ALLOWED_FORMATS}")

        # Check dimensions
        width, height = image.size
        min_dim = settings.min_image_dimension

        if width < min_dim or height < min_dim:
            raise ImageQualityError(f"Image too small: {width}x{height} (minimum: {min_dim}x{min_dim})")

        if width > settings.max_image_dimension or height > settings.max_image_dimension:
            raise ImageQualityError(f"Image too large: {width}x{height} (maximum: {settings.max_image_dimension})")

    @staticmethod
    def check_quality(image_bytes: bytes) -> Tuple[bool, str]:
        """
        Check image quality using blur detection and brightness analysis.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Tuple of (is_acceptable, reason)
        """
        # Convert to PIL Image
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to numpy array for opencv
        img_array = np.array(image.convert('RGB'))

        # Convert to grayscale for blur detection
        gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)

        # Blur detection using Laplacian variance
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        if laplacian_var < settings.blur_threshold:
            return False, f"Image too blurry (score: {laplacian_var:.1f}, threshold: {settings.blur_threshold})"

        # Brightness analysis
        mean_brightness = np.mean(img_array)
        if mean_brightness < settings.min_brightness:
            return False, f"Image too dark (brightness: {mean_brightness:.1f})"

        if mean_brightness > settings.max_brightness:
            return False, f"Image too bright (brightness: {mean_brightness:.1f})"

        # Contrast check
        std_dev = np.std(img_array)
        if std_dev < 20:
            return False, f"Image contrast too low (std dev: {std_dev:.1f})"

        return True, "Image quality acceptable"

    @staticmethod
    def preprocess_image(image_bytes: bytes) -> bytes:
        """
        Resize and compress image for optimal API performance.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Preprocessed image bytes
        """
        image = Image.open(io.BytesIO(image_bytes))

        # Convert to RGB if necessary
        if image.mode not in ('RGB', 'L'):
            image = image.convert('RGB')

        # Resize if too large
        max_dimension = settings.resize_max_dimension
        width, height = image.size

        if width > max_dimension or height > max_dimension:
            # Calculate new dimensions maintaining aspect ratio
            if width > height:
                new_width = max_dimension
                new_height = int(height * (max_dimension / width))
            else:
                new_height = max_dimension
                new_width = int(width * (max_dimension / height))

            image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)

        # Compress to JPEG with quality optimization
        output = io.BytesIO()
        image.save(output, format='JPEG', quality=85, optimize=True)
        output.seek(0)

        return output.getvalue()

    @staticmethod
    def calculate_hash(image_bytes: bytes) -> Tuple[str, str]:
        """
        Calculate both SHA256 and perceptual hash of image.

        Args:
            image_bytes: Raw image bytes

        Returns:
            Tuple of (sha256_hash, perceptual_hash)
        """
        # SHA256 for exact match
        sha256_hash = hashlib.sha256(image_bytes).hexdigest()

        # Perceptual hash for similar images
        image = Image.open(io.BytesIO(image_bytes))
        phash = str(imagehash.phash(image, hash_size=16))

        return sha256_hash, phash

    @staticmethod
    def process_upload(image_bytes: bytes, filename: str = "") -> Tuple[bytes, str, str]:
        """
        Full image processing pipeline: validate, check quality, preprocess, hash.

        Args:
            image_bytes: Raw image bytes
            filename: Original filename

        Returns:
            Tuple of (processed_bytes, sha256_hash, perceptual_hash)

        Raises:
            ImageQualityError: If validation or quality check fails
        """
        # Step 1: Validate
        ImageProcessor.validate_image(image_bytes, filename)

        # Step 2: Check quality
        is_acceptable, reason = ImageProcessor.check_quality(image_bytes)
        if not is_acceptable:
            raise ImageQualityError(reason)

        # Step 3: Preprocess
        processed_bytes = ImageProcessor.preprocess_image(image_bytes)

        # Step 4: Calculate hashes
        sha256_hash, phash = ImageProcessor.calculate_hash(processed_bytes)

        return processed_bytes, sha256_hash, phash
