# -*- coding: utf-8 -*-
"""Error learning tools: log_error, analyze_error, watch_logs, add_prevention_rule"""

import re
import json
from pathlib import Path
from datetime import datetime
from mcp.types import TextContent

from ..license import require_license, require_license_premium

# 에러 패턴 정의
ERROR_PATTERNS = {
    "type_error": {
        "patterns": [r"TypeError:", r"type\s+error", r"is not a function", r"undefined is not"],
        "category": "타입 에러",
        "prevention": "타입 체크 강화, TypeScript strict 모드"
    },
    "null_error": {
        "patterns": [r"null|undefined", r"Cannot read propert", r"is null", r"is undefined"],
        "category": "Null 참조",
        "prevention": "Optional chaining, null 체크 추가"
    },
    "import_error": {
        "patterns": [r"Cannot find module", r"Module not found", r"ImportError", r"ModuleNotFoundError"],
        "category": "임포트 에러",
        "prevention": "의존성 확인, 경로 검증"
    },
    "syntax_error": {
        "patterns": [r"SyntaxError", r"Unexpected token", r"Parse error"],
        "category": "문법 에러",
        "prevention": "린터 활성화, 저장 시 포맷팅"
    },
    "network_error": {
        "patterns": [r"ECONNREFUSED", r"fetch failed", r"NetworkError", r"timeout", r"ETIMEDOUT"],
        "category": "네트워크 에러",
        "prevention": "재시도 로직, 타임아웃 설정"
    },
    "permission_error": {
        "patterns": [r"EACCES", r"Permission denied", r"PermissionError", r"403"],
        "category": "권한 에러",
        "prevention": "권한 체크, 적절한 에러 핸들링"
    },
    "database_error": {
        "patterns": [r"SQLITE", r"PostgreSQL", r"MySQL", r"duplicate key", r"constraint violation"],
        "category": "DB 에러",
        "prevention": "트랜잭션 처리, 제약조건 검증"
    },
}


def _get_error_log_path(project_path: str) -> Path:
    """에러 로그 경로"""
    return Path(project_path) / ".clouvel" / "errors"


def _classify_error(error_text: str) -> dict:
    """에러 분류"""
    error_lower = error_text.lower()

    for error_type, config in ERROR_PATTERNS.items():
        for pattern in config["patterns"]:
            if re.search(pattern, error_text, re.IGNORECASE):
                return {
                    "type": error_type,
                    "category": config["category"],
                    "prevention": config["prevention"]
                }

    return {
        "type": "unknown",
        "category": "기타 에러",
        "prevention": "로그 분석 후 패턴 추가"
    }


def _extract_stack_info(error_text: str) -> dict:
    """스택 트레이스에서 정보 추출"""
    info = {
        "file": None,
        "line": None,
        "function": None
    }

    # JavaScript/TypeScript 패턴
    js_match = re.search(r'at\s+(\S+)\s+\(([^:]+):(\d+):', error_text)
    if js_match:
        info["function"] = js_match.group(1)
        info["file"] = js_match.group(2)
        info["line"] = js_match.group(3)
        return info

    # Python 패턴
    py_match = re.search(r'File\s+"([^"]+)",\s+line\s+(\d+),\s+in\s+(\S+)', error_text)
    if py_match:
        info["file"] = py_match.group(1)
        info["line"] = py_match.group(2)
        info["function"] = py_match.group(3)
        return info

    return info


@require_license_premium
async def log_error(
    path: str,
    error_text: str,
    context: str = "",
    source: str = "terminal"
) -> list[TextContent]:
    """에러 로깅 및 분류"""
    log_path = _get_error_log_path(path)
    log_path.mkdir(parents=True, exist_ok=True)

    # 에러 분류
    classification = _classify_error(error_text)
    stack_info = _extract_stack_info(error_text)

    # 에러 기록
    timestamp = datetime.now().isoformat()
    error_entry = {
        "timestamp": timestamp,
        "source": source,
        "context": context,
        "error_text": error_text[:2000],  # 너무 길면 자르기
        "classification": classification,
        "stack_info": stack_info
    }

    # 로그 파일에 추가
    log_file = log_path / "error_log.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(error_entry, ensure_ascii=False) + "\n")

    # 패턴 카운트 업데이트
    pattern_file = log_path / "patterns.json"
    patterns = {}
    if pattern_file.exists():
        patterns = json.loads(pattern_file.read_text(encoding="utf-8"))

    error_type = classification["type"]
    if error_type not in patterns:
        patterns[error_type] = {"count": 0, "last_seen": None, "examples": []}

    patterns[error_type]["count"] += 1
    patterns[error_type]["last_seen"] = timestamp
    if len(patterns[error_type]["examples"]) < 3:
        patterns[error_type]["examples"].append(error_text[:200])

    pattern_file.write_text(json.dumps(patterns, ensure_ascii=False, indent=2), encoding="utf-8")

    return [TextContent(type="text", text=f"""
# 에러 기록됨

## 분류
- **타입**: {classification['category']}
- **소스**: {source}
- **시간**: {timestamp}

## 위치
- 파일: {stack_info['file'] or '알 수 없음'}
- 라인: {stack_info['line'] or '알 수 없음'}
- 함수: {stack_info['function'] or '알 수 없음'}

## 방지책
{classification['prevention']}

## 다음 단계
1. `analyze_error` 도구로 상세 분석
2. `add_prevention_rule` 도구로 방지 규칙 추가
""")]


@require_license_premium
async def analyze_error(
    path: str,
    error_text: str = "",
    include_history: bool = True
) -> list[TextContent]:
    """에러 상세 분석"""
    log_path = _get_error_log_path(path)

    result = "# 에러 분석\n\n"

    # 입력된 에러 분석
    if error_text:
        classification = _classify_error(error_text)
        stack_info = _extract_stack_info(error_text)

        result += f"""## 현재 에러

### 분류
- **타입**: {classification['category']}
- **코드**: {classification['type']}

### 위치
- 파일: {stack_info['file'] or '알 수 없음'}
- 라인: {stack_info['line'] or '알 수 없음'}
- 함수: {stack_info['function'] or '알 수 없음'}

### 권장 조치
{classification['prevention']}

### 에러 원문
```
{error_text[:500]}
```

"""

    # 히스토리 분석
    if include_history:
        pattern_file = log_path / "patterns.json"
        if pattern_file.exists():
            patterns = json.loads(pattern_file.read_text(encoding="utf-8"))

            if patterns:
                result += "## 에러 히스토리\n\n"
                result += "| 타입 | 횟수 | 마지막 발생 |\n"
                result += "|------|------|-------------|\n"

                sorted_patterns = sorted(
                    patterns.items(),
                    key=lambda x: x[1]["count"],
                    reverse=True
                )

                for error_type, data in sorted_patterns[:10]:
                    category = ERROR_PATTERNS.get(error_type, {}).get("category", error_type)
                    last_seen = data["last_seen"][:10] if data["last_seen"] else "-"
                    result += f"| {category} | {data['count']} | {last_seen} |\n"

                # 가장 많이 발생한 에러 타입
                if sorted_patterns:
                    top_error = sorted_patterns[0]
                    top_type = top_error[0]
                    top_count = top_error[1]["count"]

                    prevention = ERROR_PATTERNS.get(top_type, {}).get("prevention", "분석 필요")

                    result += f"""
### 가장 빈번한 에러
- **타입**: {ERROR_PATTERNS.get(top_type, {}).get('category', top_type)}
- **횟수**: {top_count}회
- **권장 조치**: {prevention}
"""
        else:
            result += "## 에러 히스토리\n\n아직 기록된 에러가 없습니다.\n"

    if not error_text and not include_history:
        result += "분석할 에러가 없습니다. error_text를 제공하거나 include_history=true로 설정하세요.\n"

    return [TextContent(type="text", text=result)]


@require_license
async def watch_logs(
    path: str,
    log_paths: list[str] = None,
    patterns: list[str] = None
) -> list[TextContent]:
    """로그 파일 모니터링 설정"""
    config_path = _get_error_log_path(path)
    config_path.mkdir(parents=True, exist_ok=True)

    # 기본 로그 경로
    default_paths = [
        "logs/*.log",
        "*.log",
        "npm-debug.log",
        "yarn-error.log",
        ".next/server/pages-errors.log"
    ]

    # 기본 에러 패턴
    default_patterns = [
        r"Error:",
        r"ERROR",
        r"Exception:",
        r"FATAL",
        r"Failed",
        r"Traceback"
    ]

    watch_config = {
        "log_paths": log_paths or default_paths,
        "error_patterns": patterns or default_patterns,
        "enabled": True,
        "last_check": None
    }

    config_file = config_path / "watch_config.json"
    config_file.write_text(json.dumps(watch_config, ensure_ascii=False, indent=2), encoding="utf-8")

    return [TextContent(type="text", text=f"""
# 로그 모니터링 설정 완료

## 감시 대상
```
{chr(10).join(watch_config['log_paths'])}
```

## 에러 패턴
```
{chr(10).join(watch_config['error_patterns'])}
```

## 사용법
로그 파일에서 에러를 발견하면:
1. `log_error` 도구로 기록
2. `analyze_error` 도구로 분석
3. `add_prevention_rule` 도구로 방지 규칙 추가

## 팁
- 커스텀 로그 경로 추가: log_paths 파라미터 사용
- 커스텀 패턴 추가: patterns 파라미터 사용
""")]


@require_license
async def check_logs(path: str) -> list[TextContent]:
    """로그 파일 스캔 (수동 체크)"""
    config_path = _get_error_log_path(path)
    config_file = config_path / "watch_config.json"

    if not config_file.exists():
        return [TextContent(type="text", text="로그 모니터링이 설정되지 않았습니다. `watch_logs` 도구를 먼저 실행하세요.")]

    config = json.loads(config_file.read_text(encoding="utf-8"))
    project_path = Path(path)

    found_errors = []

    for log_pattern in config["log_paths"]:
        for log_file in project_path.glob(log_pattern):
            if not log_file.is_file():
                continue

            try:
                content = log_file.read_text(encoding="utf-8", errors="ignore")
                lines = content.split("\n")

                for i, line in enumerate(lines[-100:]):  # 마지막 100줄만
                    for pattern in config["error_patterns"]:
                        if re.search(pattern, line, re.IGNORECASE):
                            found_errors.append({
                                "file": str(log_file),
                                "line_num": len(lines) - 100 + i + 1,
                                "content": line[:200]
                            })
                            break
            except Exception:
                continue

    if not found_errors:
        return [TextContent(type="text", text="# 로그 체크 완료\n\n에러가 발견되지 않았습니다.")]

    result = f"# 로그 체크 결과\n\n{len(found_errors)}개 에러 발견\n\n"

    for i, error in enumerate(found_errors[:20], 1):
        result += f"## {i}. {error['file']}:{error['line_num']}\n"
        result += f"```\n{error['content']}\n```\n\n"

    if len(found_errors) > 20:
        result += f"\n... 외 {len(found_errors) - 20}개 더\n"

    result += "\n## 다음 단계\n`log_error` 도구로 중요한 에러를 기록하세요.\n"

    return [TextContent(type="text", text=result)]


@require_license_premium
async def add_prevention_rule(
    path: str,
    error_type: str,
    rule: str,
    scope: str = "project"
) -> list[TextContent]:
    """에러 방지 규칙 추가"""
    log_path = _get_error_log_path(path)
    log_path.mkdir(parents=True, exist_ok=True)

    rules_file = log_path / "prevention_rules.json"
    rules = {}
    if rules_file.exists():
        rules = json.loads(rules_file.read_text(encoding="utf-8"))

    if error_type not in rules:
        rules[error_type] = {
            "rules": [],
            "scope": scope,
            "added": datetime.now().isoformat()
        }

    if rule not in rules[error_type]["rules"]:
        rules[error_type]["rules"].append(rule)

    rules_file.write_text(json.dumps(rules, ensure_ascii=False, indent=2), encoding="utf-8")

    # CLAUDE.md에 규칙 추가 제안
    claude_md_path = Path(path) / "CLAUDE.md"
    suggestion = ""

    if claude_md_path.exists():
        suggestion = f"""
## CLAUDE.md 업데이트 제안

다음 내용을 CLAUDE.md에 추가하세요:

```markdown
## 에러 방지 규칙

### {ERROR_PATTERNS.get(error_type, {}).get('category', error_type)}
- {rule}
```
"""

    return [TextContent(type="text", text=f"""
# 방지 규칙 추가됨

## 규칙
- **에러 타입**: {error_type}
- **규칙**: {rule}
- **범위**: {scope}

## 현재 등록된 규칙
{json.dumps(rules, ensure_ascii=False, indent=2)}
{suggestion}
""")]


@require_license_premium
async def get_error_summary(path: str, days: int = 30) -> list[TextContent]:
    """에러 요약 리포트"""
    log_path = _get_error_log_path(path)

    if not log_path.exists():
        return [TextContent(type="text", text="에러 기록이 없습니다.")]

    result = f"# 에러 요약 (최근 {days}일)\n\n"

    # 패턴 통계
    pattern_file = log_path / "patterns.json"
    if pattern_file.exists():
        patterns = json.loads(pattern_file.read_text(encoding="utf-8"))

        total_errors = sum(p["count"] for p in patterns.values())
        result += f"**총 에러 수**: {total_errors}\n\n"

        if patterns:
            result += "## 에러 타입별 통계\n\n"
            result += "| 타입 | 횟수 | 비율 |\n"
            result += "|------|------|------|\n"

            sorted_patterns = sorted(
                patterns.items(),
                key=lambda x: x[1]["count"],
                reverse=True
            )

            for error_type, data in sorted_patterns:
                category = ERROR_PATTERNS.get(error_type, {}).get("category", error_type)
                ratio = (data["count"] / total_errors * 100) if total_errors > 0 else 0
                result += f"| {category} | {data['count']} | {ratio:.1f}% |\n"

    # 방지 규칙
    rules_file = log_path / "prevention_rules.json"
    if rules_file.exists():
        rules = json.loads(rules_file.read_text(encoding="utf-8"))

        if rules:
            result += "\n## 등록된 방지 규칙\n\n"
            for error_type, data in rules.items():
                category = ERROR_PATTERNS.get(error_type, {}).get("category", error_type)
                result += f"### {category}\n"
                for rule in data["rules"]:
                    result += f"- {rule}\n"
                result += "\n"

    return [TextContent(type="text", text=result)]
