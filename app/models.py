from typing import Optional
from pydantic import BaseModel, Field


class Material(BaseModel):
    """Material needed for repair."""
    name: str = Field(..., description="Generic product name")
    category: str = Field(..., description="Material category (plumbing, door, furniture, tool, electrical)")
    search_query: str = Field(..., description="Search query for hardware stores")


class RepairStep(BaseModel):
    """Single repair step."""
    step: int = Field(..., description="Step number")
    title: str = Field(..., description="Step title")
    instruction: str = Field(..., description="Detailed instruction")
    safety_tip: Optional[str] = Field(None, description="Safety warning for this step")


class TimingInfo(BaseModel):
    """Timing breakdown for request."""
    total_time: float = Field(..., description="Total processing time in seconds")
    image_processing_time: float = Field(0.0, description="Image validation and preprocessing time")
    cache_lookup_time: float = Field(0.0, description="Cache lookup time")
    openai_api_time: float = Field(0.0, description="OpenAI API call time")
    normalization_time: float = Field(0.0, description="Material normalization time")
    cache_source: Optional[str] = Field(None, description="Cache hit source (exact, perceptual, miss)")


class DiagnosisResponse(BaseModel):
    """Response from diagnosis endpoint."""
    diagnosis: str = Field(..., description="Description of what is broken")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score 0-1")
    issue_type: Optional[str] = Field(None, description="Type of issue (plumbing, door, furniture, electrical)")
    professional_help_recommended: Optional[str] = Field(None, description="Professional type if needed (electrician, plumber, etc.)")
    professional_help_reason: Optional[str] = Field(None, description="Reason professional help is recommended")
    estimated_time: Optional[str] = Field(None, description="Estimated repair time")
    difficulty: Optional[str] = Field(None, description="Difficulty level (easy, moderate, hard)")
    materials: list[Material] = Field(default_factory=list, description="Required materials")
    tools_required: list[str] = Field(default_factory=list, description="Required tools")
    repair_steps: list[RepairStep] = Field(default_factory=list, description="Step-by-step repair instructions")
    warnings: list[str] = Field(default_factory=list, description="Safety warnings")
    followup_questions: list[str] = Field(default_factory=list, description="Suggested follow-up questions")
    session_id: Optional[str] = Field(None, description="Session ID for follow-up questions")
    timing: Optional[TimingInfo] = Field(None, description="Timing breakdown")


class FollowupResponse(BaseModel):
    """Response from follow-up question."""
    answer: str = Field(..., description="Answer to the follow-up question")
    additional_steps: list[RepairStep] = Field(default_factory=list, description="Additional steps if relevant")
    additional_materials: list[Material] = Field(default_factory=list, description="Additional materials if relevant")
    warnings: list[str] = Field(default_factory=list, description="Additional warnings if relevant")
    session_id: str = Field(..., description="Session ID")


class ErrorResponse(BaseModel):
    """Error response."""
    error: str = Field(..., description="Error category")
    message: str = Field(..., description="User-friendly error message")
    details: Optional[str] = Field(None, description="Technical details")
    retry_after: Optional[int] = Field(None, description="Seconds to wait before retry")
