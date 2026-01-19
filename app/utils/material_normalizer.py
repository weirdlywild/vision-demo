import re
from typing import List, Dict


class MaterialNormalizer:
    """Removes brand names, SKUs, and URLs from material descriptions."""

    # Common brand names to remove (case-insensitive)
    BRAND_PATTERNS = [
        # Tools & Hardware
        r'\b(dewalt|makita|milwaukee|bosch|craftsman|stanley|irwin|husky)\b',
        # Adhesives & Chemicals
        r'\b(gorilla|loctite|3m|wd-?40|clr|goo gone|goof off)\b',
        # Paint & Finishes
        r'\b(rustoleum|rust-oleum|krylon|minwax|behr|sherwin williams|benjamin moore)\b',
        # Plumbing
        r'\b(kohler|american standard|moen|delta|pfister|fluidmaster)\b',
        # Electrical
        r'\b(leviton|lutron|eaton|square d|ge|philips|sylvania)\b',
        # Fasteners
        r'\b(tapcon|hilti|ramset|red head)\b',
        # Batteries
        r'\b(duracell|energizer|rayovac|panasonic)\b',
        # Lumber & Building
        r'\b(simpson strong-tie|tyvek|zip system)\b',
        # General retail
        r'\b(home depot|lowes|ace hardware|true value|menards)\b',
    ]

    # URL pattern
    URL_PATTERN = r'https?://[^\s]+'

    # SKU patterns (alphanumeric codes)
    SKU_PATTERNS = [
        r'\b[A-Z]{2,}[-_]?[0-9]{3,}[-_]?[A-Z0-9]*\b',  # ABC-1234, ABC1234
        r'\b[0-9]{5,}[-_]?[A-Z0-9]*\b',  # 12345-ABC
        r'\bmodel\s*#?\s*[A-Z0-9-]+\b',  # Model #ABC-123
        r'\bsku\s*#?\s*[A-Z0-9-]+\b',  # SKU #123456
        r'\bitem\s*#?\s*[A-Z0-9-]+\b',  # Item #789
    ]

    # Generic replacements for common branded terms
    GENERIC_MAPPING = {
        'wd-40': 'penetrating lubricant',
        'wd40': 'penetrating lubricant',
        'gorilla glue': 'strong adhesive',
        'super glue': 'cyanoacrylate adhesive',
        'krazy glue': 'cyanoacrylate adhesive',
        'duct tape': 'multi-purpose tape',
        'scotch tape': 'transparent adhesive tape',
        'plexiglass': 'acrylic sheet',
        'styrofoam': 'expanded polystyrene foam',
        'kleenex': 'facial tissue',
        'saran wrap': 'plastic food wrap',
        'ziploc': 'resealable plastic bag',
    }

    @classmethod
    def normalize_text(cls, text: str) -> str:
        """
        Remove brands, URLs, and SKUs from text.

        Args:
            text: Input text potentially containing brands/SKUs/URLs

        Returns:
            Cleaned text
        """
        if not text:
            return text

        original = text.lower()

        # Remove URLs
        text = re.sub(cls.URL_PATTERN, '', text, flags=re.IGNORECASE)

        # Remove brand names
        for pattern in cls.BRAND_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Remove SKUs
        for pattern in cls.SKU_PATTERNS:
            text = re.sub(pattern, '', text, flags=re.IGNORECASE)

        # Apply generic mapping
        text_lower = text.lower()
        for branded, generic in cls.GENERIC_MAPPING.items():
            if branded in text_lower:
                # Replace while preserving case context
                text = re.sub(re.escape(branded), generic, text, flags=re.IGNORECASE)

        # Clean up whitespace
        text = ' '.join(text.split())

        # If text became too short after cleaning, return a warning
        if len(text.strip()) < 3 and len(original) > 10:
            return "generic replacement part"

        return text.strip()

    @classmethod
    def normalize_materials(cls, materials: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """
        Normalize all materials in a list.

        Args:
            materials: List of material dictionaries

        Returns:
            List of normalized materials
        """
        normalized = []

        for material in materials:
            normalized_material = material.copy()

            # Normalize name field
            if 'name' in normalized_material:
                normalized_material['name'] = cls.normalize_text(normalized_material['name'])

            # Normalize search_query field
            if 'search_query' in normalized_material:
                normalized_material['search_query'] = cls.normalize_text(normalized_material['search_query'])

            # Normalize category field
            if 'category' in normalized_material:
                normalized_material['category'] = cls.normalize_text(normalized_material['category'])

            normalized.append(normalized_material)

        return normalized

    @classmethod
    def has_brand_names(cls, text: str) -> bool:
        """
        Check if text contains brand names.

        Args:
            text: Text to check

        Returns:
            True if brand names detected
        """
        if not text:
            return False

        text_lower = text.lower()

        # Check brand patterns
        for pattern in cls.BRAND_PATTERNS:
            if re.search(pattern, text_lower):
                return True

        return False

    @classmethod
    def has_urls(cls, text: str) -> bool:
        """
        Check if text contains URLs.

        Args:
            text: Text to check

        Returns:
            True if URLs detected
        """
        if not text:
            return False

        return bool(re.search(cls.URL_PATTERN, text))

    @classmethod
    def has_skus(cls, text: str) -> bool:
        """
        Check if text contains SKUs.

        Args:
            text: Text to check

        Returns:
            True if SKUs detected
        """
        if not text:
            return False

        for pattern in cls.SKU_PATTERNS:
            if re.search(pattern, text, flags=re.IGNORECASE):
                return True

        return False

    @classmethod
    def validate_materials(cls, materials: List[Dict[str, str]]) -> tuple[bool, List[str]]:
        """
        Validate that materials don't contain brands, URLs, or SKUs.

        Args:
            materials: List of material dictionaries

        Returns:
            Tuple of (is_valid, list_of_violations)
        """
        violations = []

        for i, material in enumerate(materials):
            material_name = material.get('name', '')

            if cls.has_brand_names(material_name):
                violations.append(f"Material {i+1} contains brand names: {material_name}")

            if cls.has_urls(material_name):
                violations.append(f"Material {i+1} contains URLs: {material_name}")

            if cls.has_skus(material_name):
                violations.append(f"Material {i+1} contains SKUs: {material_name}")

        return len(violations) == 0, violations
