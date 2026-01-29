# Clouvel 전략적 백로그

> AI 에이전트 시대를 위한 정책 엔진으로의 진화

---

## AI 트렌드 배경 (2026~)

| 트렌드 | 변화 | Clouvel 기회 |
|--------|------|--------------|
| IDE 보조 → 레포 변경 에이전트 | 멀티파일 변경 + 테스트 실행 + 반복 수정이 기본값 | "왜 바꿨는지" 기록이 핵심 가치 |
| 단일 → 멀티 에이전트 | 여러 에이전트가 분업하는 흐름 | 공통 정책 통과 게이트 필요 |
| MCP 표준 확산 | 도구/데이터 연결 표준 | 정책 MCP 서버로 확장 가능 |
| Evals 필수화 | 에이전트 평가 체계화 | 정책이 품질을 올리는지 증명 필요 |
| 규제/거버넌스 구매 조건화 | EU AI Act 등 기록/통제/책임 요구 | Evidence Pack = B2B 결제 버튼 |

---

## 우선순위 프레임워크

### RICE 기준

| 항목 | 설명 |
|------|------|
| **R**each | 영향받는 사용자 % |
| **I**mpact | 개별 사용자 영향 (0.25/0.5/1/2/3) |
| **C**onfidence | 추정 확신도 (%) |
| **E**ffort | 인원-월 |

**RICE Score = (R × I × C) / E**

---

## 단기 백로그 (0~3개월): 제품화 + 전환 + 신뢰

> **목표**: 설치 60초 + 데모 1장 + "어디서 되나" 3초 이해

### B1. Works-with 배지 시스템

**목표**: 랜딩 최상단에 호환성 배지 배치

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 배지 디자인 | 100% | 2 | 95% | 0.2 | 950 |
| 랜딩페이지 배치 | 100% | 2 | 90% | 0.3 | 600 |

**배지 목록**:
- [ ] CLI
- [ ] Claude Desktop
- [ ] VS Code
- [ ] Cursor

**메시지**: "한 번 설치하면 어디서든 같은 정책"

**검증 기준**:
- [ ] 배지 4개 모두 표시
- [ ] 클릭 시 설치 가이드로 이동

---

### B2. Quickstart 60초

**목표**: docs 첫 화면에서 설치 → 연결 → BLOCK 확인까지 한 줄로

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 원라인 설치 스크립트 | 100% | 3 | 90% | 0.3 | 900 |
| 60초 Quickstart 문서 | 100% | 3 | 85% | 0.5 | 510 |

**흐름**:
```bash
# 1. 설치 (10초)
pip install clouvel-pro

# 2. 활성화 (20초)
clouvel activate CLOUVEL-PERSONAL-XXXXX

# 3. PRD 없으면 BLOCK 확인 (30초)
clouvel gate --check
# → ❌ BLOCK: PRD.md 없음
```

**검증 기준**:
- [ ] 신규 사용자가 60초 내 BLOCK 메시지 확인
- [ ] 설치 완료율 70% 이상

---

### B3. BLOCK/PASS 통일 데모

**목표**: 모든 마케팅/README/Docs에서 동일 이미지 재사용

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 스크린샷 제작 | 100% | 2 | 90% | 0.2 | 900 |
| README 적용 | 100% | 2 | 85% | 0.1 | 1700 |
| 랜딩 적용 | 100% | 2 | 85% | 0.2 | 850 |

**데모 시나리오**:
```
┌─────────────────────────────────────┐
│  ❌ BLOCK: PRD.md 없음              │
│  ────────────────────               │
│  필수 문서가 없습니다.               │
│  /plan 실행 전 PRD.md를 작성하세요. │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│  ✅ PASS: 모든 검증 통과            │
│  ────────────────────               │
│  PRD.md ✓ | ARCH.md ✓ | Tests ✓    │
│  커밋 진행 가능                     │
└─────────────────────────────────────┘
```

**검증 기준**:
- [ ] BLOCK/PASS 이미지 통일
- [ ] 3초 내 이해 (스크롤/이탈 감소)

---

### B4. 가벼운 품질 게이트 추가

**목표**: "PRD 없음" 외 최소 조건 2~3개 추가

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| ARCH.md WARN | 80% | 1 | 85% | 0.3 | 227 |
| ACCEPTANCE BLOCK | 90% | 2 | 80% | 0.4 | 360 |
| 테스트 최소 요구 | 70% | 2 | 75% | 0.5 | 210 |

**규칙**:
| 조건 | 동작 | 이유 |
|------|------|------|
| PRD.md 없음 | BLOCK | 의도 없이 시작 방지 |
| ARCH.md 없음 | WARN | 구조 문서 권장 |
| acceptance 섹션 없음 | BLOCK | 완료 기준 필수 |
| 테스트 0개 | WARN | 품질 게이트 최소 요구 |

**검증 기준**:
- [ ] 각 조건별 BLOCK/WARN 동작
- [ ] 사용자 피드백으로 조건 조정

---

### 단기 성공 지표

| 지표 | 목표 |
|------|------|
| 설치 완료율 (Quickstart 끝까지) | 70%+ |
| BLOCK/PASS 이해 시간 | 3초 이내 |
| 랜딩 → docs 전환율 | 40%+ |
| docs → 설치 전환율 | 50%+ |

---

## 중기 백로그 (3~9개월): 정책 엔진

> **목표**: "PRD 있냐 없냐"가 아니라 팀/프로젝트별 개발 규칙을 굴리는 엔진

### B5. clouvel.policy.yml 도입 (핵심)

**목표**: 선언적 정책 파일로 팀별 규칙 정의

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 스키마 설계 | 100% | 3 | 80% | 1 | 240 |
| 파서 구현 | 100% | 3 | 85% | 1.5 | 170 |
| 검증 엔진 통합 | 100% | 3 | 80% | 2 | 120 |
| 문서화 | 100% | 2 | 90% | 0.5 | 360 |

**예시**:
```yaml
# clouvel.policy.yml
version: "1.0"
name: "my-team-policy"

require_docs:
  - PRD.md
  - ARCH.md

require_sections:
  PRD.md:
    - scope
    - non_goals
    - acceptance
    - determinism
    - tests

quality_gates:
  min_tests: 8
  min_coverage: 60%

block_on:
  - missing_healthz
  - missing_ci
  - no_acceptance_criteria

warn_on:
  - no_arch_doc
  - low_test_count
```

**검증 기준**:
- [ ] YAML 파싱 및 검증
- [ ] 정책 기반 BLOCK/WARN/PASS 동작
- [ ] 팀이 정책 파일을 커밋하기 시작

---

### B6. 표준 JSON 출력 포맷

**목표**: 모든 클라이언트에서 동일한 결과 포맷 사용

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| JSON 스키마 정의 | 100% | 2 | 90% | 0.5 | 360 |
| CLI 출력 변환 | 100% | 2 | 85% | 0.5 | 340 |
| MCP 응답 통합 | 100% | 2 | 80% | 0.8 | 200 |

**출력 포맷**:
```json
{
  "version": "1.0",
  "timestamp": "2026-01-17T12:00:00Z",
  "result": "BLOCK",
  "policy": {
    "name": "my-team-policy",
    "version": "1.0",
    "hash": "abc123"
  },
  "checks": [
    {
      "name": "require_docs.PRD.md",
      "status": "PASS",
      "message": "PRD.md exists"
    },
    {
      "name": "require_sections.acceptance",
      "status": "BLOCK",
      "message": "acceptance section missing in PRD.md"
    }
  ],
  "summary": {
    "pass": 5,
    "warn": 1,
    "block": 1
  }
}
```

**검증 기준**:
- [ ] CLI/VS Code/Cursor/Desktop에서 동일 결과
- [ ] 스키마 버전 관리

---

### B7. 예외 승인 플로우

**목표**: 현실적 운영을 위한 예외 처리 + 감사 로그

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 예외 요청 CLI | 80% | 2 | 75% | 0.8 | 150 |
| 예외 승인 저장 | 80% | 3 | 80% | 1 | 192 |
| 예외 만료 처리 | 70% | 2 | 70% | 0.5 | 196 |

**예외 구조**:
```yaml
# .clouvel/exceptions.yml
exceptions:
  - id: "exc-001"
    rule: "min_tests"
    reason: "레거시 마이그레이션 중"
    approved_by: "tech-lead@example.com"
    expires: "2026-03-01"
    created_at: "2026-01-17"
```

**검증 기준**:
- [ ] 예외 승인 시 로그 기록
- [ ] 만료된 예외 자동 비활성화
- [ ] 예외 사유/기간/승인자 추적 가능

---

### B8. Evidence Pack v1

**목표**: 검증 결과 자동 기록 패키지

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 기본 구조 설계 | 90% | 3 | 80% | 1 | 216 |
| 자동 생성 구현 | 90% | 3 | 75% | 1.5 | 135 |
| 저장 위치 설정 | 90% | 2 | 85% | 0.3 | 510 |

**Evidence Pack 구조**:
```
.clouvel/evidence/
├── 2026-01-17_12-00-00/
│   ├── result.json          # 검증 결과
│   ├── policy.yml           # 적용된 정책 (스냅샷)
│   ├── input_hashes.json    # 입력 파일 해시
│   ├── change_summary.md    # 변경 요약
│   └── metadata.json        # 환경 정보
```

**result.json 예시**:
```json
{
  "pack_version": "1.0",
  "generated_at": "2026-01-17T12:00:00Z",
  "result": "PASS",
  "policy_version": "1.0",
  "policy_hash": "sha256:abc123...",
  "input_files": {
    "PRD.md": "sha256:def456...",
    "ARCH.md": "sha256:ghi789..."
  },
  "checks_passed": 8,
  "checks_warned": 1,
  "checks_blocked": 0,
  "change_summary": "Added user authentication feature"
}
```

**검증 기준**:
- [ ] 매 gate 실행 시 Evidence Pack 생성
- [ ] 이전 결과 조회 가능
- [ ] 감사 요청 시 문서로 제출 가능

---

### 중기 성공 지표

| 지표 | 목표 |
|------|------|
| 팀이 policy.yml 커밋 | 10+ 팀 |
| 예외 승인이 로그로 추적 가능 | 100% |
| Evidence Pack 자동 생성률 | 95%+ |

---

## 장기 백로그 (9~18개월): B2B급 방어선

> **목표**: 에이전트가 더 강해져도 Clouvel이 필수 인프라로 남기

### B9. Safety Layer

**목표**: 에이전트 위험 행동 분류 및 차단

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 위험 행동 분류 체계 | 70% | 3 | 70% | 2 | 73.5 |
| 대량 삭제 감지 | 80% | 3 | 75% | 1.5 | 120 |
| 시크릿 접근 감지 | 90% | 3 | 80% | 2 | 108 |
| Human-in-the-loop UI | 60% | 3 | 65% | 3 | 39 |

**위험 분류**:
| 레벨 | 행동 | 기본 동작 |
|------|------|----------|
| CRITICAL | 대량 파일 삭제 (10+) | BLOCK + 알림 |
| CRITICAL | 시크릿/크레덴셜 접근 | Human 확인 |
| HIGH | 대규모 리팩터링 (100+ 라인) | WARN + 로그 |
| HIGH | 외부 API 호출 | WARN |
| MEDIUM | 설정 파일 수정 | 로그 |

**검증 기준**:
- [ ] 위험 행동 감지 정확도 90%+
- [ ] Human-in-the-loop 응답 시간 30초 이내
- [ ] 오탐률 5% 이하

---

### B10. Eval Harness

**목표**: 정책이 실제로 품질을 올리는지 증명

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| 회귀 시나리오 설계 | 60% | 3 | 70% | 1.5 | 84 |
| 자동화 테스트 구현 | 60% | 3 | 65% | 2 | 58.5 |
| 메트릭 대시보드 | 50% | 2 | 60% | 2 | 30 |

**회귀 시나리오**:
```yaml
# clouvel.evals.yml
scenarios:
  - name: "prd_block"
    description: "PRD 없으면 BLOCK"
    setup:
      remove: ["PRD.md"]
    expected: "BLOCK"

  - name: "test_warn"
    description: "테스트 없으면 WARN"
    setup:
      empty_dir: ["tests/"]
    expected: "WARN"

  - name: "full_pass"
    description: "모든 조건 충족 시 PASS"
    setup:
      ensure: ["PRD.md", "ARCH.md", "tests/test_*.py"]
    expected: "PASS"
```

**메트릭**:
| 메트릭 | 설명 |
|--------|------|
| Groundedness | 정책 규칙이 실제 파일 상태와 일치 |
| Coverage | 검증 가능한 조건의 비율 |
| Consistency | 동일 입력에 동일 결과 |

**검증 기준**:
- [ ] 회귀 시나리오 100% 통과
- [ ] 정책 변경 시 영향 분석 가능
- [ ] 품질 개선 데이터 제공

---

### B11. Compliance Pack

**목표**: 규제/조달 대응 문서 자동 생성

| 항목 | R | I | C | E | Score |
|------|---|---|---|---|-------|
| EU AI Act 매핑 | 40% | 3 | 60% | 2 | 36 |
| 감사 리포트 템플릿 | 50% | 2 | 70% | 1 | 70 |
| 자동 문서 생성 | 40% | 3 | 60% | 3 | 24 |

**Compliance Pack 구조**:
```
.clouvel/compliance/
├── audit_report.md           # 감사 리포트
├── policy_history.json       # 정책 변경 이력
├── exception_log.json        # 예외 승인 이력
├── evidence_index.json       # Evidence Pack 인덱스
└── responsibility_matrix.md  # 책임 소재 매트릭스
```

**검증 기준**:
- [ ] 감사 질문에 문서로 답변 가능
- [ ] EU AI Act 요구사항 매핑
- [ ] B2B 구매 체크리스트 통과

---

### 장기 성공 지표

| 지표 | 목표 |
|------|------|
| "이거 없으면 프로덕션 못 넣음" 팀 | 5+ |
| 감사/보안 질문 문서 응답률 | 90%+ |
| Safety Layer 오탐률 | 5% 이하 |

---

## 분기 점검 체크리스트

> 매 3개월 1회, 60분

### 1. 클라이언트 변화
- [ ] Cursor/Claude Desktop/VS Code의 "툴 실행 방식" 변경?
- [ ] 새로운 AI 코딩 도구 등장?
- [ ] 기존 연동 방식 deprecated?

### 2. 에이전트 위험 사건
- [ ] 파일 삭제/권한 사고/인젝션 사례 증가?
- [ ] 새로운 위험 패턴 발견?
- [ ] Safety Layer 우선순위 조정 필요?

### 3. 표준 변화
- [ ] MCP 스펙/권장 패턴 변경?
- [ ] 새로운 연결 표준 등장?
- [ ] 정책 MCP 서버 전환 시점?

### 4. 사용자 피드백 Top3
- [ ] "막히는 지점"이 설치? 정책? 증거?
- [ ] 가장 많이 요청된 기능?
- [ ] 가장 많은 불만?

### 5. 전환 병목
- [ ] 랜딩 → docs 이탈률?
- [ ] docs → 설치 이탈률?
- [ ] 설치 → 활성 사용 전환율?

### 6. B2B 요구
- [ ] 팀들은 "정책"을 원하나 "로그/감사"를 원하나?
- [ ] Enterprise 문의 패턴?
- [ ] 가격 저항점?

### 7. 평가 필요성
- [ ] 정책 변경이 실제로 품질을 올렸는지 증명 가능?
- [ ] Eval Harness 우선순위 조정 필요?

---

## 분기 피벗 규칙

| 신호 | 대응 |
|------|------|
| 설치/온보딩 이탈이 크다 | 단기(제품화) 작업으로 회귀 |
| 팀이 들어오기 시작했다 | 정책 엔진 강화(중기 가속) |
| 보안/사고 얘기가 늘었다 | Safety Layer 우선순위 상승 |
| "정책이 효과 있냐" 질문이 늘었다 | Eval Harness 우선순위 상승 |
| 규제/감사 문의 증가 | Compliance Pack 우선순위 상승 |

---

## 기존 백로그 통합

### Phase 2: 웹훅 환불 감지 (기존)

**상태**: 계획됨 → 단기 백로그로 이관

| 기능 | 상태 |
|------|------|
| Cloudflare Workers 설정 | 📋 계획 |
| KV 네임스페이스 생성 | 📋 계획 |
| 웹훅 핸들러 구현 | 📋 계획 |
| Discord 알림 | 📋 계획 |
| clouvel-pro 검증 수정 | 📋 계획 |

### Phase 3: 대시보드 (기존)

**상태**: 대기 → 중기 백로그로 통합

| 기능 | 통합 대상 |
|------|----------|
| 라이선스 목록 | B2B 대시보드 |
| 사용 통계 | Eval Harness 메트릭 |
| 환불 내역 | Evidence Pack |
| 고객 관리 | Compliance Pack |

---

## 거절된 아이디어

| 아이디어 | 거절 이유 |
|----------|-----------|
| 무료 체험 | 평생 라이선스라 체험 불필요 |
| 구독 모델 | 사용자 선호도 낮음 |
| 모바일 앱 | 개발 환경에서 사용, 불필요 |
| 암호화폐 결제 | 복잡성 대비 수요 낮음 |
| 실시간 협업 | 범위 초과, 정책 엔진에 집중 |

---

## 버전별 백로그 할당

### v1.1.0 (단기)
- [ ] B1. Works-with 배지 시스템
- [ ] B2. Quickstart 60초
- [ ] B3. BLOCK/PASS 통일 데모
- [ ] 웹훅 환불 감지 (기존 Phase 2)

### v1.2.0 (단기)
- [ ] B4. 가벼운 품질 게이트 추가
- [ ] CLI 개선 (컬러 출력, 프로그레스바)

### v2.0.0 (중기)
- [ ] B5. clouvel.policy.yml 도입
- [ ] B6. 표준 JSON 출력 포맷
- [ ] B7. 예외 승인 플로우

### v2.1.0 (중기)
- [ ] B8. Evidence Pack v1
- [ ] 팀 정책 공유 기능

### v3.0.0 (장기)
- [ ] B9. Safety Layer
- [ ] B10. Eval Harness
- [ ] B11. Compliance Pack

---

## 한 줄 요약

| 단계 | 핵심 |
|------|------|
| 단기 | 설치/이해/전환 |
| 중기 | 정책 엔진 + Evidence Pack |
| 장기 | Safety + Evals + Compliance |

**3개월마다 "클라이언트 변화/안전 사고/표준(MCP)/평가 요구"만 점검하면, AI가 바뀌어도 Clouvel은 계속 살아남는다.**

---

## 문서 히스토리

| 날짜 | 변경 |
|------|------|
| 2026-01-17 | 전략적 백로그 v2.0 - AI 트렌드 기반 재설계 |
