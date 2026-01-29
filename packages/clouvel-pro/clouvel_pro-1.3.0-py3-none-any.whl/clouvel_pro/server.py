# -*- coding: utf-8 -*-
"""
Clouvel Pro MCP Server v1.2.0
Shovel 워크플로우 + 프리미엄 기능
"""

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.types import Tool, TextContent

from .license import activate_license, verify_license, get_license_age_days, PREMIUM_UNLOCK_DAYS
from .tools import (
    install_shovel,
    sync_commands,
    log_error,
    analyze_error,
    watch_logs,
    check_logs,
    add_prevention_rule,
    get_error_summary,
    # Team (Team/Enterprise only)
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

server = Server("clouvel-pro")


# ============================================================
# Tool Definitions
# ============================================================

TOOL_DEFINITIONS = [
    # === License ===
    Tool(
        name="activate_license",
        description="Clouvel Pro 라이선스 활성화.",
        inputSchema={
            "type": "object",
            "properties": {
                "license_key": {"type": "string", "description": "라이선스 키 (CLOUVEL-TIER-CODE)"}
            },
            "required": ["license_key"]
        }
    ),
    Tool(
        name="check_license",
        description="현재 라이선스 상태 확인.",
        inputSchema={"type": "object", "properties": {}}
    ),

    # === Shovel ===
    Tool(
        name="install_shovel",
        description="Pro: Shovel .claude/ 구조 자동 설치. 라이선스 필요.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "project_type": {"type": "string", "enum": ["web", "api", "desktop", "fullstack"]},
                "force": {"type": "boolean", "description": "기존 폴더 덮어쓰기"}
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="sync_commands",
        description="Pro: Shovel 커맨드 동기화.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "mode": {"type": "string", "enum": ["merge", "overwrite"]}
            },
            "required": ["path"]
        }
    ),

    # === Error Learning ===
    Tool(
        name="log_error",
        description="Pro: 에러 로깅 및 자동 분류.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "error_text": {"type": "string", "description": "에러 메시지"},
                "context": {"type": "string", "description": "에러 발생 상황"},
                "source": {"type": "string", "enum": ["terminal", "log", "browser", "manual"]}
            },
            "required": ["path", "error_text"]
        }
    ),
    Tool(
        name="analyze_error",
        description="Pro: 에러 상세 분석 및 히스토리.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "error_text": {"type": "string", "description": "분석할 에러"},
                "include_history": {"type": "boolean"}
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="watch_logs",
        description="Pro: 로그 파일 모니터링 설정.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "log_paths": {"type": "array", "items": {"type": "string"}},
                "patterns": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="check_logs",
        description="Pro: 로그 파일 스캔.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"}
            },
            "required": ["path"]
        }
    ),
    Tool(
        name="add_prevention_rule",
        description="Pro: 에러 방지 규칙 추가.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "error_type": {"type": "string"},
                "rule": {"type": "string"},
                "scope": {"type": "string", "enum": ["project", "file", "function"]}
            },
            "required": ["path", "error_type", "rule"]
        }
    ),
    Tool(
        name="get_error_summary",
        description="Pro: 에러 요약 리포트.",
        inputSchema={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "프로젝트 루트 경로"},
                "days": {"type": "integer"}
            },
            "required": ["path"]
        }
    ),

    # === Team (Team/Enterprise only) ===
    Tool(
        name="team_invite",
        description="Team: 팀원 초대. Team/Enterprise 라이선스 필요.",
        inputSchema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "초대할 이메일"},
                "role": {"type": "string", "enum": ["admin", "member"], "description": "역할"}
            },
            "required": ["email"]
        }
    ),
    Tool(
        name="team_members",
        description="Team: 팀원 목록 조회.",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="team_remove",
        description="Team: 팀원 제거.",
        inputSchema={
            "type": "object",
            "properties": {
                "email": {"type": "string", "description": "제거할 이메일"}
            },
            "required": ["email"]
        }
    ),
    Tool(
        name="team_settings",
        description="Team: C-Level 역할 설정 조회.",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="team_toggle_role",
        description="Team: C-Level 역할 활성화/비활성화.",
        inputSchema={
            "type": "object",
            "properties": {
                "cto": {"type": "boolean", "description": "CTO 모드"},
                "cdo": {"type": "boolean", "description": "CDO 모드"},
                "cpo": {"type": "boolean", "description": "CPO 모드"},
                "cfo": {"type": "boolean", "description": "CFO 모드"},
                "cmo": {"type": "boolean", "description": "CMO 모드"}
            }
        }
    ),
    Tool(
        name="sync_team_errors",
        description="Team: 로컬 에러 패턴을 팀에 동기화.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "프로젝트 경로"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="get_team_rules",
        description="Team: 팀 NEVER/ALWAYS 규칙 조회.",
        inputSchema={"type": "object", "properties": {}}
    ),
    Tool(
        name="apply_team_rules",
        description="Team: 팀 규칙을 로컬 CLAUDE.md에 적용.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "프로젝트 경로"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="sync_project_context",
        description="Team: 프로젝트 컨텍스트를 팀에 동기화.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_path": {"type": "string", "description": "프로젝트 경로"},
                "project_id": {"type": "string", "description": "프로젝트 ID (선택)"}
            },
            "required": ["project_path"]
        }
    ),
    Tool(
        name="get_project_context",
        description="Team: 팀 프로젝트 컨텍스트 조회.",
        inputSchema={
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "프로젝트 ID"}
            },
            "required": ["project_id"]
        }
    ),
]


@server.list_tools()
async def list_tools() -> list[Tool]:
    return TOOL_DEFINITIONS


# ============================================================
# Tool Handlers
# ============================================================

TOOL_HANDLERS = {
    # License
    "activate_license": lambda args: activate_license(args.get("license_key", "")),
    "check_license": lambda args: _check_license(),

    # Shovel
    "install_shovel": lambda args: install_shovel(
        args.get("path", ""),
        args.get("project_type", "web"),
        args.get("force", False)
    ),
    "sync_commands": lambda args: sync_commands(
        args.get("path", ""),
        args.get("mode", "merge")
    ),

    # Error Learning
    "log_error": lambda args: log_error(
        args.get("path", ""),
        args.get("error_text", ""),
        args.get("context", ""),
        args.get("source", "terminal")
    ),
    "analyze_error": lambda args: analyze_error(
        args.get("path", ""),
        args.get("error_text", ""),
        args.get("include_history", True)
    ),
    "watch_logs": lambda args: watch_logs(
        args.get("path", ""),
        args.get("log_paths"),
        args.get("patterns")
    ),
    "check_logs": lambda args: check_logs(args.get("path", "")),
    "add_prevention_rule": lambda args: add_prevention_rule(
        args.get("path", ""),
        args.get("error_type", ""),
        args.get("rule", ""),
        args.get("scope", "project")
    ),
    "get_error_summary": lambda args: get_error_summary(
        args.get("path", ""),
        args.get("days", 30)
    ),

    # Team (Team/Enterprise only)
    "team_invite": lambda args: team_invite(
        args.get("email", ""),
        args.get("role", "member")
    ),
    "team_members": lambda args: team_members(),
    "team_remove": lambda args: team_remove(args.get("email", "")),
    "team_settings": lambda args: team_settings(),
    "team_toggle_role": lambda args: team_toggle_role(
        args.get("cto"),
        args.get("cdo"),
        args.get("cpo"),
        args.get("cfo"),
        args.get("cmo")
    ),
    "sync_team_errors": lambda args: sync_team_errors(args.get("project_path", "")),
    "get_team_rules": lambda args: get_team_rules(),
    "apply_team_rules": lambda args: apply_team_rules(args.get("project_path", "")),
    "sync_project_context": lambda args: sync_project_context(
        args.get("project_path", ""),
        args.get("project_id")
    ),
    "get_project_context": lambda args: get_project_context(args.get("project_id", "")),
}


async def _check_license() -> list[TextContent]:
    """라이선스 상태 확인"""
    result = verify_license()

    if result["valid"]:
        tier = result["tier_info"]
        age_days = get_license_age_days()
        remaining = PREMIUM_UNLOCK_DAYS - age_days
        premium_unlocked = remaining <= 0

        # Team/Enterprise tier check
        tier_name = tier.get("name", "").lower()
        is_team_tier = "team" in tier_name or "enterprise" in tier_name

        team_features = ""
        if is_team_tier:
            team_features = """

## Team 전용 기능
- `team_invite` - 팀원 초대
- `team_members` - 팀원 목록
- `team_remove` - 팀원 제거
- `team_settings` - C-Level 설정 조회
- `team_toggle_role` - CTO/CDO/CPO/CFO/CMO 모드 토글
- `sync_team_errors` - 에러 패턴 팀 동기화
- `get_team_rules` - 팀 NEVER/ALWAYS 규칙
- `apply_team_rules` - 팀 규칙 로컬 적용
- `sync_project_context` - 프로젝트 컨텍스트 동기화
- `get_project_context` - 프로젝트 컨텍스트 조회"""

        if premium_unlocked:
            lock_status = "🔓 **프리미엄 잠금 해제됨**"
            available_features = f"""
## 사용 가능한 기능 (전체)
- `install_shovel` - Shovel 설치
- `sync_commands` - 커맨드 동기화
- `log_error` - 에러 기록
- `analyze_error` - 에러 분석
- `watch_logs` - 로그 감시
- `check_logs` - 로그 체크
- `add_prevention_rule` - 방지 규칙
- `get_error_summary` - 에러 요약{team_features}"""
        else:
            lock_status = f"⏳ **프리미엄 잠금 중** ({remaining}일 남음)"
            available_features = f"""
## 지금 사용 가능한 기능
- `watch_logs` - 로그 감시 설정
- `check_logs` - 로그 체크{team_features}

## {remaining}일 후 사용 가능 (프리미엄)
- `install_shovel` - Shovel 설치
- `sync_commands` - 커맨드 동기화
- `log_error` - 에러 기록
- `analyze_error` - 에러 분석
- `add_prevention_rule` - 방지 규칙
- `get_error_summary` - 에러 요약"""

        return [TextContent(type="text", text=f"""
# ✅ 라이선스 활성화됨

- **티어**: {tier['name']}
- **인원**: {tier['seats'] if tier['seats'] > 0 else '무제한'}명
- **활성화 경과**: {age_days}일
- {lock_status}
{available_features}
""")]

    return [TextContent(type="text", text=f"""
# ❌ 라이선스 없음

{result['message']}

## 구매
https://clouvel.lemonsqueezy.com
""")]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[TextContent]:
    handler = TOOL_HANDLERS.get(name)
    if handler:
        return await handler(arguments)

    return [TextContent(type="text", text=f"Unknown tool: {name}")]


# ============================================================
# Server Entry Points
# ============================================================

async def run_server():
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


def main():
    import asyncio
    asyncio.run(run_server())


if __name__ == "__main__":
    main()
