"""DSPy signatures for structured diagnosis outputs."""

import dspy
from typing import List, Dict


class DiagnosisSignature(dspy.Signature):
    """
    Signature for DIY repair diagnosis from image.

    CRITICAL RULES:
    - NO brand names (e.g., "WD-40" → "penetrating lubricant")
    - NO product SKUs or model numbers
    - NO URLs or links
    - Only generic, searchable product names
    """

    # Inputs
    image_description: str = dspy.InputField(desc="Description of what you see in the image")
    context: str = dspy.InputField(desc="Additional context from previous conversation", default="")

    # Outputs
    object_identified: str = dspy.OutputField(desc="What object is in the image")
    failure_mode: str = dspy.OutputField(desc="What is broken or damaged")
    diagnosis: str = dspy.OutputField(desc="Summary diagnosis of the issue")
    confidence: float = dspy.OutputField(desc="Confidence score (0.0-1.0)")
    issue_type: str = dspy.OutputField(desc="Category: plumbing, electrical, door, furniture, appliance, etc.")
    diy_feasible: bool = dspy.OutputField(desc="Can this be repaired as a DIY project?")
    materials_json: str = dspy.OutputField(desc="JSON array of materials needed (generic names only, NO brands)")
    tools_json: str = dspy.OutputField(desc="JSON array of tools needed")
    steps_json: str = dspy.OutputField(desc="JSON array of repair steps")
    warnings_json: str = dspy.OutputField(desc="JSON array of safety warnings")
    followup_json: str = dspy.OutputField(desc="JSON array of suggested follow-up questions")


class FollowUpSignature(dspy.Signature):
    """Signature for follow-up questions with context."""

    # Inputs
    previous_diagnosis: str = dspy.InputField(desc="Previous diagnosis context")
    question: str = dspy.InputField(desc="User's follow-up question")

    # Outputs
    answer: str = dspy.OutputField(desc="Answer to the follow-up question")
    materials_json: str = dspy.OutputField(desc="JSON array of any additional materials mentioned")
    steps_json: str = dspy.OutputField(desc="JSON array of any additional steps")
    warnings_json: str = dspy.OutputField(desc="JSON array of any safety warnings")
