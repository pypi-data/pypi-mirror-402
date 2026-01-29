# Clouvel Pro Security System

> Week 1-4 보안 방어 체계 문서

---

## 개요

Clouvel Pro는 4주간의 보안 강화를 통해 다층 방어 체계를 구축했습니다.

```
Week 1: 기본 방어 (진입 차단)
Week 2: 탐지 (이상 감지)
Week 3: 고급 탐지 (심층 분석)
Week 4: 자동 대응 (즉각 조치)
```

---

## Week 1: 기본 방어

### 1.1 7일 잠금 (Premium Lock)

```
구매 후 7일간 프리미엄 기능 잠금
→ 환불 기간 내 콘텐츠 추출 방지
```

| 설정 | 값 |
|------|-----|
| 잠금 기간 | 7일 |
| 적용 대상 | 프리미엄 콘텐츠 전체 |

### 1.2 서버사이드 콘텐츠

```
템플릿/커맨드가 패키지에 없음
→ 서버에서 실시간 다운로드
→ 라이선스 검증 후에만 제공
```

### 1.3 Machine ID 바인딩

```
라이선스 + 머신 ID 연결
→ 다른 기기에서 무단 사용 방지
```

### 1.4 환불 즉시 차단

```
Lemon Squeezy 웹훅 수신
→ order_refunded 이벤트 감지
→ KV에 환불 라이선스 저장
→ 즉시 접근 차단
```

---

## Week 2: 탐지

### 2.1 Rate Limiting

```javascript
const RATE_LIMITS = {
  '/content/bundle': { requests: 10, windowSeconds: 60 },
  '/content/manifest': { requests: 20, windowSeconds: 60 },
  '/check': { requests: 30, windowSeconds: 60 },
  '/heartbeat': { requests: 5, windowSeconds: 60 },
  'default': { requests: 60, windowSeconds: 60 }
};
```

### 2.2 브루트포스 방지

```
50회 실패/분 → 1시간 IP 차단
```

### 2.3 Heartbeat 시스템

```
24시간마다 Heartbeat 전송
→ 3일 오프라인 유예 기간
→ 초과 시 라이선스 일시정지
```

### 2.4 Audit Logging

```javascript
const AUDIT_EVENT_TYPES = {
  AUTH_FAILURE: 'auth_failure',
  RATE_LIMITED: 'rate_limited',
  BRUTE_FORCE_BLOCKED: 'brute_force',
  REVOKED_ACCESS: 'revoked_access',
  REFUND_PROCESSED: 'refund_processed',
  ANOMALY_DETECTED: 'anomaly_detected'
};
```

---

## Week 3: 고급 탐지

### 3.1 이상 탐지 (Anomaly Detection)

```javascript
const ANOMALY_THRESHOLDS = {
  MAX_COUNTRIES_24H: 3,      // 24시간 내 다른 국가
  MAX_MACHINES_1H: 5,        // 1시간 내 다른 머신
  REQUEST_SPIKE_MULTIPLIER: 10,  // 요청 급증 배율
  NIGHT_ACCESS_RATIO: 0.7,   // 새벽 접속 비율
  SUSPICION_LEVEL_1: 30,     // 로그만
  SUSPICION_LEVEL_2: 60,     // Discord 알림
  SUSPICION_LEVEL_3: 90      // 자동 차단
};
```

### 3.2 동시 사용 제한

```javascript
const TIER_CONCURRENT_LIMITS = {
  personal: 1,    // 동시 1대
  team: 10,       // 동시 10대
  enterprise: -1  // 무제한
};
```

- 등록은 무제한
- 동시 사용만 제한
- 24시간 미사용 시 자동 비활성화

### 3.3 오프라인 토큰

```
HMAC-SHA256 서명된 토큰
→ 7일간 오프라인 사용 가능
→ 온라인 복귀 시 재검증
```

### 3.4 Admin Dashboard

| API | 용도 |
|-----|------|
| `/admin/dashboard` | 전체 통계 |
| `/admin/block` | 수동 차단 |
| `/admin/unblock` | 차단 해제 |

---

## Week 4: 자동 대응

### 4.1 실시간 알림 (Discord)

```javascript
const ALERT_CONFIG = {
  brute_force: { title: '🚨 브루트포스 공격', color: 0xFF0000, priority: 'critical' },
  anomaly_level_3: { title: '🔴 심각한 이상 징후', color: 0xFF0000, priority: 'critical' },
  anomaly_level_2: { title: '🟠 이상 징후 경고', color: 0xFF6600, priority: 'high' },
  license_sharing: { title: '👥 라이선스 공유 의심', color: 0xFF6600, priority: 'high' },
  daily_report: { title: '📊 일일 보안 리포트', color: 0x10B981, priority: 'info' }
};
```

### 4.2 라이선스 공유 탐지

```
탐지 기준:
- 24시간 내 5개 이상 고유 IP → +40점
- 24시간 내 3개 이상 국가 → +50점
- 동시 활성 세션 3개 이상 → +30점

50점 이상 → 공유 의심
```

### 4.3 클라이언트 버전 검증

```javascript
const CLIENT_VERSION_CONFIG = {
  MIN_SUPPORTED_VERSION: '1.0.0',  // 미만 차단
  RECOMMENDED_VERSION: '1.2.0',    // 미만 경고
  LATEST_VERSION: '1.2.0',
  BLOCKED_VERSIONS: ['0.9.0', '0.9.1']  // 보안 취약점
};
```

### 4.4 자동 대응 시스템

```
반복 위반에 따른 차단 시간:
- 1회: 1시간
- 2회: 2시간
- 3회: 6시간
- 5회+: 24시간

7일 후 위반 카운트 리셋
```

---

## API 엔드포인트 목록

### 공개 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/health` | 서버 상태 |
| POST | `/webhook` | Lemon Squeezy 웹훅 |
| POST | `/check` | 라이선스 검증 |
| POST | `/content/bundle` | 콘텐츠 다운로드 |
| GET | `/content/manifest` | 콘텐츠 목록 |
| POST | `/heartbeat` | Heartbeat |
| GET | `/version/check` | 버전 검증 |
| GET | `/stats/rate-limits` | Rate Limit 상태 |

### 인증 필요 API

| Method | Endpoint | 설명 |
|--------|----------|------|
| POST | `/license/status` | 라이선스 상태 |
| POST | `/license/machines` | 머신 목록 |
| POST | `/license/deactivate-machine` | 머신 비활성화 |
| POST | `/token/issue` | 오프라인 토큰 발급 |
| POST | `/token/verify` | 토큰 검증 |

### Admin API (API Key 필요)

| Method | Endpoint | 설명 |
|--------|----------|------|
| GET | `/admin/dashboard` | 관리자 대시보드 |
| POST | `/admin/block` | 수동 차단 |
| POST | `/admin/unblock` | 차단 해제 |
| GET | `/admin/daily-report` | 일일 리포트 |
| POST | `/admin/check-sharing` | 공유 탐지 |
| GET | `/stats/audit` | 감사 로그 |
| GET | `/stats/anomaly` | 이상 탐지 통계 |
| POST | `/analyze/license` | 라이선스 분석 |

---

## 환경 변수

| 변수 | 설명 |
|------|------|
| `LEMON_SQUEEZY_WEBHOOK_SECRET` | 웹훅 서명 검증 |
| `LEMON_SQUEEZY_API_KEY` | API 호출용 |
| `ADMIN_API_KEY` | Admin API 인증 |
| `TOKEN_SECRET` | 오프라인 토큰 서명 |
| `DISCORD_WEBHOOK_URL` | 알림 전송 |

---

## 보안 흐름도

```
┌─────────────────────────────────────────────────────────────┐
│                        요청 수신                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 2] Rate Limit 체크                                     │
│ 초과 → 429 반환 + 감사 로그                                   │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 2] 브루트포스 체크                                      │
│ 50회/분 초과 → IP 1시간 차단                                  │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 1] 환불 라이선스 체크                                   │
│ 환불됨 → 403 반환                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 3] 일시정지 상태 체크                                   │
│ 정지됨 → 403 반환                                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 4] 클라이언트 버전 체크                                 │
│ 차단 버전 → 403 반환                                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 1] Lemon Squeezy 라이선스 검증                         │
│ 무효 → 403 반환                                              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 3] 이상 탐지 분석                                       │
│ Level 1: 로그 | Level 2: 알림 | Level 3: 차단                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 3] 동시 사용 제한 체크                                  │
│ 초과 → 403 반환 (24시간 후 자동 해제)                         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│ [Week 1] 7일 잠금 체크                                        │
│ 7일 미만 → 403 반환                                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                     ✅ 콘텐츠 제공                            │
└─────────────────────────────────────────────────────────────┘
```

---

## 문의 처리 프로세스

```
사용자 문의 (PC 교체 등)
        │
        ▼
랜딩페이지 문의 폼
        │
        ▼
Discord Webhook 알림
        │
        ▼
Lemon Squeezy에서 이메일로 라이선스 확인
        │
        ▼
Admin API로 조치 (/admin/unblock 등)
        │
        ▼
사용자에게 완료 안내
```

---

## 버전 히스토리

| 버전 | 날짜 | 내용 |
|------|------|------|
| 1.0.0 | 2026-01-10 | Week 1 - 기본 방어 |
| 1.1.0 | 2026-01-12 | Week 2 - 탐지 시스템 |
| 1.2.0 | 2026-01-15 | Week 3 - 고급 탐지 |
| 2.0.0 | 2026-01-17 | Week 4 - 자동 대응 |

---

## 참고

- 서버: Cloudflare Workers
- 스토리지: Cloudflare KV
- 결제: Lemon Squeezy
- 알림: Discord Webhook
