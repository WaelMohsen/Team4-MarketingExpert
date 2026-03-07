import json
import os
from datetime import datetime

try:
    from openai import OpenAI
except ImportError:
    raise ImportError(
        "The 'openai' package is not installed.\n"
        "Run:  pip install openai"
    )

class OpenAIClient:
    DEFAULT_MODEL    = "gpt-4.1-mini"
    DEFAULT_BASE_URL = "https://api.openai.com/v1"
    DEFAULT_PROMPT   = "/Users/marwa/Desktop/Marwa/NLP course/My project/prompt_engineering/prompt.txt"
    api_key="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"
    DEFAULT_INPUT="/Users/marwa/Desktop/Marwa/NLP course/My project/prompt_engineering/campaign_platforms_data.json"
    def __init__(
        self,
        api_key:     str        = api_key,
        model:       str        = DEFAULT_MODEL,
        base_url:    str        = DEFAULT_BASE_URL,
        prompt_path: str        = DEFAULT_PROMPT,
        input_path:  str        = DEFAULT_INPUT
       ):

       self.model        = model
       self._client      = OpenAI(api_key=api_key)
       self._prompt_path = prompt_path
       self._input_path = input_path


     

    def _creat_message(self) ->list:
        # 1️⃣ Load system prompt from text file
        with open(self._prompt_path, "r", encoding="utf-8") as f:
         system_prompt = f.read()

      # 2️⃣ Load JSON input file
        with open(self._input_path, "r", encoding="utf-8") as f:
         input_data = json.load(f)
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user",   "content": json.dumps(input_data)},
        ]

    def _call_api(self, messages: list) -> str:
        """Send messages to the model and return the raw response text."""
        response = self._client.chat.completions.create(
            model       = self.model,
            messages    = messages,
            temperature = 0.2,   # low = consistent, factual, strict schema adherence
        )
        return response.choices[0].message.content  


