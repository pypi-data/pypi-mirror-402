# /learn-error - 에러 학습 자동화 (v2)

> **목적**: 에러 수집 → 패턴 분석 → 방지 규칙 생성 → CLAUDE.md 규칙화
> **Pro 기능**: MCP 도구 연동 (`log_error`, `analyze_error`, `add_prevention_rule`)

---

## 사용법

```bash
/learn-error              # 전체 에러 학습
/learn-error --analyze    # 분석만 (히스토리 포함)
/learn-error --summary    # 요약 리포트
```

---

## 에러 수집 방법

```
┌───────────────────────┬──────────────────────────────────┐
│       시나리오        │            접근 방법             │
├───────────────────────┼──────────────────────────────────┤
│ 터미널 에러           │ Claude Code가 자동 감지 ✅       │
│                       │ → log_error 도구 자동 호출       │
├───────────────────────┼──────────────────────────────────┤
│ 로그 파일             │ watch_logs → check_logs          │
│                       │ → 발견된 에러 자동 기록          │
├───────────────────────┼──────────────────────────────────┤
│ 브라우저 에러         │ 사용자가 복붙                    │
│                       │ → log_error(source="browser")    │
├───────────────────────┼──────────────────────────────────┤
│ 수동 입력             │ 사용자가 에러 전달               │
│                       │ → log_error(source="manual")     │
└───────────────────────┴──────────────────────────────────┘
```

---

## 실행 프로세스

```
/learn-error
    │
    ├── Phase 1: 에러 수집
    │   ├── .clouvel/errors/error_log.jsonl 읽기
    │   ├── .clouvel/errors/patterns.json 통계
    │   └── 최근 로그 파일 스캔 (check_logs)
    │
    ├── Phase 2: 패턴 분석 (analyze_error)
    │   ├── 자동 분류된 패턴 확인
    │   ├── 반복 패턴 식별 (3회+ 주의)
    │   └── 근본 원인 추정
    │
    ├── Phase 3: 규칙 생성
    │   ├── NEVER/ALWAYS 형식
    │   └── add_prevention_rule 호출
    │
    ├── Phase 4: 적용
    │   ├── .clouvel/errors/prevention_rules.json 저장
    │   └── CLAUDE.md에 규칙 추가 제안
    │
    └── Phase 5: 리포트 (get_error_summary)
```

---

## Phase 1: 에러 수집

### MCP 도구 호출

```
analyze_error(path=".", include_history=true)
```

### 자동 분류되는 에러 패턴

| 패턴 | 카테고리 | 자동 방지책 |
|------|----------|-------------|
| `type_error` | 타입 에러 | TypeScript strict, null 체크 |
| `null_error` | Null 참조 | Optional chaining |
| `import_error` | 임포트 에러 | 의존성 확인, 경로 검증 |
| `syntax_error` | 문법 에러 | 린터 활성화 |
| `network_error` | 네트워크 에러 | 재시도 로직, 타임아웃 |
| `permission_error` | 권한 에러 | 권한 체크 |
| `database_error` | DB 에러 | 트랜잭션, 제약조건 |

### 출력 형식

```markdown
## 📊 에러 현황

| 타입 | 횟수 | 마지막 발생 |
|------|------|-------------|
| 타입 에러 | 5 | 2026-01-17 |
| Null 참조 | 3 | 2026-01-16 |
| 네트워크 에러 | 2 | 2026-01-15 |

**총 에러**: 10건
**3회+ 반복**: 2종류 ⚠️
```

---

## Phase 2: 패턴 분석

### 반복 패턴 식별

```markdown
### ⚠️ 반복 에러 (3회+)

**타입 에러 - 5회**
- 공통점: API 응답에서 undefined 접근
- 위치: src/api/*.ts
- 권장: Optional chaining 필수

**Null 참조 - 3회**
- 공통점: state 초기화 전 접근
- 위치: src/hooks/*.ts
- 권장: 초기값 설정
```

### 근본 원인 추정

```markdown
### 🎯 근본 원인

1. **타입 안전성 부족** (7건)
   - null/undefined 가드 미적용
   - TypeScript strict 미사용

2. **외부 API 방어 부족** (2건)
   - Rate limit, timeout 미설정

3. **상태 관리 실수** (1건)
   - 비동기 상태 초기화
```

---

## Phase 3: 규칙 생성

### MCP 도구 호출

```
add_prevention_rule(
    path=".",
    error_type="type_error",
    rule="외부 API 응답은 반드시 optional chaining 사용",
    scope="project"
)
```

### NEVER 규칙

```markdown
### 🚫 추가할 NEVER 규칙

1. **NEVER** 외부 데이터 사용 without null 체크
   ```typescript
   // ❌ NEVER
   const name = response.data.user.name;

   // ✅ INSTEAD
   const name = response.data?.user?.name ?? 'Unknown';
   ```

2. **NEVER** 외부 API 호출 without timeout
   ```typescript
   // ❌ NEVER
   await fetch(url);

   // ✅ INSTEAD
   await fetch(url, { signal: AbortSignal.timeout(5000) });
   ```
```

### ALWAYS 규칙

```markdown
### ✅ 추가할 ALWAYS 규칙

1. **ALWAYS** 서버 시작 시 필수 환경변수 검증
2. **ALWAYS** API 호출 시 에러 핸들링 포함
3. **ALWAYS** 상태 접근 전 초기화 확인
```

---

## Phase 4: 적용

### 저장 위치

```
.clouvel/errors/
├── error_log.jsonl        # 에러 로그 (JSONL)
├── patterns.json          # 패턴별 통계
└── prevention_rules.json  # 방지 규칙
```

### CLAUDE.md 업데이트 제안

```markdown
## 에러 방지 규칙 (자동 생성)

> 이 섹션은 /learn-error로 자동 생성되었습니다.
> 마지막 업데이트: 2026-01-17

### 타입 에러 방지
- 외부 API 응답은 반드시 optional chaining 사용
- undefined 가능성 있는 값은 기본값 설정

### 네트워크 에러 방지
- 모든 API 호출에 timeout 5초 설정
- 재시도 로직 포함 (최대 3회)
```

---

## Phase 5: 리포트

### MCP 도구 호출

```
get_error_summary(path=".", days=30)
```

### 리포트 형식

```markdown
## ✅ 에러 학습 완료

### 요약
| 항목 | 값 |
|------|-----|
| 분석된 에러 | 10건 |
| 식별된 패턴 | 3종류 |
| 추가된 규칙 | 5개 |

### 적용된 규칙
1. NEVER 외부 데이터 without null 체크
2. NEVER 외부 API without timeout
3. ALWAYS 서버 시작 시 환경변수 검증
4. ALWAYS API 호출 시 에러 핸들링
5. ALWAYS 상태 접근 전 초기화 확인

### 효과
- 예상 에러 감소: 70%
- 자동 방지: 활성화됨

---

**다음 학습**: 새 에러가 쌓이면 `/learn-error` 다시 실행
```

---

## 로그 파일 모니터링 설정

### 초기 설정

```
watch_logs(
    path=".",
    log_paths=["logs/*.log", "*.log", ".next/server/*.log"],
    patterns=["Error:", "ERROR", "Exception:", "FATAL"]
)
```

### 수동 스캔

```
check_logs(path=".")
```

---

## 예시 전체 플로우

```markdown
사용자: /learn-error

Claude: 에러 학습을 시작합니다.

## Phase 1: 에러 수집
[analyze_error 호출]

총 10건의 에러가 기록되어 있습니다.
- 타입 에러: 5건
- Null 참조: 3건
- 네트워크 에러: 2건

## Phase 2: 패턴 분석

⚠️ 반복 에러 발견:
- 타입 에러 (5회) - 주의 필요

근본 원인:
1. Optional chaining 미사용
2. API 응답 검증 누락

## Phase 3: 규칙 생성
[add_prevention_rule 호출]

2개의 NEVER 규칙, 3개의 ALWAYS 규칙 생성

## Phase 4: 적용

✅ .clouvel/errors/prevention_rules.json 저장
📝 CLAUDE.md 업데이트 제안 생성

## Phase 5: 리포트
[get_error_summary 호출]

학습 완료! 5개의 방지 규칙이 활성화되었습니다.
이 패턴의 에러는 앞으로 자동으로 감지됩니다.
```

---

## 기존 ERROR_LOG.md 마이그레이션

기존 ERROR_LOG.md가 있다면:

```bash
# 기존 에러를 새 시스템으로 마이그레이션
# 각 에러를 log_error로 기록

log_error(
    path=".",
    error_text="[기존 ERROR_LOG.md의 에러 내용]",
    source="manual"
)
```

마이그레이션 후 ERROR_LOG.md는 보관하거나 삭제 가능.
