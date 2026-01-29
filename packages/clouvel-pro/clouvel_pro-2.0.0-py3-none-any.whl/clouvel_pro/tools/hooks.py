# -*- coding: utf-8 -*-
"""Context Recovery Hooks: PreCompact, SessionStart

자동 컨텍스트 복구를 위한 Claude Code Hook 스크립트 설치
"""

import os
from pathlib import Path
from datetime import datetime
from mcp.types import TextContent

from ..license import require_license

# Hook 스크립트 내용 (임베디드)
SAVE_STATE_SCRIPT = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""PreCompact Hook: 컨텍스트 압축 전 상태 저장"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# Windows UTF-8 설정
if sys.platform == "win32":
    sys.stdin.reconfigure(encoding='utf-8')

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        sys.exit(1)

    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    project_path = Path(project_dir)

    # 상태 수집
    state = {
        "timestamp": datetime.now().isoformat(),
        "trigger": input_data.get("trigger", "unknown"),
        "session_id": input_data.get("session_id", "")
    }

    # current.md 읽기
    current_md = project_path / ".claude" / "status" / "current.md"
    if current_md.exists():
        try:
            state["current_md"] = current_md.read_text(encoding="utf-8")[:3000]
        except:
            pass

    # 활성 PLAN 찾기
    plans_dir = project_path / ".claude" / "plans"
    if plans_dir.exists():
        for f in plans_dir.glob("PLAN-*.md"):
            try:
                content = f.read_text(encoding="utf-8")
                if "LOCKED" in content or "IN_PROGRESS" in content or "진행 중" in content:
                    state["active_plan"] = f.name
                    state["plan_content"] = content[:2000]
                    break
            except:
                continue

    # CLAUDE.md 핵심 규칙
    claude_md = project_path / "CLAUDE.md"
    if claude_md.exists():
        try:
            content = claude_md.read_text(encoding="utf-8")
            # NEVER/ALWAYS 추출
            import re
            rules = []
            for match in re.findall(r"NEVER[:\\s]+([^\\n]+)", content, re.IGNORECASE)[:5]:
                rules.append(f"NEVER: {match.strip()}")
            for match in re.findall(r"ALWAYS[:\\s]+([^\\n]+)", content, re.IGNORECASE)[:5]:
                rules.append(f"ALWAYS: {match.strip()}")
            if rules:
                state["rules"] = rules
        except:
            pass

    # Git 브랜치
    git_head = project_path / ".git" / "HEAD"
    if git_head.exists():
        try:
            head_content = git_head.read_text(encoding="utf-8").strip()
            if head_content.startswith("ref: refs/heads/"):
                state["git_branch"] = head_content.replace("ref: refs/heads/", "")
        except:
            pass

    # 저장
    state_dir = project_path / ".claude" / "status"
    state_dir.mkdir(parents=True, exist_ok=True)
    state_file = state_dir / "session-state.json"

    try:
        state_file.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    except:
        pass

    sys.exit(0)

if __name__ == "__main__":
    main()
'''

RECOVER_CONTEXT_SCRIPT = '''#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SessionStart Hook: 컨텍스트 압축 후 자동 복구"""

import json
import sys
import os
from pathlib import Path

# Windows UTF-8 stdout 설정
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')
    sys.stdin.reconfigure(encoding='utf-8')

def main():
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # 입력 없으면 빈 컨텍스트
        output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
        print(json.dumps(output))
        sys.exit(0)

    source = input_data.get("source", "startup")
    project_dir = os.environ.get("CLAUDE_PROJECT_DIR", ".")
    project_path = Path(project_dir)

    # startup이면 복구 불필요 (새 세션)
    if source == "startup":
        output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
        print(json.dumps(output))
        sys.exit(0)

    # compact, resume일 때만 복구
    state_file = project_path / ".claude" / "status" / "session-state.json"

    if not state_file.exists():
        output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
        print(json.dumps(output))
        sys.exit(0)

    try:
        state = json.loads(state_file.read_text(encoding="utf-8"))
    except:
        output = {"hookSpecificOutput": {"hookEventName": "SessionStart", "additionalContext": ""}}
        print(json.dumps(output))
        sys.exit(0)

    # 복구 컨텍스트 생성
    parts = []
    parts.append("# Context Recovery (Auto-injected)")
    parts.append("")
    parts.append(f"> **Source**: {source}")
    parts.append(f"> **Saved at**: {state.get('timestamp', 'unknown')}")

    if state.get("git_branch"):
        parts.append(f"> **Branch**: {state['git_branch']}")

    # 활성 계획
    if state.get("active_plan"):
        parts.append("")
        parts.append(f"## Active Plan: {state['active_plan']}")
        parts.append("")
        parts.append("```markdown")
        # 처음 50줄만
        plan_lines = state.get("plan_content", "").split("\\n")[:50]
        parts.append("\\n".join(plan_lines))
        parts.append("```")

    # 현재 상태 요약
    if state.get("current_md"):
        parts.append("")
        parts.append("## Current Status (from current.md)")
        parts.append("")
        # 처음 40줄만
        current_lines = state["current_md"].split("\\n")[:40]
        parts.append("\\n".join(current_lines))

    # 핵심 규칙
    if state.get("rules"):
        parts.append("")
        parts.append("## Key Rules")
        for rule in state["rules"]:
            parts.append(f"- {rule}")

    parts.append("")
    parts.append("---")
    parts.append("**Continue where you left off.**")

    context = "\\n".join(parts)

    output = {
        "hookSpecificOutput": {
            "hookEventName": "SessionStart",
            "additionalContext": context
        }
    }

    print(json.dumps(output, ensure_ascii=False))
    sys.exit(0)

if __name__ == "__main__":
    main()
'''

# Hook 설정 템플릿
HOOKS_SETTINGS = {
    "PreCompact": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/save-state.py\"",
                    "timeout": 10
                }
            ]
        }
    ],
    "SessionStart": [
        {
            "hooks": [
                {
                    "type": "command",
                    "command": "python \"$CLAUDE_PROJECT_DIR/.claude/hooks/recover-context.py\"",
                    "timeout": 10
                }
            ]
        }
    ]
}


@require_license
async def setup_auto_recovery(
    project_path: str = None
) -> list[TextContent]:
    """
    자동 컨텍스트 복구 설정.

    PreCompact + SessionStart hook을 설치하여:
    - 컨텍스트 압축 전 상태 자동 저장
    - 압축 후 세션 시작 시 자동 복구 + 주입

    Args:
        project_path: 프로젝트 경로 (기본: 현재 디렉토리)
    """
    import json

    # 경로 설정
    if project_path:
        path = Path(project_path)
    else:
        path = Path.cwd()

    if not path.exists():
        return [TextContent(type="text", text=f"# Error\n\nProject path not found: `{path}`")]

    claude_dir = path / ".claude"
    hooks_dir = claude_dir / "hooks"
    status_dir = claude_dir / "status"

    # 디렉토리 생성
    hooks_dir.mkdir(parents=True, exist_ok=True)
    status_dir.mkdir(parents=True, exist_ok=True)

    # Hook 스크립트 설치
    save_state_path = hooks_dir / "save-state.py"
    recover_context_path = hooks_dir / "recover-context.py"

    save_state_path.write_text(SAVE_STATE_SCRIPT, encoding="utf-8")
    recover_context_path.write_text(RECOVER_CONTEXT_SCRIPT, encoding="utf-8")

    # settings.json 업데이트
    settings_path = claude_dir / "settings.json"

    settings = {}
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
        except:
            settings = {}

    # hooks 섹션 병합
    if "hooks" not in settings:
        settings["hooks"] = {}

    settings["hooks"]["PreCompact"] = HOOKS_SETTINGS["PreCompact"]
    settings["hooks"]["SessionStart"] = HOOKS_SETTINGS["SessionStart"]

    settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2), encoding="utf-8")

    return [TextContent(type="text", text=f"""
# Auto Recovery Setup Complete

## Installed Files

| File | Purpose |
|------|---------|
| `.claude/hooks/save-state.py` | PreCompact: Save state before compaction |
| `.claude/hooks/recover-context.py` | SessionStart: Restore state after compaction |
| `.claude/settings.json` | Hook configuration |

## How It Works

```
Context Compaction Triggered
        │
        ▼
┌─────────────────────────────┐
│ PreCompact Hook             │
│ → Save current.md           │
│ → Save active PLAN          │
│ → Save git branch           │
│ → Save key rules            │
└─────────────────────────────┘
        │
        ▼
   [Compaction]
        │
        ▼
┌─────────────────────────────┐
│ SessionStart Hook           │
│ (source: "compact")         │
│ → Read saved state          │
│ → Inject as additionalContext│
│ → Claude knows the context  │
└─────────────────────────────┘
        │
        ▼
Claude continues seamlessly
```

## Saved State Location

`{status_dir / "session-state.json"}`

## Verification

The next time context compaction happens:
1. State will be saved automatically
2. Context will be restored automatically
3. No user intervention needed

**This is the core paid feature of Clouvel Pro.**
""")]


async def check_auto_recovery_status(
    project_path: str = None
) -> list[TextContent]:
    """자동 복구 설정 상태 확인"""
    import json

    if project_path:
        path = Path(project_path)
    else:
        path = Path.cwd()

    claude_dir = path / ".claude"
    hooks_dir = claude_dir / "hooks"
    settings_path = claude_dir / "settings.json"
    state_path = claude_dir / "status" / "session-state.json"

    results = []
    results.append("# Auto Recovery Status\n")

    # Hook 스크립트 확인
    save_state = hooks_dir / "save-state.py"
    recover_context = hooks_dir / "recover-context.py"

    results.append("## Hook Scripts")
    results.append(f"- `save-state.py`: {'Installed' if save_state.exists() else 'Missing'}")
    results.append(f"- `recover-context.py`: {'Installed' if recover_context.exists() else 'Missing'}")

    # 설정 확인
    results.append("\n## Settings")
    if settings_path.exists():
        try:
            settings = json.loads(settings_path.read_text(encoding="utf-8"))
            hooks = settings.get("hooks", {})

            pre_compact = "PreCompact" in hooks
            session_start = "SessionStart" in hooks

            results.append(f"- PreCompact hook: {'Configured' if pre_compact else 'Not configured'}")
            results.append(f"- SessionStart hook: {'Configured' if session_start else 'Not configured'}")
        except:
            results.append("- Error reading settings.json")
    else:
        results.append("- settings.json not found")

    # 저장된 상태 확인
    results.append("\n## Last Saved State")
    if state_path.exists():
        try:
            state = json.loads(state_path.read_text(encoding="utf-8"))
            results.append(f"- Timestamp: {state.get('timestamp', 'unknown')}")
            results.append(f"- Trigger: {state.get('trigger', 'unknown')}")
            results.append(f"- Active Plan: {state.get('active_plan', 'None')}")
            results.append(f"- Git Branch: {state.get('git_branch', 'unknown')}")
        except:
            results.append("- Error reading state file")
    else:
        results.append("- No saved state yet (will be created on first compaction)")

    # 전체 상태
    all_good = (
        save_state.exists() and
        recover_context.exists() and
        settings_path.exists()
    )

    results.append("\n## Overall")
    if all_good:
        results.append("**Status: READY**")
        results.append("\nAuto recovery is properly configured.")
    else:
        results.append("**Status: NOT CONFIGURED**")
        results.append("\nRun `setup_auto_recovery` to enable auto recovery.")

    return [TextContent(type="text", text="\n".join(results))]
