"""Approved, read-only integration capability evidence (BR-009)."""

CATALOG = (
    {
        "key": "microsoft-365",
        "name": "Microsoft 365",
        "capabilities": ["read_mail_metadata", "read_files", "workflow_events"],
        "evidence": "Approved catalog entry; validate tenant licensing and permissions before use.",
    },
    {
        "key": "google-workspace",
        "name": "Google Workspace",
        "capabilities": ["read_mail_metadata", "read_files", "workflow_events"],
        "evidence": "Approved catalog entry; validate tenant licensing and permissions before use.",
    },
    {
        "key": "salesforce",
        "name": "Salesforce",
        "capabilities": ["read_records", "workflow_events"],
        "evidence": (
            "Approved catalog entry; validate object access and connected-app policy before use."
        ),
    },
)
