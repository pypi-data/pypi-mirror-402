# Clouvel Pro PRD

> Shovel 워크플로우 + 프리미엄 기능

---

## 제품 개요

### 비전

AI 개발에서 **실수 반복을 제거**하고 **검증된 워크플로우**를 강제하는 도구

### 대상 사용자

- AI 기반 코딩 사용자 (Claude Code, Cursor, Copilot)
- 일관된 품질을 원하는 개인 개발자/팀
- Shovel 워크플로우 자동화가 필요한 사용자

### 핵심 가치

| 가치 | 설명 |
|------|------|
| 실수 방지 | 에러 패턴 학습 + 방지 규칙 |
| 강제 검증 | Gate PASS 없이 커밋 불가 |
| 원클릭 설치 | Shovel 구조 자동 생성 |

---

## 기능 요구사항

### Phase 1: 코어 기능 ✅

#### F1. Shovel 자동 설치

**목표**: .claude/ 구조 원클릭 설치

```python
install_shovel(path="./project")
```

**생성 구조**:
```
.claude/
├── commands/      # 슬래시 커맨드
│   ├── gate.md
│   ├── plan.md
│   ├── implement.md
│   ├── verify.md
│   ├── learn-error.md
│   └── ...
├── templates/     # 프로젝트 템플릿
├── evidence/      # Gate 결과 저장
├── logs/          # 에러 로그
├── plans/         # 계획 문서
└── settings.json  # 설정
```

**검증 기준**:
- [ ] 모든 커맨드 파일 생성 확인
- [ ] settings.json 기본값 설정
- [ ] 기존 파일 덮어쓰기 방지 (merge 옵션)

#### F2. Error Learning

**목표**: 에러 패턴 분석 + NEVER/ALWAYS 규칙 생성

```python
log_error(path=".", error_text="TypeError: ...")
analyze_error(path=".", include_history=True)
add_prevention_rule(path=".", error_type="type_error", rule="...")
get_error_summary(path=".", days=30)
```

**저장 형식** (ERROR_LOG.md):
```markdown
## Error #{number}

| 항목 | 값 |
|------|---|
| 날짜 | 2026-01-17 |
| 타입 | TypeError |
| 파일 | src/auth/login.ts:42 |
| 반복 | 3회 |

### 에러 메시지
{error_text}

### 근본 원인
{root_cause}

### 방지 규칙
NEVER: {never_rule}
ALWAYS: {always_rule}
```

**검증 기준**:
- [ ] 에러 로그 기록
- [ ] 패턴 분석 (3회 이상 반복 감지)
- [ ] NEVER/ALWAYS 규칙 생성
- [ ] CLAUDE.md 자동 업데이트

#### F3. 커맨드 동기화

**목표**: Shovel 업데이트 시 프로젝트 동기화

```python
sync_commands(path=".", mode="merge")
```

**모드**:
- `merge`: 기존 커스텀 유지 + 새 커맨드 추가
- `overwrite`: 전체 덮어쓰기

**검증 기준**:
- [ ] 새 커맨드 추가
- [ ] 기존 커스텀 보존 (merge)
- [ ] 버전 충돌 해결

#### F4. 온라인 라이선스 검증

**목표**: Lemon Squeezy API로 라이선스 검증

```python
activate_license(license_key="CLOUVEL-PERSONAL-XXXXX")
verify_license()
```

**검증 흐름**:
```
1. 온라인 검증 시도 (Lemon Squeezy API)
2. 성공 → 캐시 저장 (7일)
3. 실패 → 에러 반환
4. 네트워크 오류 → 캐시 폴백
```

**검증 기준**:
- [ ] 유효 키 활성화
- [ ] 무효 키 거부
- [ ] 오프라인 캐시 동작

---

### Phase 2: 웹훅 환불 감지 + 보안 시스템 ✅

#### F5. 환불 시 라이선스 즉시 무효화

**목표**: Lemon Squeezy 환불 웹훅 → KV 저장 → 검증 차단

**아키텍처**:
```
[Lemon Squeezy] ──order_refunded──> [Cloudflare Workers]
                                          │
                                   ┌──────┴──────┐
                                   ↓             ↓
                              [KV Store]   [Discord 알림]
                                   │
                                   ↓
                           [clouvel-pro 검증]
                                   │
                              revoked → 차단
```

**검증 기준**:
- [x] 테스트 환불 시 라이선스 차단
- [x] clouvel-pro에서 차단된 키 접근 시 에러
- [x] Discord 알림 수신

#### F5.1 Week 1-4 보안 시스템

| Week | 기능 | 상태 |
|------|------|------|
| Week 1 | 7일 잠금, 서버사이드 콘텐츠, Machine ID 바인딩 | ✅ |
| Week 2 | Rate Limiting, 브루트포스 방지, Heartbeat, Audit Log | ✅ |
| Week 3 | 이상 탐지, 동시 사용 제한, 오프라인 토큰 | ✅ |
| Week 4 | 실시간 알림, 라이선스 공유 탐지, 클라이언트 버전 검증, 자동 대응 | ✅ |

**문서**: [SECURITY.md](./SECURITY.md)

---

### Phase 3: 대시보드 ✅

#### F6. 라이선스 관리 UI

**URL**: https://clouvel-admin.pages.dev

| 기능 | 상태 |
|------|------|
| 활성/비활성 라이선스 목록 | ✅ |
| 사용 통계 (도구별) | ✅ |
| 환불 내역 | ✅ |
| 보안 이상 탐지 | ✅ |
| 차단/해제 관리 | ✅ |
| Audit Log | ✅ |

---

### Phase 4: Team 기능 ✅

**상태**: Server API 완료 | **완료일**: 2026-01-18

**목표**: 팀 단위 협업 + 지식 공유 시스템

#### F7. 팀 멤버 관리

**API 명세**:

| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/team/invite` | POST | 멤버 초대 (Admin만) |
| `/team/members` | GET | 멤버 목록 조회 |
| `/team/remove` | DELETE | 멤버 제거 (Admin/본인) |
| `/team/role` | PUT | 역할 변경 (Admin만) |

**데이터 구조**:
```
team:{license_key}
├── owner: "owner@email.com"     # 구매자 = Admin
├── members: [
│   { email, role, machine_id, joined_at }
│   ]
├── settings: {
│   enabled_roles: { cto, cdo, cpo, cfo, cmo }
│   }
└── max_seats: 10
```

**역할**:
- `admin`: 초대/제거/설정 변경 가능
- `member`: 기능 사용만 가능

**검증 기준**:
- [ ] 멤버 초대 (이메일 + 활성화 토큰)
- [ ] 10명 시트 제한 검증
- [ ] Admin만 초대/제거 가능
- [ ] 본인 탈퇴 가능

#### F8. C-Level 역할 토글

**목표**: 팀 성격에 맞게 필요한 역할만 활성화

```yaml
# 팀 설정 예시
team_settings:
  enabled_roles:
    cto: true    # 기술 검토 ✅
    cdo: false   # 디자인 검토 ❌
    cpo: true    # 제품 검토 ✅
    cfo: false   # 재무 검토 ❌
    cmo: true    # 마케팅 검토 ✅
```

**API**:
| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/team/settings` | GET | 팀 설정 조회 |
| `/team/settings` | PUT | 팀 설정 변경 (Admin) |

**검증 기준**:
- [ ] 역할 토글 저장/조회
- [ ] 비활성화된 역할은 /c-level에서 제외
- [ ] 기본값: 모든 역할 활성화

#### F9. 팀 에러 패턴 공유

**목표**: 팀원 A의 에러 → 팀 전체 NEVER/ALWAYS 규칙으로

**흐름**:
```
팀원 A: /error-log TypeError...
         ↓
    로컬 ERROR_LOG.md 기록
         ↓
    서버로 동기화 (team:{key}:errors)
         ↓
팀원 B, C: /sync-team-errors
         ↓
    팀 공통 규칙 다운로드
         ↓
    로컬 CLAUDE.md에 NEVER/ALWAYS 추가
```

**데이터 구조**:
```
team:{license_key}:errors
├── patterns: [
│   {
│     type: "TypeError",
│     signature: "Cannot read property...",
│     count: 5,
│     never: "undefined 체크 없이 접근",
│     always: "옵셔널 체이닝 사용",
│     created_by: "memberA@email.com",
│     created_at: "2026-01-18T..."
│   }
│   ]
└── last_sync: "2026-01-18T..."
```

**API**:
| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/team/errors/sync` | POST | 에러 패턴 업로드 |
| `/team/errors` | GET | 팀 에러 패턴 조회 |
| `/team/errors/rules` | GET | 팀 NEVER/ALWAYS 규칙 |

**검증 기준**:
- [ ] 에러 패턴 업로드
- [ ] 중복 패턴 병합 (count 증가)
- [ ] 팀원 간 규칙 동기화
- [ ] CLAUDE.md 자동 업데이트

#### F10. 시니어 리뷰 시스템

**목표**: 프로젝트 맥락을 아는 자동 리뷰

**핵심 요구사항**: "정확도가 높고 프로젝트 모든 정보를 알아야 함"

**아키텍처**:
```
프로젝트 컨텍스트 저장:
┌─────────────────────────────────────────┐
│ team:{key}:project:{project_id}         │
├─────────────────────────────────────────┤
│ ├── prd: "PRD.md 내용"                  │
│ ├── claude_md: "CLAUDE.md 내용"         │
│ ├── structure: "파일 구조"               │
│ ├── decisions: [                        │
│ │   { what, why, when, who }            │
│ │   ]                                   │
│ └── review_rules: [                     │
│     { rule, priority, created_by }      │
│     ]                                   │
└─────────────────────────────────────────┘
```

**시니어 리뷰 흐름**:
```
주니어: /review-request "로그인 기능 구현했습니다"
         ↓
    서버에서 프로젝트 컨텍스트 로드
         ↓
    시니어 리뷰 룰 + PRD + 히스토리 기반 검토
         ↓
    자동 리뷰 코멘트 생성
         ↓
시니어: 리뷰 결과 확인 + 승인/반려
```

**API**:
| 엔드포인트 | 메서드 | 설명 |
|------------|--------|------|
| `/team/project/sync` | POST | 프로젝트 컨텍스트 업로드 |
| `/team/project` | GET | 프로젝트 컨텍스트 조회 |
| `/team/review/rules` | GET/PUT | 리뷰 룰 관리 |
| `/team/review/request` | POST | 리뷰 요청 |

**검증 기준**:
- [ ] 프로젝트 컨텍스트 저장/조회
- [ ] 리뷰 룰 기반 자동 검토
- [ ] PRD 위반 감지
- [ ] 기존 결정사항과 충돌 감지

---

#### 아키텍처 변경

**현재 (Stateless)**:
```
Claude Code → Workers → 콘텐츠 반환
```

**Team 기능 (Stateful)**:
```
Claude Code → Workers → KV (팀 데이터)
                 ↓
         ┌──────┴──────┐
         │ 멤버 정보   │
         │ 에러 패턴   │
         │ 프로젝트    │
         │ 리뷰 룰     │
         └─────────────┘
```

**KV 네임스페이스**:
- `REVOKED_LICENSES`: 기존 (라이선스, 감사 로그)
- `TEAM_DATA`: 신규 (팀 멤버, 설정, 에러 패턴, 프로젝트)

---

## 비기능 요구사항

### 성능

| 항목 | 목표 |
|------|------|
| install_shovel | < 3초 |
| verify_license (온라인) | < 2초 |
| verify_license (캐시) | < 100ms |

### 보안

- 라이선스 키 해시 저장 (SHA-256)
- HTTPS 통신 필수
- 캐시 파일 암호화 (선택)

### 호환성

- Python 3.9+
- Windows / macOS / Linux
- Claude Code / Claude Desktop

---

## API 명세

### MCP Tools

| 도구 | 설명 | 라이선스 필요 |
|------|------|--------------|
| `activate_license` | 라이선스 활성화 | ❌ |
| `install_shovel` | Shovel 설치 | ✅ |
| `sync_commands` | 커맨드 동기화 | ✅ |
| `log_error` | 에러 기록 | ✅ |
| `analyze_error` | 에러 분석 | ✅ |
| `add_prevention_rule` | 방지 규칙 추가 | ✅ |
| `get_error_summary` | 에러 요약 | ✅ |

---

## 티어

| 티어 | 가격 | 인원 | 기능 |
|------|------|------|------|
| Personal | $29 | 1명 | 모든 Pro 기능 |
| Team | $79 | 10명 | + 팀 지식 공유 |
| Enterprise | $199 | 무제한 | + 커스텀 지원 |

### Personal ($29)
- Shovel 워크플로우 자동 설치
- C-Level 역할 시스템 (CTO, CDO, CPO, CFO, CMO)
- Error Learning (에러 패턴 학습)
- Gate 시스템 (lint → test → build)
- 7일 프리미엄 잠금 해제

### Team ($79) - 10명
**Personal 모든 기능 +**
- 멤버 관리 (초대/제거/역할)
- C-Level 역할 토글 (팀별 커스터마이징)
- **팀 에러 패턴 공유** (팀원 실수 → 전체 규칙)
- **시니어 리뷰 시스템** (프로젝트 맥락 기반 자동 리뷰)
- 프로젝트 컨텍스트 동기화

### Enterprise ($199) - 무제한
**Team 모든 기능 +**
- 무제한 시트
- 전용 지원 채널
- 커스텀 역할 정의
- SSO 연동 (예정)

---

## 성공 지표

| 지표 | 목표 |
|------|------|
| 활성 라이선스 | 100+ (3개월) |
| 환불률 | < 10% |
| NPS | > 50 |

---

## 버전 히스토리

| 버전 | 날짜 | 변경 |
|------|------|------|
| 1.0.0 | 2026-01-17 | PRD 초안 |
| 1.1.0 | 2026-01-17 | Phase 2 완료 (웹훅 + Week 1-4 보안) |
| 1.2.0 | 2026-01-17 | Phase 3 완료 (Admin Dashboard) |
