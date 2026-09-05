# Automation Taxonomy and Selection Guide

## API / System Integration
Use when systems expose stable supported interfaces and data must move reliably. Prefer for durable system-to-system automation. Avoid claiming availability without evidence.

## Workflow Automation
Use for routing, approvals, state transitions, task assignment, SLA timers, notifications, and human-in-the-loop processes.

## Business Rules
Use when decisions are deterministic, explainable, stable, and based on explicit conditions. Prefer rules over an LLM for exact policy logic.

## Document AI / OCR
Use when documents contain semi/unstructured fields that must be classified or extracted. Pair with validation and human review for sensitive/high-impact fields.

## RPA / UI Automation
Use when a necessary system lacks practical integration and UI steps are stable enough. Flag brittleness, credential handling, screen changes, and exception monitoring.

## LLM / Generative AI Assistance
Use for semantic classification, summarization, extraction from varied text, drafting, or assisting judgment. Do not use as the sole source of deterministic calculations or policy enforcement.

## Traditional ML
Use when a repeatable prediction/classification problem has sufficient representative historical labeled data and measurable evaluation criteria.

## Data / ETL Automation
Use for scheduled/event-driven extraction, transformation, reconciliation, and reporting pipelines where data contracts are known.

## Notification / Event Automation
Use for reminders, alerts, status transitions, and event-triggered follow-up.

## Human-in-the-loop
Not a separate technology; a control pattern. Use when exceptions, uncertainty, risk, approval, accountability, or regulation requires human judgment.

## Selection preference
Stable API/integration > workflow/rules > document AI/AI where semantic work exists > RPA when integration is impractical. Combine patterns when appropriate.
