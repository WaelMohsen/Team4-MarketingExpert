from __future__ import annotations

import os
import json
import logging
from typing import List, Dict, Any, Optional

from .prompt_saver import save_llm_prompt
from src.shared.utils.observability import observe

# Native Langfuse OpenAI Integration
from langfuse.openai import OpenAI
from openai import OpenAIError

logger = logging.getLogger(__name__)

class LLMApiClient:
    """
    Abstraction layer over OpenAI API.
    Uses native Langfuse OpenAI integration for automatic tracing, token tracking, and metadata.
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        temperature: float = 0.3,
        max_output_tokens: int = 1200,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY not found.")
        
        # This client automatically sends traces to Langfuse
        self.client = OpenAI(api_key=self.api_key)
        self.model = model or "gpt-5-mini"
        self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    @observe()
    def generate(self, messages: List[Dict[str, str]], save_dir: Optional[str] = None, prompt_name: str = "prompt") -> str:
        """Sends messages to the model. Tracing is handled automatically."""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_completion_tokens=self.max_output_tokens,
                # Langfuse native parameters: name and metadata
                name=prompt_name,
                metadata={"prompt_name": prompt_name}
            )

            result = response.choices[0].message.content.strip()
            
            if save_dir:
                save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)

            return result

        except OpenAIError as e:
            logger.error(f"OpenAI API error: {e}")
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e
        except Exception as e:
            logger.error(f"Unexpected LLM error: {e}")
            raise RuntimeError(f"Unexpected LLM error: {str(e)}") from e

    @observe()
    def generate_json(self, messages: List[Dict[str, str]], response_format: Optional[Any] = None, save_dir: Optional[str] = None, prompt_name: str = "prompt") -> Dict[str, Any]:
        """
        Forces JSON output with a retry mechanism for schema validation.
        Utilizes Langfuse native OpenAI integration for structured outputs.
        """
        max_retries = 1
        retry_count = 0
        last_error = None

        schema_version = getattr(response_format, "__version__", "1.0.0") if response_format else "unknown"

        while retry_count <= max_retries:
            try:
                if response_format:
                    # Use the stable 'parse' method for Pydantic-based structured outputs
                    # Passing name and metadata directly for Langfuse
                    response = self.client.chat.completions.parse(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_completion_tokens=self.max_output_tokens,
                        response_format=response_format,
                        name=prompt_name,
                        metadata={
                            "schema_version": schema_version,
                            "prompt_name": prompt_name,
                            "retry_count": retry_count
                        }
                    )
                    
                    parsed_obj = response.choices[0].message.parsed
                    
                    if save_dir and retry_count == 0:
                        save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)

                    # Return as dict for pipeline compatibility
                    return parsed_obj.model_dump() if hasattr(parsed_obj, "model_dump") else parsed_obj
                else:
                    # standard JSON mode
                    response = self.client.chat.completions.create(
                        model=self.model,
                        messages=messages,
                        temperature=self.temperature,
                        max_completion_tokens=self.max_output_tokens,
                        response_format={"type": "json_object"},
                        name=prompt_name,
                        metadata={"prompt_name": prompt_name}
                    )
                    
                    if save_dir and retry_count == 0:
                        save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)
                        
                    return json.loads(response.choices[0].message.content)

            except (OpenAIError, json.JSONDecodeError, Exception) as e:
                logger.warning(f"JSON Generation attempt {retry_count + 1} failed: {e}")
                last_error = e
                retry_count += 1
                if retry_count > max_retries:
                    break

        raise RuntimeError(f"Failed to generate valid JSON after retries: {str(last_error)}")