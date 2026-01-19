import base64
import json
import time
from typing import Dict, Optional, List, Tuple
from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APITimeoutError
from app.config import settings
from app.prompts import load_prompt


class VisionServiceError(Exception):
    """Raised when vision service encounters an error."""
    pass


class VisionService:
    """
    Handles GPT-4o Vision API integration with enhanced structured outputs.

    Uses DSPy-inspired techniques for better prompt engineering and validation:
    - Explicit output structure requirements in prompts
    - Comprehensive field validation and defaults
    - Type conversion and normalization
    - Consistent error handling
    """

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.system_prompt = load_prompt("system_prompt.txt")
        self.initial_prompt = load_prompt("initial_diagnosis.txt")
        self.followup_prompt = load_prompt("followup_prompt.txt")

    async def diagnose_image(self, image_bytes: bytes, context: str = "", model: str = None) -> Dict:
        """
        Diagnose an image using GPT-4o Vision with DSPy structured outputs.

        Args:
            image_bytes: Processed image bytes
            context: Optional context for follow-up questions
            model: OpenAI model to use (defaults to settings.openai_model)

        Returns:
            Diagnosis dictionary with validated structure

        Raises:
            VisionServiceError: If API call fails
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Detailed analysis prompt
        enhanced_prompt = """Analyze this image of a broken/damaged household item with expert attention to detail.

STEP 1 - CAREFUL OBSERVATION:
- Examine every visible detail in the image
- Identify the object type and its current condition
- Look for damage patterns: cracks, breaks, wear, corrosion, discoloration, leaks, misalignment
- Check for secondary issues or hidden problems indicated by visual clues

STEP 2 - ROOT CAUSE ANALYSIS:
- Determine WHY this failure occurred (not just what failed)
- Consider: age/wear, improper installation, stress/overload, manufacturing defect, environmental factors

STEP 3 - COMPLEXITY ASSESSMENT:
- Evaluate repair difficulty honestly
- Determine if this is DIY-appropriate or requires professional help
- Consider safety risks and required skill level

STEP 4 - COMPREHENSIVE REPAIR PLAN:
- List ALL tools needed upfront
- Provide detailed step-by-step instructions with measurements where relevant
- Include safety warnings for each dangerous step
- Suggest 3-4 helpful follow-up questions the user might ask

OUTPUT: Return valid JSON only (no markdown, no explanations outside JSON)
Required format: {"object_identified":"specific item", "failure_mode":"what broke and why", "diagnosis":"detailed explanation", "confidence":0.0-1.0, "issue_type":"plumbing|electrical|door|furniture|appliance|other", "diy_feasible":true|false, "professional_help_recommended":"electrician|plumber|appliance technician|carpenter|none", "professional_help_reason":"reason if applicable", "estimated_time":"realistic estimate", "difficulty":"easy|moderate|hard", "materials":[{"name":"generic product", "category":"type", "search_query":"search term"}], "tools_required":["all tools needed"], "repair_steps":[{"step":1, "title":"step name", "instruction":"detailed instruction", "safety_tip":"warning"}], "warnings":["critical safety warnings"], "followup_questions":["helpful questions"]}

CRITICAL: NO brand names, NO URLs, NO SKUs. Use generic product names only."""

        # Build messages
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": enhanced_prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/jpeg;base64,{base64_image}",
                            "detail": "high"
                        }
                    }
                ]
            }
        ]

        # Call GPT-4o with retry logic
        response_json, usage_data = await self._call_openai_with_retry(messages, model or settings.openai_model)

        # Parse and validate response with DSPy-inspired structure validation
        try:
            diagnosis = json.loads(response_json)
            diagnosis = self._validate_and_structure_diagnosis(diagnosis)
            # Add usage data to diagnosis
            diagnosis['usage'] = usage_data
        except json.JSONDecodeError as e:
            raise VisionServiceError(f"Invalid JSON response from GPT: {str(e)}")
        except Exception as e:
            raise VisionServiceError(f"Failed to structure diagnosis: {str(e)}")

        return diagnosis

    async def handle_followup(
        self,
        question: str,
        context: str,
        previous_diagnosis: Optional[Dict] = None
    ) -> Dict:
        """
        Handle follow-up question with context using DSPy structured outputs.

        Args:
            question: User's follow-up question
            context: Session context summary
            previous_diagnosis: Previous diagnosis for reference

        Returns:
            Follow-up response dictionary with validated structure

        Raises:
            VisionServiceError: If API call fails
        """
        # Enhanced follow-up prompt with DSPy-style instructions
        enhanced_prompt = f"""
{self.followup_prompt.format(context=context, question=question)}

CRITICAL OUTPUT REQUIREMENTS:
- Return ONLY valid JSON
- NO brand names (use generic terms)
- NO product SKUs or model numbers
- NO URLs or links

Required JSON structure:
{{
    "diagnosis": "answer to the question",
    "confidence": 0.0-1.0,
    "materials": [{{"name": "generic name", "category": "category", "search_query": "search term"}}],
    "tools_required": ["tool1"],
    "repair_steps": [{{"step": 1, "title": "title", "instruction": "instruction", "safety_tip": "tip"}}],
    "warnings": ["warning if applicable"],
    "followup_questions": ["suggested question"]
}}
"""

        # Build messages
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": enhanced_prompt
            }
        ]

        # Call GPT-4o with retry logic
        response_json, usage_data = await self._call_openai_with_retry(messages)

        # Parse and validate response with DSPy-inspired structure validation
        try:
            followup_response = json.loads(response_json)
            followup_response = self._validate_and_structure_diagnosis(followup_response)
            # Add usage data to response
            followup_response['usage'] = usage_data
        except json.JSONDecodeError as e:
            raise VisionServiceError(f"Invalid JSON response from GPT: {str(e)}")
        except Exception as e:
            raise VisionServiceError(f"Failed to structure follow-up: {str(e)}")

        return followup_response

    def _validate_and_structure_diagnosis(self, diagnosis: Dict) -> Dict:
        """
        Validate and structure diagnosis output using DSPy-inspired validation.

        Args:
            diagnosis: Raw diagnosis dictionary from GPT

        Returns:
            Validated and structured diagnosis

        Raises:
            ValueError: If required fields are missing or invalid
        """
        # Required fields with defaults
        structured = {
            "object_identified": diagnosis.get("object_identified", "Unknown object"),
            "failure_mode": diagnosis.get("failure_mode", "Unable to determine"),
            "diagnosis": diagnosis.get("diagnosis", diagnosis.get("object_identified", "Analysis incomplete")),
            "confidence": float(diagnosis.get("confidence", 0.5)),
            "issue_type": diagnosis.get("issue_type", "other"),
            "diy_feasible": bool(diagnosis.get("diy_feasible", True)),
            "professional_help_recommended": diagnosis.get("professional_help_recommended", "none"),
            "professional_help_reason": diagnosis.get("professional_help_reason", ""),
            "estimated_time": diagnosis.get("estimated_time", "Varies"),
            "difficulty": diagnosis.get("difficulty", "moderate"),
            "materials": self._validate_materials(diagnosis.get("materials", [])),
            "tools_required": diagnosis.get("tools_required", diagnosis.get("tools", [])),
            "repair_steps": self._validate_repair_steps(diagnosis.get("repair_steps", [])),
            "warnings": diagnosis.get("warnings", diagnosis.get("safety_warnings", [])),
            "followup_questions": diagnosis.get("followup_questions", [
                "What tools do you already have?",
                "Do you need more detailed instructions for any step?"
            ])
        }

        # Ensure confidence is in valid range
        if not 0.0 <= structured["confidence"] <= 1.0:
            structured["confidence"] = max(0.0, min(1.0, structured["confidence"]))

        return structured

    def _validate_materials(self, materials: List) -> List[Dict]:
        """
        Validate and structure materials list.

        Args:
            materials: Raw materials list

        Returns:
            Validated materials list with proper structure
        """
        validated = []
        for mat in materials:
            if isinstance(mat, dict):
                validated.append({
                    "name": mat.get("name", ""),
                    "category": mat.get("category", "general"),
                    "search_query": mat.get("search_query", mat.get("name", ""))
                })
            elif isinstance(mat, str):
                # Convert string to structured material
                validated.append({
                    "name": mat,
                    "category": "general",
                    "search_query": mat
                })
        return validated

    def _validate_repair_steps(self, steps: List) -> List[Dict]:
        """
        Validate and structure repair steps list.

        Args:
            steps: Raw repair steps list

        Returns:
            Validated repair steps with proper structure
        """
        validated = []
        for i, step in enumerate(steps, 1):
            if isinstance(step, dict):
                validated.append({
                    "step": step.get("step", i),
                    "title": step.get("title", f"Step {i}"),
                    "instruction": step.get("instruction", step.get("description", "")),
                    "safety_tip": step.get("safety_tip", "")
                })
            elif isinstance(step, str):
                # Convert string to structured step
                validated.append({
                    "step": i,
                    "title": f"Step {i}",
                    "instruction": step,
                    "safety_tip": ""
                })
        return validated

    async def _call_openai_with_retry(self, messages: list, model: str = None) -> Tuple[str, Dict]:
        """
        Call OpenAI API with exponential backoff retry.

        Args:
            messages: Chat messages
            model: OpenAI model to use

        Returns:
            Tuple of (response content string, usage dict with token counts)

        Raises:
            VisionServiceError: If all retries fail
        """
        max_retries = settings.max_retries
        backoff_factor = settings.backoff_factor

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=model or settings.openai_model,
                    messages=messages,
                    max_tokens=settings.openai_max_tokens,
                    temperature=settings.openai_temperature,
                    response_format={"type": "json_object"}
                )

                # Extract usage data from response
                usage_data = {
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                    "total_tokens": response.usage.total_tokens if response.usage else 0,
                    "model": model or settings.openai_model
                }

                return response.choices[0].message.content, usage_data

            except RateLimitError as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
                    continue
                raise VisionServiceError(f"Rate limit exceeded: {str(e)}")

            except APITimeoutError as e:
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
                    continue
                raise VisionServiceError(f"API timeout: {str(e)}")

            except APIError as e:
                if attempt < max_retries - 1 and e.status_code >= 500:
                    # Retry on server errors
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
                    continue
                raise VisionServiceError(f"OpenAI API error: {str(e)}")

            except Exception as e:
                raise VisionServiceError(f"Unexpected error: {str(e)}")

        raise VisionServiceError("Max retries exceeded")


# Global vision service instance
vision_service = VisionService()
