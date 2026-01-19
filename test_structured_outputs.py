"""Test script to verify structured output improvements."""

import json
from app.services.vision_service import vision_service


def test_validate_materials():
    """Test material validation and structuring."""
    print("Testing material validation...")

    # Test with dict materials
    materials_dict = [
        {"name": "rubber gasket", "category": "plumbing"},
        {"name": "WD-40", "category": "lubricant"}  # Should be handled by normalizer
    ]
    result = vision_service._validate_materials(materials_dict)
    print(f"Dict materials: {json.dumps(result, indent=2)}")

    # Test with string materials
    materials_string = ["screwdriver", "wrench"]
    result = vision_service._validate_materials(materials_string)
    print(f"String materials: {json.dumps(result, indent=2)}")

    # Test with mixed
    materials_mixed = [
        {"name": "teflon tape", "category": "plumbing", "search_query": "plumbing teflon tape"},
        "adjustable wrench"
    ]
    result = vision_service._validate_materials(materials_mixed)
    print(f"Mixed materials: {json.dumps(result, indent=2)}")
    print()


def test_validate_repair_steps():
    """Test repair step validation and structuring."""
    print("Testing repair step validation...")

    # Test with dict steps
    steps_dict = [
        {"step": 1, "title": "Turn off water", "instruction": "Locate shut-off valve"},
        {"title": "Remove old part", "instruction": "Use wrench to loosen", "safety_tip": "Wear gloves"}
    ]
    result = vision_service._validate_repair_steps(steps_dict)
    print(f"Dict steps: {json.dumps(result, indent=2)}")

    # Test with string steps
    steps_string = [
        "Turn off water supply",
        "Remove old flapper",
        "Install new flapper"
    ]
    result = vision_service._validate_repair_steps(steps_string)
    print(f"String steps: {json.dumps(result, indent=2)}")
    print()


def test_validate_diagnosis():
    """Test full diagnosis validation."""
    print("Testing full diagnosis validation...")

    # Test with incomplete diagnosis
    diagnosis_incomplete = {
        "diagnosis": "Broken toilet flapper",
        "confidence": 0.9,
        "materials": ["rubber flapper"],
        "tools": ["adjustable wrench"]
    }
    result = vision_service._validate_and_structure_diagnosis(diagnosis_incomplete)
    print(f"Incomplete diagnosis: {json.dumps(result, indent=2)}")

    # Test with complete diagnosis
    diagnosis_complete = {
        "object_identified": "Toilet",
        "failure_mode": "Running water",
        "diagnosis": "Worn flapper valve causing water leak",
        "confidence": 0.95,
        "issue_type": "plumbing",
        "diy_feasible": True,
        "materials": [
            {"name": "rubber flapper valve", "category": "plumbing", "search_query": "toilet flapper"}
        ],
        "tools_required": ["adjustable wrench", "bucket"],
        "repair_steps": [
            {"step": 1, "title": "Turn off water", "instruction": "Turn valve clockwise", "safety_tip": ""},
            {"step": 2, "title": "Remove old flapper", "instruction": "Unhook from chain", "safety_tip": ""}
        ],
        "warnings": ["Ensure water is off before starting"],
        "followup_questions": ["Do you have the tools?"]
    }
    result = vision_service._validate_and_structure_diagnosis(diagnosis_complete)
    print(f"Complete diagnosis: {json.dumps(result, indent=2)}")

    # Test with out-of-range confidence
    diagnosis_bad_confidence = {
        "diagnosis": "Test",
        "confidence": 1.5  # Out of range
    }
    result = vision_service._validate_and_structure_diagnosis(diagnosis_bad_confidence)
    print(f"\nOut-of-range confidence (should be clamped to 1.0): {result['confidence']}")
    print()


if __name__ == "__main__":
    print("=" * 60)
    print("STRUCTURED OUTPUT VALIDATION TESTS")
    print("=" * 60)
    print()

    try:
        test_validate_materials()
        test_validate_repair_steps()
        test_validate_diagnosis()

        print("=" * 60)
        print("ALL TESTS COMPLETED SUCCESSFULLY")
        print("=" * 60)
    except Exception as e:
        print(f"\nERROR: {e}")
        import traceback
        traceback.print_exc()
