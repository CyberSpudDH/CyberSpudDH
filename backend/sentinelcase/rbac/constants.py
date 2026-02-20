PERMISSIONS = [
    "signals.read", "signals.triage", "signals.dismiss",
    "cases.read", "cases.create", "cases.update", "cases.close",
    "sources.manage", "users.manage", "roles.manage", "audit.read",
]

DEFAULT_ROLES = {
    "Admin": PERMISSIONS,
    "Analyst": [
        "signals.read", "signals.triage", "signals.dismiss",
        "cases.read", "cases.create", "cases.update", "cases.close",
    ],
    "ReadOnly": ["signals.read", "cases.read"],
}
