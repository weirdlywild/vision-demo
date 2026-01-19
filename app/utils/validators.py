from typing import Optional
import re


def validate_session_id(session_id: str) -> bool:
    """
    Validate session ID format (UUID).

    Args:
        session_id: Session ID string

    Returns:
        True if valid UUID format
    """
    uuid_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(uuid_pattern, session_id, re.IGNORECASE))


def validate_filename(filename: str) -> bool:
    """
    Validate uploaded filename is safe.

    Args:
        filename: Original filename

    Returns:
        True if safe filename
    """
    if not filename:
        return False

    # Check for path traversal attempts
    if '..' in filename or '/' in filename or '\\' in filename:
        return False

    # Check for allowed extensions
    allowed_extensions = ['.jpg', '.jpeg', '.png', '.webp']
    return any(filename.lower().endswith(ext) for ext in allowed_extensions)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename by removing unsafe characters.

    Args:
        filename: Original filename

    Returns:
        Sanitized filename
    """
    # Remove path components
    filename = filename.split('/')[-1].split('\\')[-1]

    # Remove unsafe characters
    filename = re.sub(r'[^a-zA-Z0-9._-]', '', filename)

    return filename or 'image.jpg'
