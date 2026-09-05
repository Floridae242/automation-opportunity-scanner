# API Error and Authorization Standard

## Error envelope
```json
{
  "error": {
    "code": "ANALYSIS_SCHEMA_INVALID",
    "message": "The analysis could not be validated.",
    "request_id": "...",
    "details": {}
  }
}
```

## Rules
- Client messages are safe and actionable; internal stack/provider detail stays in logs.
- 401 = unauthenticated; 403/404 behavior should avoid resource-existence leakage according to policy.
- 409 for version/state conflicts.
- 422 for valid JSON that violates input/domain validation.
- 429 for rate/quota limit.
- 503 for temporarily unavailable dependencies when retry may help.

## Roles v1
Owner/Admin: manage org/project membership/settings. Analyst: create/edit/analyze. Reviewer: review/approve process facts. Viewer: read published results. Server endpoints enforce role/action, not UI alone.
