
from __future__ import annotations

import os
import json
from typing import List, Dict, Any, Optional

from .prompt_saver import save_llm_prompt

from openai import OpenAI
from openai import OpenAIError


class LLMApiClient:
    """
    Thin class is an abstraction layer over OpenAI Responses API.
    Responsible ONLY for:
    - Sending messages to LLM
    - Returning text or parsed JSON
    - Handling errors

    No prompt logic here.
    No business logic here.    

    Lightweight wrapper around OpenAI Responses API.

    Usage:
        client = LLMApiClient()
        response_text = client.generate(messages)
        response_json = client.generate_json(messages)
    """

    def __init__(
        self,
        model: str = "gpt-5-mini",
        api_key: Optional[str] = None,
        # The model predicts probabilities (P(token | context)) for the next token. Temperature rescales these probabilities before sampling:
        #temperature: float = 0.3,
        max_output_tokens: int = 1200,
    ):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        
        if not self.api_key:
            raise ValueError(
                "OPENAI_API_KEY not found. Set it as environment variable."
            )
        if model is None:
            model = "gpt-5-mini"

        self.client = OpenAI(api_key=self.api_key)
        self.model = model
        #self.temperature = temperature
        self.max_output_tokens = max_output_tokens

    # ---------------------------------------------------------
    # Core call (raw text)
    # ---------------------------------------------------------
    def generate(self, messages: List[Dict[str, str]], save_dir: Optional[str] = None, prompt_name: str = "prompt") -> str:
        """
        Sends chat-style messages to the model and returns raw text output.
        """

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                #temperature=self.temperature,
                max_completion_tokens=self.max_output_tokens,
            )

            result = response.choices[0].message.content.strip()
            
            if save_dir:
                save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)

            return result

        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

        except Exception as e:
            raise RuntimeError(f"Unexpected LLM error: {str(e)}") from e

    # ---------------------------------------------------------
    # JSON-enforced call
    # ---------------------------------------------------------
    def generate_json(self, messages: List[Dict[str, str]], response_format: Optional[Any] = None, save_dir: Optional[str] = None, prompt_name: str = "prompt") -> Dict[str, Any]:
        """
        Forces JSON output from the model and returns parsed dict.
        Raises error if invalid JSON.
        """

        try:
            if response_format:
                response = self.client.beta.chat.completions.parse(
                    model=self.model,
                    messages=messages,
                    #temperature=self.temperature,
                    max_completion_tokens=self.max_output_tokens,
                    response_format=response_format,
                )
                
                parsed_obj = response.choices[0].message.parsed
                result = parsed_obj.model_dump() if parsed_obj else json.loads(response.choices[0].message.content)
                
                if save_dir:
                    save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)
                
                return result
            else:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    #temperature=self.temperature,
                    max_completion_tokens=self.max_output_tokens,
                    response_format={"type": "json_object"},
                )

                raw_text = response.choices[0].message.content.strip()
                result = json.loads(raw_text)
                
                if save_dir:
                    save_llm_prompt(messages, save_dir, filename_prefix=prompt_name)
                    
                return result

        except json.JSONDecodeError as e:
            raise ValueError("Model returned invalid JSON.") from e

        except OpenAIError as e:
            raise RuntimeError(f"OpenAI API error: {str(e)}") from e

        except Exception as e:
            raise RuntimeError(f"Unexpected LLM error: {str(e)}") from e