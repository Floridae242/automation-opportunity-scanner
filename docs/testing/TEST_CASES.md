# Core Test Cases

## Authorization
- Analyst in Org A cannot GET/PATCH/start analysis for Org B resource ID.
- Viewer cannot edit/review.
- Reviewer can review but cannot manage members.

## Scoring
- Risk=0 => risk_safety=100; Risk=100 => risk_safety=0.
- Each dimension boundary 0 and 100.
- Sample vector returns 74.5.
- Missing required dimension does not become 0.
- Same facts + same scoring version always return same result.

## ROI
- Zero/unknown implementation cost does not divide incorrectly.
- Missing loaded labor cost prevents monetary ROI.
- Exception fraction reduces saved hours.

## Process versioning
Reviewed version cannot be mutated in place; edit creates successor version.

## AI
Invalid step IDs, unknown taxonomy enum, invented numeric facts, and schema errors fail validation or are flagged before review.
