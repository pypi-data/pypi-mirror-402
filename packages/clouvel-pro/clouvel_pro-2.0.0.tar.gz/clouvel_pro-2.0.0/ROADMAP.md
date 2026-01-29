# Clouvel 로드맵

> AI 에이전트 시대의 정책 엔진으로 진화

---

## 현재 버전

- **버전**: v1.0.0
- **상태**: Phase 1 완료, 전략적 로드맵 재설계
- **PyPI**: [clouvel-pro](https://pypi.org/project/clouvel-pro/)

---

## AI 트렌드 (2026~)

| 변화 | Clouvel 대응 |
|------|-------------|
| IDE 보조 → 레포 변경 에이전트 | "왜 바꿨는지" 기록이 핵심 가치 |
| 단일 → 멀티 에이전트 | 공통 정책 통과 게이트 필요 |
| MCP 표준 확산 | 정책 MCP 서버로 확장 가능 |
| Evals 필수화 | 정책이 품질을 올리는지 증명 필요 |
| 규제/거버넌스 구매 조건화 | Evidence Pack = B2B 결제 버튼 |

---

## 로드맵 개요

```
┌─────────────────────────────────────────────────────────────────┐
│  단기 (0~3개월)        │  중기 (3~9개월)      │  장기 (9~18개월)  │
│  ─────────────         │  ─────────────       │  ──────────────   │
│  설치/이해/전환        │  정책 엔진           │  B2B 방어선       │
│                        │  + Evidence Pack     │  + Safety/Evals   │
└─────────────────────────────────────────────────────────────────┘
```

| 단계 | 핵심 목표 | 버전 |
|------|----------|------|
| 단기 | 60초 설치 + 3초 이해 | v1.1~v1.2 |
| 중기 | 팀별 정책 + 감사 기록 | v2.0~v2.1 |
| 장기 | 안전 + 평가 + 규제 대응 | v3.0 |

---

## 단기 (0~3개월): 제품화 + 전환

> **목표**: 설치 60초 + 데모 1장 + "어디서 되나" 3초 이해

### v1.1.0 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| Works-with 배지 | CLI/Desktop/VS Code/Cursor 호환성 표시 | 📋 계획 |
| Quickstart 60초 | 설치 → 활성화 → BLOCK 확인 한 줄로 | 📋 계획 |
| BLOCK/PASS 데모 통일 | 모든 마케팅/문서에서 동일 이미지 | 📋 계획 |
| 웹훅 환불 감지 | Cloudflare Workers + KV 기반 | 📋 계획 |

### v1.2.0 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| 품질 게이트 확장 | ARCH.md WARN, acceptance BLOCK | 📋 계획 |
| CLI 개선 | 컬러 출력, 프로그레스바 | 📋 계획 |

### 단기 성공 지표

| 지표 | 목표 |
|------|------|
| 설치 완료율 | 70%+ |
| BLOCK/PASS 이해 시간 | 3초 이내 |
| 랜딩 → 설치 전환율 | 20%+ |

---

## 중기 (3~9개월): 정책 엔진

> **목표**: "PRD 있냐 없냐"가 아니라 팀/프로젝트별 개발 규칙을 굴리는 엔진

### v2.0.0 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| clouvel.policy.yml | 선언적 정책 파일로 팀별 규칙 정의 | 💡 설계 |
| 표준 JSON 출력 | 모든 클라이언트에서 동일 결과 포맷 | 💡 설계 |
| 예외 승인 플로우 | 예외 사유/기간/승인자 로그 기록 | 💡 설계 |

**clouvel.policy.yml 예시**:
```yaml
version: "1.0"
name: "my-team-policy"

require_docs:
  - PRD.md
  - ARCH.md

require_sections:
  PRD.md: [scope, non_goals, acceptance]

quality_gates:
  min_tests: 8

block_on: [missing_healthz, no_acceptance_criteria]
warn_on: [no_arch_doc, low_test_count]
```

### v2.1.0 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| Evidence Pack v1 | 검증 결과 자동 기록 패키지 | 💡 설계 |
| 팀 정책 공유 | 팀 내 policy.yml 동기화 | 💡 아이디어 |

**Evidence Pack 구조**:
```
.clouvel/evidence/
├── 2026-01-17_12-00-00/
│   ├── result.json          # 검증 결과
│   ├── policy.yml           # 적용된 정책
│   ├── input_hashes.json    # 입력 파일 해시
│   └── change_summary.md    # 변경 요약
```

### 중기 성공 지표

| 지표 | 목표 |
|------|------|
| policy.yml 커밋 팀 | 10+ |
| 예외 승인 추적률 | 100% |
| Evidence Pack 생성률 | 95%+ |

---

## 장기 (9~18개월): B2B급 방어선

> **목표**: 에이전트가 더 강해져도 Clouvel이 필수 인프라로 남기

### v3.0.0 주요 기능

| 기능 | 설명 | 상태 |
|------|------|------|
| Safety Layer | 에이전트 위험 행동 분류 및 차단 | 💡 아이디어 |
| Eval Harness | 정책 효과 증명 (회귀 테스트) | 💡 아이디어 |
| Compliance Pack | 규제/감사 대응 문서 자동 생성 | 💡 아이디어 |

**Safety Layer 위험 분류**:
| 레벨 | 행동 | 기본 동작 |
|------|------|----------|
| CRITICAL | 대량 삭제 (10+) | BLOCK + 알림 |
| CRITICAL | 시크릿 접근 | Human 확인 |
| HIGH | 대규모 리팩터링 | WARN + 로그 |

### 장기 성공 지표

| 지표 | 목표 |
|------|------|
| "필수 인프라" 팀 | 5+ |
| 감사 문서 응답률 | 90%+ |
| Safety 오탐률 | 5% 이하 |

---

## 분기 점검 (매 3개월)

> 60분, 7가지 체크

| 영역 | 점검 항목 |
|------|----------|
| 클라이언트 변화 | Cursor/Desktop/VS Code 툴 실행 방식 변경? |
| 에이전트 위험 | 파일 삭제/인젝션 사고 증가? |
| 표준 변화 | MCP 스펙/권장 패턴 변경? |
| 사용자 피드백 | "막히는 지점"이 설치? 정책? 증거? |
| 전환 병목 | 랜딩 → docs → 설치 중 어디서 이탈? |
| B2B 요구 | 정책 원함? 로그/감사 원함? |
| 평가 필요성 | 정책 변경이 품질 개선 증명 가능? |

### 피벗 규칙

| 신호 | 대응 |
|------|------|
| 설치/온보딩 이탈 ↑ | 단기(제품화) 회귀 |
| 팀 유입 ↑ | 중기(정책 엔진) 가속 |
| 보안 사고 ↑ | Safety Layer 우선 |
| "효과 있냐" 질문 ↑ | Eval Harness 우선 |
| 규제 문의 ↑ | Compliance Pack 우선 |

---

## Shovel 워크플로우 (기존)

```
/start → /plan → /implement → /gate → /commit
```

| 커맨드 | 설명 | 자동화 |
|--------|------|--------|
| /start | 프로젝트 온보딩 | install_shovel |
| /plan | 계획 수립 | - |
| /implement | 구현 실행 | - |
| /gate | lint → test → build → audit | gate 도구 |
| /verify | Context Bias 검증 | verify 도구 |
| /commit | Gate PASS 후 커밋 | - |
| /learn-error | 에러 패턴 학습 | Error Learning |

---

## 완료된 Phase

### Phase 1: 코어 기능 ✅

| 기능 | 상태 |
|------|------|
| Shovel 자동 설치 | ✅ 완료 |
| Error Learning | ✅ 완료 |
| 커맨드 동기화 | ✅ 완료 |
| Lemon Squeezy 연동 | ✅ 완료 |

---

## 7 Theories (Shovel 기반)

| 이론 | 설명 | 적용 |
|------|------|------|
| Tree of Thoughts | 여러 경로 탐색 | /plan |
| Self-Consistency | 여러 답변 비교 | /verify |
| Chain of Verification | 단계별 검증 | /gate |
| LLM-as-Judge | AI가 AI 평가 | /review |
| ReAct | 행동+추론 결합 | /implement |
| Reflexion | 자기 반성 | /learn-error |
| DeepSeek-R1 | 긴 추론 체인 | /deep-debug |

---

## 관련 문서

| 문서 | 설명 |
|------|------|
| [PRD.md](docs/PRD.md) | 제품 요구사항 |
| [CHECKLIST.md](docs/CHECKLIST.md) | 릴리스/검증 체크리스트 |
| [BACKLOG.md](docs/BACKLOG.md) | 전략적 백로그 (RICE 스코어 포함) |

---

## 다음 할 일

1. [ ] v1.1.0 단기 기능 착수
   - [ ] Works-with 배지 디자인
   - [ ] Quickstart 60초 문서
   - [ ] BLOCK/PASS 스크린샷 통일
2. [ ] 웹훅 환불 감지 구현 (기존 Phase 2)
3. [ ] 분기 점검 캘린더 설정

---

## 버전 히스토리

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| 1.0.0 | 2026-01-17 | 초기 릴리스 (Phase 1) |

---

## 한 줄 결론

**단기**: 설치/이해/전환 → **중기**: 정책 엔진 + Evidence Pack → **장기**: Safety + Evals + Compliance

3개월마다 점검하면, AI가 바뀌어도 Clouvel은 계속 살아남는다.
