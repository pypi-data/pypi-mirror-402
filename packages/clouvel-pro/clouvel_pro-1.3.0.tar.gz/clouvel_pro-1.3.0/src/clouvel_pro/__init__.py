# -*- coding: utf-8 -*-
"""
Clouvel Pro - Shovel 워크플로우 + 프리미엄 기능

Pro 기능:
- Shovel 자동 설치 (.claude/ 구조)
- Error Learning (에러 패턴 학습)
- 라이선스 관리
"""

__version__ = "1.2.0"

from .license import verify_license, activate_license
from .tools import install_shovel, sync_commands
from .tools import (
    log_error,
    analyze_error,
    watch_logs,
    check_logs,
    add_prevention_rule,
    get_error_summary,
)

__all__ = [
    # License
    "verify_license",
    "activate_license",
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
]
