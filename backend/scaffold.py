import os

structure = {
    "app/models": [
        "user.py", "workspace.py", "workspace_member.py", "invite.py", "client.py",
        "project.py", "project_member.py", "task.py", "time_entry.py", "tag.py",
        "webhook.py", "notification.py"
    ],
    "app/schemas": [
        "auth.py", "user.py", "workspace.py", "invite.py", "client.py", "project.py",
        "task.py", "time_entry.py", "approval.py", "report.py", "webhook.py", "notification.py"
    ],
    "app/routers": [
        "auth.py", "users.py", "workspaces.py", "invites.py", "clients.py", "projects.py",
        "tasks.py", "time_entries.py", "approvals.py", "reports.py", "webhooks.py", "notifications.py"
    ],
    "app/services": [
        "auth_service.py", "invite_service.py", "time_entry_service.py", "approval_service.py",
        "rate_service.py", "rounding_service.py", "report_service.py", "notification_service.py",
        "webhook_service.py"
    ],
    "app/utils": [
        "email.py", "pagination.py"
    ]
}

for folder, files in structure.items():
    os.makedirs(folder, exist_ok=True)
    
    # Ensure __init__.py exists
    init_path = os.path.join(folder, "__init__.py")
    if not os.path.exists(init_path):
        with open(init_path, "w") as f:
            f.write("")
            
    for file in files:
        file_path = os.path.join(folder, file)
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("# TODO: implement\n")
                
print("Scaffolding complete.")
