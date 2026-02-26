from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict

from langchain_groq import ChatGroq
from openai import OpenAI


def _load_prompt_template(prompt_path: Path | None = None) -> str:
    if prompt_path is None:
        prompt_path = Path("Prompt 1.txt")
    with prompt_path.open("r", encoding="utf-8") as f:
        return f.read()


def _fill_placeholders(template: str, payload: Dict[str, Any]) -> str:
    return (
        template.replace("{{CAMPAIGN_TARGET}}", json.dumps(payload["campaign_target"]))
        .replace("{{BUSINESS_DOMAIN}}", json.dumps(payload["business_domain"]))
        .replace("{{CAMPAIGN_PLATFORMS_DATA}}", json.dumps(payload["campaign_platforms_data"]))
    )


def call_groq_with_payload(
    payload: Dict[str, Any],
    model: str | None = None,
    prompt_path: Path | None = None,
) -> str:
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY environment variable is not set.")

    if model is None:
        model = "llama-3.3-70b-versatile"

    template = _load_prompt_template(prompt_path)
    prompt_text = _fill_placeholders(template, payload)

    llm = ChatGroq(api_key=api_key, model=model, temperature=0)

    response = llm.invoke(prompt_text)
    content = getattr(response, "content", None)

    if isinstance(content, str):
        return content
    try:
        # Handle list-of-chunks style content
        return "".join(getattr(part, "text", "") for part in content)  # type: ignore[arg-type]
    except Exception:
        return str(content)


def call_openai_with_payload(
    payload: Dict[str, Any],
    model: str | None = None,
    prompt_path: Path | None = None,
) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY environment variable is not set.")

    if model is None:
        model = "gpt-4.1-mini"

    template = _load_prompt_template(prompt_path)
    prompt_text = _fill_placeholders(template, payload)

    client = OpenAI(api_key=api_key)

    response = client.responses.create(
        model=model,
        input=prompt_text,
    )

    raw_output = response.output[0].content[0].text
    if hasattr(raw_output, "value"):
        return raw_output.value  # type: ignore[no-any-return]
    return str(raw_output)
