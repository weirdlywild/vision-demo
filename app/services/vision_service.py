import base64
import json
import time
from typing import Dict, Optional, List
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

    async def diagnose_image(self, image_bytes: bytes, context: str = "") -> Dict:
        """
        Diagnose an image using GPT-4o Vision with DSPy structured outputs.

        Args:
            image_bytes: Processed image bytes
            context: Optional context for follow-up questions

        Returns:
            Diagnosis dictionary with validated structure

        Raises:
            VisionServiceError: If API call fails
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

        # Ultra-concise prompt for speed
        enhanced_prompt = """Broken item analysis. JSON format. No brands/SKUs/URLs.
{"object_identified":"", "failure_mode":"", "diagnosis":"", "confidence":0.8, "issue_type":"other", "diy_feasible":true, "materials":[{"name":"", "category":"", "search_query":""}], "tools_required":[], "repair_steps":[{"step":1, "title":"", "instruction":"", "safety_tip":""}], "warnings":[], "followup_questions":[]}"""

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
                            "detail": "auto"
                        }
                    }
                ]
            }
        ]

        # Call GPT-4o with retry logic
        response_json = await self._call_openai_with_retry(messages)

        # Parse and validate response with DSPy-inspired structure validation
        try:
            diagnosis = json.loads(response_json)
            diagnosis = self._validate_and_structure_diagnosis(diagnosis)
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
        response_json = await self._call_openai_with_retry(messages)

        # Parse and validate response with DSPy-inspired structure validation
        try:
            followup_response = json.loads(response_json)
            followup_response = self._validate_and_structure_diagnosis(followup_response)
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

    async def _call_openai_with_retry(self, messages: list) -> str:
        """
        Call OpenAI API with exponential backoff retry.

        Args:
            messages: Chat messages

        Returns:
            Response content string

        Raises:
            VisionServiceError: If all retries fail
        """
        max_retries = settings.max_retries
        backoff_factor = settings.backoff_factor

        for attempt in range(max_retries):
            try:
                response = await self.client.chat.completions.create(
                    model=settings.openai_model,
                    messages=messages,
                    max_tokens=settings.openai_max_tokens,
                    temperature=settings.openai_temperature,
                    response_format={"type": "json_object"}
                )

                return response.choices[0].message.content

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
