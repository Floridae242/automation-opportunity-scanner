# Database Schema

## Core tables
- organizations(id, name, settings_json, created_at)
- users(id, auth_subject, email, display_name, created_at)
- memberships(id, organization_id, user_id, role)
- projects(id, organization_id, name, department, status, created_by, timestamps)
- processes(id, organization_id, project_id, name, status, created_by, timestamps)
- process_versions(id, organization_id, process_id, version_no, review_status, source_summary, created_by, created_at)
- process_steps(id, organization_id, process_version_id, step_key, sequence_no, name, actor_id, system_id, manual_flag, duration_minutes, data_json)
- actors(id, organization_id, process_version_id, name, type)
- systems(id, organization_id, process_version_id, name, integration_status, integration_evidence_id)
- evidences(id, organization_id, process_version_id, source_type, source_ref, excerpt, reviewed, confidence)
- pain_points(id, organization_id, analysis_run_id, category, description, severity, confidence)
- analysis_runs(id, organization_id, process_version_id, status, model_id, prompt_version, schema_version, scoring_version, timestamps, error_code)
- opportunities(id, organization_id, analysis_run_id, title, scope_json, confidence, status)
- opportunity_scores(id, organization_id, opportunity_id, total_score, dimension_json, confidence_score, scoring_version, created_at)
- recommendations(id, organization_id, opportunity_id, patterns_json, rationale, prerequisites_json, risks_json, confidence)
- roi_scenarios(id, organization_id, opportunity_id, input_json, output_json, created_at)
- reports(id, organization_id, analysis_run_id, status, snapshot_json, storage_key)
- ai_runs(id, organization_id, analysis_run_id, task, provider, model, prompt_version, schema_version, latency_ms, usage_json, status)
- audit_logs(id, organization_id, actor_user_id, action, entity_type, entity_id, metadata_json, created_at)

## Index priorities
organization_id on all tenant data; process/project foreign keys; analysis_run status; opportunities score/reporting filters; created_at for history.
