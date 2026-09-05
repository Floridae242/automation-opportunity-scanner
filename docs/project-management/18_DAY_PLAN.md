# 18-Day Plan — ทีม 4 คน

## Role split (rotate/review each other)
A: Product/UX + frontend lead  
B: Backend/domain + DB lead  
C: AI/evaluation lead  
D: QA/DevOps + full-stack integration lead

## Days 1–3 Foundation
D1 product freeze, user flow, demo process; D2 architecture/schema/repo; D3 auth/tenant + design shell + CI.

## Days 4–6 Intake
Project/process CRUD, guided intake, DB migrations, demo seeds, happy-path E2E skeleton.

## Days 7–9 AI extraction + review
Structured schema, fake provider, real provider adapter, extraction review, process map. **Go/no-go D9:** if AI unreliable, freeze schema and use stronger guided intake + AI assist rather than chasing prompts.

## Days 10–12 Opportunity engine
Pain points, taxonomy rules, deterministic scoring, confidence, Impact-vs-Effort.

## Days 13–14 Recommendations/report
Recommendation rationale/prerequisites, ROI scenarios, executive report, portfolio view.

## Day 15 Evaluation
Golden/adversarial eval; fix highest-impact failures; lock prompt v1.

## Day 16 Hardening
Authorization suite, E2E, error paths, performance basics, visual consistency.

## Day 17 Deployment/demo freeze
Production-like staging, backup demo dataset, record fallback demo video/screenshots if permitted, no major features.

## Day 18 Demo
Rehearse 5–10 minute story; only critical bug fixes.

## Scope cut order if behind
Cut document upload -> advanced report export -> configurable weights -> version comparison. Never cut tenant authorization, human review, deterministic score, evidence, or basic tests.
