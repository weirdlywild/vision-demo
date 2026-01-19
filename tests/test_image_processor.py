import pytest
from app.services.image_processor import ImageProcessor, ImageQualityError


def test_validate_image_too_small():
    """Test that images under 50KB are rejected."""
    small_image = b'fake_image_data'

    with pytest.raises(ImageQualityError, match="too small"):
        ImageProcessor.validate_image(small_image, "test.jpg")


def test_validate_filename():
    """Test filename validation."""
    from app.utils.validators import validate_filename

    assert validate_filename("test.jpg") == True
    assert validate_filename("test.png") == True
    assert validate_filename("../etc/passwd") == False
    assert validate_filename("test.exe") == False


def test_sanitize_filename():
    """Test filename sanitization."""
    from app.utils.validators import sanitize_filename

    assert sanitize_filename("test.jpg") == "test.jpg"
    assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
    assert sanitize_filename("test image!@#.jpg") == "testimage.jpg"


# Note: Full integration tests require actual image files
# Add more tests with sample images in tests/fixtures/sample_images/
