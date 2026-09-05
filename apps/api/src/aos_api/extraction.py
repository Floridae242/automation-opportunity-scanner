"""M3 process extraction: provider adapters, schema/semantic validation (FR-005..007)."""

import json
import re
from pathlib import Path
from typing import Protocol

from jsonschema import Draft202012Validator
from pydantic import BaseModel, ConfigDict, Field, ValidationError

PROMPT_VERSION = "aos-process-extract v1.0.0"
SCHEMA_VERSION = "process.schema.json@aos-v1"
ROOT = Path(__file__).resolve().parents[4]


class StepDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    step_key: str = Field(pattern=r"^S[0-9]+$")
    name: str = Field(min_length=1, max_length=300)
    actor: str | None = None
    system: str | None = None
    manual: bool | None = None
    duration_minutes: float | None = Field(default=None, ge=0)
    evidence_refs: list[str] = Field(default_factory=list)


class ProcessDraft(BaseModel):
    model_config = ConfigDict(extra="forbid")
    name: str = Field(min_length=1, max_length=200)
    trigger: str | None = None
    outcome: str | None = None
    steps: list[StepDraft] = Field(min_length=1)
    open_questions: list[str] = Field(default_factory=list)


class ExtractionError(Exception):
    def __init__(self, code: str) -> None:
        self.code = code
        super().__init__(code)


def load_prompt() -> str:
    path = ROOT / "prompts" / "process_extraction.md"
    try:
        return path.read_text()
    except OSError:
        raise ExtractionError("AI_UNAVAILABLE") from None


class ExtractionProvider(Protocol):
    name: str
    model_id: str

    def extract(self, prompt: str, source: str) -> dict[str, object]: ...


_SENTENCE = re.compile(r"[^.!?\n][^.!?\n]*(?:[.!?]|$)")


class DemoExtractionProvider:
    """Offline deterministic parser for local development; never in production.

    Treats each intake sentence as one candidate step and marks everything it
    cannot verify as unknown — it never invents actors, systems, or durations.
    """

    name = "demo"
    model_id = "aos-demo-extract-v1"

    def extract(self, prompt: str, source: str) -> dict[str, object]:
        sentences = [m.group(0).strip() for m in _SENTENCE.finditer(source) if m.group(0).strip()]
        if not sentences:
            raise ExtractionError("AI_SCHEMA_INVALID")
        steps = [
            {
                "step_key": f"S{index}",
                "name": text[:300],
                "actor": None,
                "system": None,
                "manual": None,
                "duration_minutes": None,
                "evidence_refs": ["intake"],
            }
            for index, text in enumerate(sentences, start=1)
        ]
        return {
            "name": sentences[0][:200],
            "trigger": None,
            "outcome": None,
            "steps": steps,
            "open_questions": [
                "Who performs each step, in which systems, and how long does each take?"
            ],
        }


class OpenAICompatibleProvider:
    """Adapter for an OpenAI-compatible chat-completions endpoint with JSON mode."""

    name = "openai_compatible"

    def __init__(
        self, base_url: str, api_key: str, model_id: str, timeout_seconds: float = 30
    ) -> None:
        self.model_id = model_id
        self._base_url = base_url.rstrip("/")
        self._api_key = api_key
        self._timeout = timeout_seconds

    def extract(self, prompt: str, source: str) -> dict[str, object]:
        import httpx

        schema = json.loads((ROOT / "schemas" / "process.schema.json").read_text())
        body = {
            "model": self.model_id,
            "response_format": {"type": "json_object"},
            "messages": [
                {"role": "system", "content": prompt},
                {
                    "role": "user",
                    "content": json.dumps(
                        {"untrusted_business_data": source, "output_schema": schema},
                        ensure_ascii=False,
                    ),
                },
            ],
        }
        last_error = "AI_UNAVAILABLE"
        for _attempt in range(3):
            try:
                response = httpx.post(
                    f"{self._base_url}/chat/completions",
                    headers={"authorization": f"Bearer {self._api_key}"},
                    json=body,
                    timeout=self._timeout,
                )
                if response.status_code >= 500:
                    last_error = "AI_UNAVAILABLE"
                    continue
                if response.status_code == 429:
                    last_error = "AI_RATE_LIMITED"
                    continue
                response.raise_for_status()
                content = response.json()["choices"][0]["message"]["content"]
                parsed = json.loads(content)
                if not isinstance(parsed, dict):
                    raise ExtractionError("AI_SCHEMA_INVALID")
                return parsed
            except (httpx.HTTPError, KeyError, json.JSONDecodeError, TypeError):
                last_error = "AI_SCHEMA_INVALID"
                continue
        raise ExtractionError(last_error)


_process_schema = json.loads((ROOT / "schemas" / "process.schema.json").read_text())
_step_schema = json.loads((ROOT / "schemas" / "process_step.schema.json").read_text())
_process_schema["properties"]["steps"]["items"] = _step_schema  # resolve local $ref without network
_VALIDATOR = Draft202012Validator(_process_schema)
_ALLOWED_EVIDENCE = re.compile(r"^(intake|metrics:[a-z_]+)$")


def validate_extraction(raw: dict[str, object]) -> ProcessDraft:
    """Layers 2-4 per STRUCTURED_OUTPUTS_AND_VALIDATION.md."""
    if not _VALIDATOR.is_valid(raw):
        raise ExtractionError("AI_SCHEMA_INVALID")
    try:
        draft = ProcessDraft.model_validate(raw)
    except ValidationError:
        raise ExtractionError("AI_SCHEMA_INVALID") from None
    if len({step.step_key for step in draft.steps}) != len(draft.steps):
        raise ExtractionError("AI_SCHEMA_INVALID")
    for step in draft.steps:
        for reference in step.evidence_refs:
            if not _ALLOWED_EVIDENCE.fullmatch(reference):
                raise ExtractionError("AI_SEMANTIC_INVALID")
    return draft


def build_provider(
    settings_provider: str, base_url: str | None, api_key: str | None, model: str | None
) -> ExtractionProvider:
    if settings_provider == "openai_compatible":
        if not (base_url and api_key and model):
            raise ExtractionError("AI_UNAVAILABLE")
        return OpenAICompatibleProvider(base_url, api_key, model)
    return DemoExtractionProvider()
