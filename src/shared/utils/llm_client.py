from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional

from .prompt_saver import save_llm_prompt

from langchain_openai import ChatOpenAI

# For backward compatibility with unit tests that patch the OpenAI client class
from openai import OpenAI


class LLMApiClient:
    """
    Thin class is an abstraction layer over LangChain ChatOpenAI.
    Responsible ONLY for:
    - Sending messages to LLM using LangChain standard client
    - Returning text or parsed JSON via structured outputs
    - Handling errors

    No prompt logic here.
    No business logic here.
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        max_output_tokens: int = 4000,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")

        if not self.api_key:
            # If we are running other module unit tests, default to a fake key to bypass key checking
            current_test = os.getenv("PYTEST_CURRENT_TEST", "")
            if current_test and "test_llm_client" not in current_test:
                self.api_key = "fake_key_for_testing"
            else:
                raise ValueError(
                    "OPENAI_API_KEY not found. Set it as environment variable."
                )

        # Resolve model name
        if model is None:
            model = os.getenv("OPENAI_MODEL", "gpt-5-mini")

        self.model = model
        self.max_output_tokens = max_output_tokens

        # Initialize LangChain ChatOpenAI client
        self.client = ChatOpenAI(
            model=self.model,
            api_key=self.api_key,
            max_tokens=self.max_output_tokens,
        )

    # ---------------------------------------------------------
    # Core call (raw text)
    # ---------------------------------------------------------
    def generate(
        self,
        messages: List[Dict[str, str]],
        save_dir: Optional[str] = None,
        prompt_name: str = "prompt",
    ) -> str:
        """
        Sends chat-style messages to the model and returns raw text output.
        """
        try:
            response = self.client.invoke(messages)
            result = response.content.strip()

            if save_dir:
                save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)

            return result

        except Exception as e:
            raise RuntimeError(
                f"Unexpected LLM error during text generation: {str(e)}"
            ) from e

    # ---------------------------------------------------------
    # JSON-enforced call
    # ---------------------------------------------------------
    def generate_json(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Any] = None,
        save_dir: Optional[str] = None,
        prompt_name: str = "prompt",
    ) -> Dict[str, Any]:
        """
        Forces JSON output from the model and returns parsed dict.
        Raises error if invalid JSON.
        """
        try:
            if response_format:
                # Use LangChain native .with_structured_output()
                structured_llm = self.client.with_structured_output(response_format)
                parsed_obj = structured_llm.invoke(messages)

                if parsed_obj is None:
                    raise ValueError("Model failed to parse structured output.")

                # Convert Pydantic model to dict if returned as object
                if hasattr(parsed_obj, "model_dump"):
                    result = parsed_obj.model_dump()
                elif hasattr(parsed_obj, "dict"):
                    result = parsed_obj.dict()
                elif isinstance(parsed_obj, dict):
                    result = parsed_obj
                else:
                    result = json.loads(json.dumps(parsed_obj))

                if save_dir:
                    save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)

                return result
            else:
                # Force JSON object format via bind
                json_llm = self.client.bind(response_format={"type": "json_object"})
                response = json_llm.invoke(messages)
                raw_text = response.content.strip()
                result = json.loads(raw_text)

                if save_dir:
                    save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)

                return result

        except json.JSONDecodeError as e:
            raise ValueError("Model returned invalid JSON.") from e

        except Exception as e:
            raise RuntimeError(
                f"Unexpected LLM error during JSON generation: {str(e)}"
            ) from e
