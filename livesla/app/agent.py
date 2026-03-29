"""
LiveSLA — Contract Parser Agent
=================================

Uses a local LLM (OpenAI-compatible API on localhost:11434/v1) to extract
structured SLA terms from raw legal / contract text.

Architecture
------------
    Raw legal text  ──▶  Prompt template  ──▶  Local LLM  ──▶  JSON  ──▶  Pydantic validation
                                                                              │
                                                                    list[SLATermExtracted]

The agent is intentionally stateless — it receives text, returns validated
Pydantic objects.  Persistence is the caller's responsibility.

Usage::

    agent = ContractParserAgent()
    terms = await agent.extract(legal_text)

Configuration
-------------
Override the endpoint via environment variables:

    LLM_BASE_URL   (default: http://localhost:11434/v1)
    LLM_MODEL      (default: qwen3)
    LLM_API_KEY    (default: not-needed — local model)
"""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

from openai import AsyncOpenAI, OpenAIError
from pydantic import ValidationError

from app.schemas import SLATermExtracted

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
LLM_BASE_URL: str = os.getenv("LLM_BASE_URL", "http://localhost:11434/v1")
LLM_MODEL: str = os.getenv("LLM_MODEL", "llama3.2")
LLM_API_KEY: str = os.getenv("LLM_API_KEY", "not-needed")
LLM_TEMPERATURE: float = float(os.getenv("LLM_TEMPERATURE", "0.1"))
LLM_MAX_TOKENS: int = int(os.getenv("LLM_MAX_TOKENS", "4096"))

# ---------------------------------------------------------------------------
# System prompt — instructs the LLM to behave as a legal data extractor.
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """\
You are a legal data extraction specialist.  Your task is to read enterprise
contract text and extract every Service Level Agreement (SLA) obligation into
a structured JSON array.

For EACH SLA obligation found, return an object with exactly these keys:

  • metric_name        — A short, machine-readable identifier for the metric
                         (e.g. "uptime", "response_time_ms", "error_rate",
                         "resolution_time_hours").  Use snake_case, lowercase.
  • target_value       — The numeric threshold stated in the contract.
                         For percentages like "99.9%" use the number 99.9.
                         For durations like "4 hours" use 4.0.
  • penalty_percentage — The financial penalty expressed as a percentage of
                         the contract value.  If the contract says "5% credit"
                         or "5% of monthly fees", return 5.0.
  • description        — A one-sentence plain-English summary of the clause.

Rules:
  1. Return ONLY a JSON array — no markdown, no commentary, no code fences.
  2. If the text contains zero SLA obligations, return an empty array: []
  3. Be precise with numbers — do not round or infer values not stated.
  4. Each distinct metric is a separate object, even if from the same clause.

/no_think
"""

USER_PROMPT_TEMPLATE: str = """\
Extract all SLA terms from the following contract text:

---
{legal_text}
---

Respond with a JSON array only.
"""


class ContractParserAgent:
    """Stateless agent that extracts SLA terms from legal text via a local LLM.

    Parameters
    ----------
    base_url : str, optional
        OpenAI-compatible API base URL.
    model : str, optional
        Model identifier to use for chat completions.
    api_key : str, optional
        API key (most local servers accept any non-empty string).
    """

    def __init__(
        self,
        base_url: str = LLM_BASE_URL,
        model: str = LLM_MODEL,
        api_key: str = LLM_API_KEY,
    ) -> None:
        self._client = AsyncOpenAI(base_url=base_url, api_key=api_key)
        self._model = model

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    async def extract(self, legal_text: str) -> list[SLATermExtracted]:
        """Parse *legal_text* and return validated SLA term objects.

        Parameters
        ----------
        legal_text : str
            Raw contract / legal clause text (e.g. from a PDF parser).

        Returns
        -------
        list[SLATermExtracted]
            Zero or more validated SLA terms.

        Raises
        ------
        ExtractionError
            If the LLM call fails or the response cannot be parsed.
        """
        raw_json = await self._call_llm(legal_text)
        return self._parse_response(raw_json)

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    async def _call_llm(self, legal_text: str) -> str:
        """Send the extraction prompt to the LLM and return the raw reply."""
        user_message = USER_PROMPT_TEMPLATE.format(legal_text=legal_text)

        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
                temperature=LLM_TEMPERATURE,
                max_tokens=LLM_MAX_TOKENS,
            )
        except OpenAIError as exc:
            raise ExtractionError(f"LLM API call failed: {exc}") from exc

        message = response.choices[0].message
        content = message.content

        # Some reasoning models (Qwen3.x) put output in a `reasoning` field
        # when the token budget is exhausted before generating `content`.
        if not content:
            reasoning = getattr(message, "reasoning", None)
            if reasoning:
                # Try to extract a JSON array from the reasoning text
                match = re.search(r"\[.*\]", reasoning, re.DOTALL)
                if match:
                    content = match.group(0)
                    logger.info("Extracted JSON from model reasoning field.")

        if not content:
            raise ExtractionError(
                "LLM returned an empty response. "
                "Try increasing LLM_MAX_TOKENS or using a non-reasoning model."
            )

        logger.debug("Raw LLM response:\n%s", content)
        return content

    @staticmethod
    def _parse_response(raw: str) -> list[SLATermExtracted]:
        """Validate the LLM's raw text into a list of Pydantic objects.

        Handles common LLM quirks:
          - Markdown code fences around JSON
          - Leading/trailing whitespace
          - Trailing commas (best-effort)
        """
        # Strip markdown code fences if present
        cleaned = raw.strip()
        cleaned = re.sub(r"^```(?:json)?\s*", "", cleaned)
        cleaned = re.sub(r"\s*```$", "", cleaned)
        cleaned = cleaned.strip()

        # Strip <think>...</think> blocks (some models emit chain-of-thought)
        cleaned = re.sub(r"<think>.*?</think>", "", cleaned, flags=re.DOTALL).strip()

        try:
            data: Any = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ExtractionError(
                f"LLM response is not valid JSON:\n{raw[:500]}"
            ) from exc

        if not isinstance(data, list):
            raise ExtractionError(
                f"Expected a JSON array, got {type(data).__name__}."
            )

        terms: list[SLATermExtracted] = []
        for idx, item in enumerate(data):
            try:
                terms.append(SLATermExtracted.model_validate(item))
            except ValidationError as exc:
                logger.warning("Skipping invalid SLA term at index %d: %s", idx, exc)

        return terms


class ExtractionError(Exception):
    """Raised when the LLM call or response parsing fails."""
