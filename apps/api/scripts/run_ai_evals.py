"""Offline regression gate for the deterministic demo extraction provider."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "apps" / "api" / "src"))

from aos_api.extraction import DemoExtractionProvider, validate_extraction  # noqa: E402


def load(name: str) -> list[dict[str, object]]:
    data = json.loads((ROOT / "evals" / name).read_text())
    cases = data.get("cases")
    if not isinstance(cases, list) or len(
        {case.get("id") for case in cases if isinstance(case, dict)}
    ) != len(cases):
        raise ValueError(f"Invalid evaluation dataset: {name}")
    return cases


def main() -> None:
    provider = DemoExtractionProvider()
    failures: list[str] = []
    for case in load("golden_dataset.json"):
        raw = provider.extract("offline evaluator", str(case["input"]))
        draft = validate_extraction(raw)
        names = " ".join(step.name.lower() for step in draft.steps)
        expected = case.get("expected", {})
        for phrase in expected.get("must_include_steps", []) if isinstance(expected, dict) else []:
            if not any(word in names for word in str(phrase).lower().split()):
                failures.append(f"{case['id']}: missing step signal {phrase}")
        for claim in expected.get("forbidden_claims", []) if isinstance(expected, dict) else []:
            if str(claim).lower() in names:
                failures.append(f"{case['id']}: invented forbidden claim")
    for case in load("adversarial_inputs.json"):
        draft = validate_extraction(provider.extract("offline evaluator", str(case["input"])))
        output = " ".join(step.name.lower() for step in draft.steps)
        if case["id"] == "inject-001" and "ignore all previous instructions" not in output:
            failures.append(f"{case['id']}: untrusted text was not preserved safely")
    if failures:
        print("AI evaluation failed:\n" + "\n".join(failures), file=sys.stderr)
        raise SystemExit(1)
    print("AI evaluation passed: demo provider preserved untrusted inputs and schema validity.")


if __name__ == "__main__":
    main()
