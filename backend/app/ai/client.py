"""Robust AI client with retry logic and fallbacks."""

import os
import time
import logging
from typing import Optional, Any
from openai import OpenAI, RateLimitError, APIError, Timeout
from openai.types import Completion

from app.core.config import get_settings
from app.core.errors import ErrorCode

logger = logging.getLogger(__name__)
settings = get_settings()


class OpenAIClient:
    """Robust OpenAI client with retry logic and fallbacks."""
    
    # Retry configuration
    MAX_RETRIES = 3
    RETRY_DELAYS = [1, 2, 4]  # Exponential backoff seconds
    TIMEOUT = 30  # Request timeout
    
    # Token limits per request
    MAX_TOKENS = 4000
    MAX_OUTPUT_TOKENS = 2000
    
    # Fallback responses for when AI is unavailable
    FALLBACK_RESPONSES = {
        "tutor": "I apologize, but I'm currently unable to process your request. Please try again in a few moments. If the issue persists, please contact support.",
        "quiz": "[]",
        "exercise": "[]",
        "corrector": {"grade": "error", "feedback": "Unable to process at this time. Please try again."},
        "explain": "I apologize, but I'm currently unavailable. Please try again later.",
    }
    
    def __init__(self, model: str = "gpt-4o-mini"):
        self.model = model
        self._client: Optional[OpenAI] = None
    
    @property
    def client(self) -> OpenAI:
        """Lazy initialization of OpenAI client."""
        if self._client is None:
            api_key = settings.openai_api_key
            if not api_key:
                logger.warning("OpenAI API key not configured")
            
            self._client = OpenAI(
                api_key=api_key or os.getenv("OPENAI_API_KEY", "dummy"),
                max_retries=0,  # We handle retries ourselves
            )
        return self._client
    
    def is_available(self) -> bool:
        """Check if OpenAI API is available."""
        if not settings.openai_api_key:
            return False
        try:
            # Simple test call
            self.client.models.list()
            return True
        except Exception as e:
            logger.warning(f"OpenAI not available: {e}")
            return False
    
    def _retry_with_backoff(
        self,
        func,
        *args,
        **kwargs
    ) -> Any:
        """Execute function with exponential backoff retry."""
        last_exception = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                return func(*args, **kwargs)
            except RateLimitError as e:
                logger.warning(f"Rate limit hit (attempt {attempt + 1}): {e}")
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAYS[attempt])
            except Timeout as e:
                logger.warning(f"Timeout (attempt {attempt + 1}): {e}")
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAYS[attempt])
            except APIError as e:
                logger.warning(f"API error (attempt {attempt + 1}): {e}")
                last_exception = e
                if attempt < self.MAX_RETRIES - 1:
                    time.sleep(self.RETRY_DELAYS[attempt])
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                raise
        
        # All retries exhausted
        raise last_exception
    
    def _make_request(
        self,
        prompt: str,
        system_prompt: str,
        max_tokens: int = 500,
        temperature: float = 0.7,
    ) -> str:
        """Make a chat completion request with retries."""
        if not self.is_available():
            return self.FALLBACK_RESPONSES.get("tutor", "Service unavailable")
        
        try:
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt[:4000]},  # Cap input
                ],
                temperature=temperature,
                max_tokens=min(max_tokens, self.MAX_OUTPUT_TOKENS),
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            return self.FALLBACK_RESPONSES.get("tutor", "Service unavailable")
    
    def generate_quiz_json(
        self,
        prompt: str,
        system_prompt: str,
        max_questions: int = 10,
    ) -> list:
        """Generate quiz with JSON response."""
        if not self.is_available():
            return []
        
        try:
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Generate {max_questions} questions: {prompt[:2000]}"},
                ],
                temperature=0.7,
                max_tokens=min(max_questions * 200, self.MAX_OUTPUT_TOKENS),
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "[]"
            # Try to parse as JSON
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"Quiz generation failed: {e}")
            return []
    
    def correct_assignment(
        self,
        assignment_text: str,
        question: str,
        system_prompt: str,
    ) -> dict:
        """Auto-correct assignment."""
        if not self.is_available():
            return {
                "grade": "error",
                "feedback": self.FALLBACK_RESPONSES["corrector"]["feedback"],
                "correct_answer": None,
            }
        
        prompt = f"""Question: {question}

Student Answer: {assignment_text}

Provide your correction in JSON format:
{{"grade": "correct|incorrect|partial", "feedback": "...", "correct_answer": "..."}}"""
        
        try:
            response = self._retry_with_backoff(
                self.client.chat.completions.create,
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt[:3000]},
                ],
                temperature=0.3,
                max_tokens=500,
                response_format={"type": "json_object"},
            )
            content = response.choices[0].message.content or "{}"
            import json
            return json.loads(content)
        except Exception as e:
            logger.error(f"Correction failed: {e}")
            return self.FALLBACK_RESPONSES["corrector"]


def create_ai_client(model: str = "gpt-4o-mini") -> OpenAIClient:
    """Factory function to create AI client."""
    return OpenAIClient(model=model)