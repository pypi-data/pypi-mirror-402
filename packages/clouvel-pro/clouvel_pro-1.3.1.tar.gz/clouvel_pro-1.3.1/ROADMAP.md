# Clouvel Pro 로드맵

> Shovel 워크플로우 + 프리미엄 기능 개발 로드맵

---

## 현재 버전

- **버전**: v1.0.0
- **상태**: Phase 1 완료, Phase 2 진행 예정
- **PyPI**: [clouvel-pro](https://pypi.org/project/clouvel-pro/)

---

## Shovel 워크플로우

```
/start → /plan → /implement → /gate → /commit
```

| 커맨드 | 설명 | 자동화 |
|--------|------|--------|
| /start | 프로젝트 온보딩 (7 Theories) | install_shovel |
| /plan | 계획 수립 (Tree of Thoughts) | - |
| /implement | 구현 실행 | - |
| /gate | lint → test → build → audit | gate 도구 |
| /verify | Context Bias 검증 | verify 도구 |
| /commit | Gate PASS 후 커밋 | - |
| /learn-error | 에러 패턴 학습 | Error Learning |

---

## Phase 개요

| Phase | 내용 | 상태 | 버전 |
|-------|------|------|------|
| Phase 1 | 코어 기능 | ✅ 완료 | v1.0.0 |
| Phase 2 | 웹훅 환불 감지 | 📋 계획됨 | v1.1.0 |
| Phase 3 | 대시보드 | ⏳ 대기 | v2.0.0 |
| Phase 4 | Error Learning 고도화 | 💡 아이디어 | v2.1.0 |
| Phase 5 | 팀 기능 | 💡 아이디어 | v3.0.0 |

---

## Phase 1: 코어 기능 ✅

**상태**: 완료

| 기능 | 설명 | 상태 |
|------|------|------|
| Shovel 자동 설치 | .claude/ 구조 원클릭 설치 | ✅ |
| Error Learning | 에러 패턴 분석 + 방지 규칙 | ✅ |
| 커맨드 동기화 | Shovel 업데이트 동기화 | ✅ |
| Lemon Squeezy 연동 | 온라인 라이선스 검증 | ✅ |

---

## Phase 2: 웹훅 환불 감지 📋

**상태**: 계획됨
**예상 시간**: 1시간 35분
**비용**: $0 (Cloudflare Free)

### 목표

환불 시 라이선스 즉시 무효화

### 아키텍처

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

### Step 목록

| Step | 내용 | 시간 |
|------|------|------|
| 2-1 | Cloudflare Workers 프로젝트 생성 | 15min |
| 2-2 | KV 네임스페이스 생성 | 5min |
| 2-3 | 웹훅 핸들러 구현 | 30min |
| 2-4 | 환경변수 설정 | 5min |
| 2-5 | 배포 | 5min |
| 2-6 | Lemon Squeezy 웹훅 등록 | 5min |
| 2-7 | clouvel-pro 검증 로직 수정 | 20min |
| 2-8 | 차단 확인 엔드포인트 추가 | 10min |

### 기술 스택

| 구성요소 | 선택 | 이유 |
|----------|------|------|
| 웹훅 서버 | Cloudflare Workers | 무료, 전역, 빠름 |
| 데이터 저장 | Cloudflare KV | Workers 통합 |
| 알림 | Discord Webhook | 무료, 실시간 |

### 검증 기준

- [ ] 테스트 환불 시 라이선스 차단 확인
- [ ] clouvel-pro에서 차단된 키로 접근 시 에러
- [ ] Discord 알림 수신 확인

---

## Phase 3: 대시보드 ⏳

**상태**: 대기
**선행**: Phase 2 완료

### 예정 기능

| 기능 | 설명 |
|------|------|
| 라이선스 관리 | 활성/비활성 라이선스 목록 |
| 사용 통계 | 도구별 사용량 |
| 환불 내역 | 환불된 라이선스 이력 |
| 고객 관리 | 고객 정보 조회 |

---

## 버전 히스토리

| 버전 | 날짜 | 변경사항 |
|------|------|----------|
| 1.0.0 | 2026-01-17 | 초기 릴리스 (Phase 1) |

---

## Phase 4: Error Learning 고도화 💡

**상태**: 아이디어
**선행**: Phase 3 완료

### 예정 기능

| 기능 | 설명 |
|------|------|
| AI 패턴 분석 | LLM으로 에러 패턴 자동 분류 |
| 에러 예방 알림 | 비슷한 코드 작성 시 실시간 경고 |
| 주간 리포트 | 에러 트렌드 자동 리포트 |
| Deep Debug 연동 | 3회 반복 에러 자동 분석 |

---

## Phase 5: 팀 기능 💡

**상태**: 아이디어
**선행**: Phase 4 완료

### 예정 기능

| 기능 | 설명 |
|------|------|
| 팀 라이선스 관리 | 멤버 초대/제거 |
| 팀 에러 공유 | 팀 내 에러 패턴 공유 |
| 팀 설정 동기화 | Shovel 설정 팀 공유 |
| 팀 대시보드 | 팀 전체 통계 |

---

## 7 Theories (Shovel 기반)

clouvel-pro가 구현하는 AI 개발 이론:

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
| [BACKLOG.md](docs/BACKLOG.md) | 미래 기능 백로그 |

---

## 다음 할 일

1. [ ] Phase 2 시작 (웹훅 환불 감지)
2. [ ] 14일 환불 정책 랜딩페이지에 명시
3. [ ] Phase 3 상세 계획 수립
4. [ ] clouvel v0.6.0~v0.8.0 자동 배포 모니터링
