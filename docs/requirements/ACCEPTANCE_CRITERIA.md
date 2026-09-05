# Acceptance Criteria — Critical Flows

## Create and analyze process
Given an authenticated organization member, when they create a process, enter a workflow description, and start analysis, then:
- a queued/running analysis state is visible;
- the AI result is schema validated;
- invalid results fail safely with a retry option;
- a draft process version is created with provenance;
- the user can edit and confirm it.

## Final scoring
Given a reviewed process version, when opportunities are generated, then each opportunity displays:
- score 0–100;
- score version;
- dimension contributions;
- assessment confidence;
- evidence references;
- impact and effort values;
- recommended technology and prerequisites.

## Missing data
Given missing duration or frequency, the system must not invent it. ROI is unavailable or scenario-based and the UI identifies the missing fields.

## Authorization
A user from organization A requesting a known resource ID owned by organization B receives a non-disclosing denial and no protected record data.
