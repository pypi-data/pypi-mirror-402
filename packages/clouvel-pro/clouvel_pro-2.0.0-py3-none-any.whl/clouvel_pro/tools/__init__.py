# -*- coding: utf-8 -*-
"""Clouvel Pro Tools"""

from .shovel import install_shovel, sync_commands
from .errors import (
    log_error,
    analyze_error,
    watch_logs,
    check_logs,
    add_prevention_rule,
    get_error_summary,
    ERROR_PATTERNS,
)
from .team import (
    team_invite,
    team_members,
    team_remove,
    team_settings,
    team_toggle_role,
    sync_team_errors,
    get_team_rules,
    apply_team_rules,
    sync_project_context,
    get_project_context,
)
from .context import recover_context
from .hooks import setup_auto_recovery, check_auto_recovery_status

__all__ = [
    # Shovel
    "install_shovel",
    "sync_commands",
    # Error Learning
    "log_error",
    "analyze_error",
    "watch_logs",
    "check_logs",
    "add_prevention_rule",
    "get_error_summary",
    "ERROR_PATTERNS",
    # Team (Team/Enterprise only)
    "team_invite",
    "team_members",
    "team_remove",
    "team_settings",
    "team_toggle_role",
    "sync_team_errors",
    "get_team_rules",
    "apply_team_rules",
    "sync_project_context",
    "get_project_context",
    # Context Recovery
    "recover_context",
    # Auto Recovery Hooks
    "setup_auto_recovery",
    "check_auto_recovery_status",
]
