import base64
import json
import time
from typing import Dict, Optional
from openai import AsyncOpenAI
from openai import APIError, RateLimitError, APITimeoutError
from app.config import settings
from app.prompts import load_prompt


class VisionServiceError(Exception):
    """Raised when vision service encounters an error."""
    pass


class VisionService:
    """Handles GPT-4o Vision API integration."""

    def __init__(self):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.system_prompt = load_prompt("system_prompt.txt")
        self.initial_prompt = load_prompt("initial_diagnosis.txt")
        self.followup_prompt = load_prompt("followup_prompt.txt")

    async def diagnose_image(self, image_bytes: bytes, context: str = "") -> Dict:
        """
        Diagnose an image using GPT-4o Vision.

        Args:
            image_bytes: Processed image bytes
            context: Optional context for follow-up questions

        Returns:
            Diagnosis dictionary

        Raises:
            VisionServiceError: If API call fails
        """
        # Encode image to base64
        base64_image = base64.b64encode(image_bytes).decode('utf-8')

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
                        "text": self.initial_prompt
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
        response_json = await self._call_openai_with_retry(messages)

        # Parse and validate response
        try:
            diagnosis = json.loads(response_json)
        except json.JSONDecodeError as e:
            raise VisionServiceError(f"Invalid JSON response from GPT: {str(e)}")

        return diagnosis

    async def handle_followup(
        self,
        question: str,
        context: str,
        previous_diagnosis: Optional[Dict] = None
    ) -> Dict:
        """
        Handle follow-up question with context.

        Args:
            question: User's follow-up question
            context: Session context summary
            previous_diagnosis: Previous diagnosis for reference

        Returns:
            Follow-up response dictionary

        Raises:
            VisionServiceError: If API call fails
        """
        # Format the follow-up prompt with context
        formatted_prompt = self.followup_prompt.format(
            context=context,
            question=question
        )

        # Build messages
        messages = [
            {
                "role": "system",
                "content": self.system_prompt
            },
            {
                "role": "user",
                "content": formatted_prompt
            }
        ]

        # Call GPT-4o with retry logic
        response_json = await self._call_openai_with_retry(messages)

        # Parse and validate response
        try:
            followup_response = json.loads(response_json)
        except json.JSONDecodeError as e:
            raise VisionServiceError(f"Invalid JSON response from GPT: {str(e)}")

        return followup_response

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
