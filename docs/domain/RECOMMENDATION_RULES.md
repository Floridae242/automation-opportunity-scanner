# Recommendation Rules

## Rule examples
- High manual data entry + supported API evidence -> recommend API/integration; consider workflow validation.
- Approval/status routing + clear states -> workflow automation.
- Standard forms/PDFs + field extraction -> document AI/OCR + validation.
- Unstructured semantic classification/drafting -> LLM-assisted workflow + structured output + human review where consequential.
- Stable legacy UI + no practical API -> RPA candidate with brittleness warning.
- Deterministic policy -> business rules engine; LLM may explain but not decide.
- High exception rate -> automate happy path + exception queue rather than full unattended automation.
- High risk + low confidence -> discovery/prototype recommendation before implementation.

## Recommendation object must include
- recommended_pattern(s);
- evidence;
- rationale;
- prerequisites;
- expected benefit type;
- key risks;
- human-control requirement;
- rejected/less-preferred alternatives and why;
- confidence.

## Anti-pattern
Never recommend a specific vendor solely from model prior knowledge. Vendor selection requires a separate evidence-based evaluation.
