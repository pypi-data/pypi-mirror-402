/**
 * Clouvel License & Content Server
 *
 * 1. Lemon Squeezy 웹훅 수신 → 환불 감지 → KV에 저장
 * 2. 콘텐츠 API → 라이선스 + 7일 검증 후 템플릿/커맨드 제공
 */

// ============================================================
// 프리미엄 콘텐츠 (서버사이드 저장)
// ============================================================

const PREMIUM_CONTENT = {
  version: "1.0.0",
  updated_at: "2026-01-17",

  // CLAUDE.md 메인 파일
  claude_md: `# Shovel Development System v8

> 이 파일은 템플릿입니다. \`/start\` 실행 시 프로젝트에 맞게 자동 생성됩니다.

---

## 🏛️ 한 줄 헌법

> **PRD가 법이다. Gate PASS만이 진실이다. 좋은 제품 50% + 좋은 비즈니스 50%.**

---

## Shovel 워크플로우

\`\`\`
/start              # 프로젝트 온보딩 (1회)
    ↓
/plan [태스크]      # 계획 수립 (PRD 확인)
    ↓
사용자 확인         # 계획 승인
    ↓
/implement          # 구현 실행
    ↓
/gate               # Gate 검증 (lint→test→build)
    ↓
EVIDENCE.md 생성    # 통과 증거
    ↓
/commit
\`\`\`

## ⚠️ CRITICAL RULES

### 🚫 NEVER (절대 금지)

\`\`\`
NEVER "됐다", "완료", "성공" 선언 without Gate PASS
NEVER 스펙 밖 확장 (PRD 외 기능은 즉시 BACKLOG)
NEVER 테스트 없이 기능 완료 선언
NEVER 증거 없는 "통과" 주장
\`\`\`

### ✅ ALWAYS (필수 수행)

\`\`\`
ALWAYS Gate PASS로만 완료 정의 (lint→test→build)
ALWAYS EVIDENCE.md 생성 (gate 통과 증거)
ALWAYS PRD를 SSOT로 고정
ALWAYS 실행 가능한 단계별 명령으로 지시
\`\`\`

---

## 🎯 Gate 시스템

### 완료의 유일한 정의

\`\`\`bash
pnpm gate  # 또는 bash scripts/gate.sh
# lint ✅ + test ✅ + build ✅
# = EVIDENCE.md 자동 생성
# = 이것만이 "완료"
\`\`\`

---

## 커맨드 목록

| 커맨드 | 설명 |
|--------|------|
| \`/start\` | 프로젝트 온보딩 |
| \`/plan\` | 태스크 계획 수립 |
| \`/implement\` | 계획 실행 |
| \`/gate\` | **Gate 전체 실행** ⭐ |
| \`/verify\` | 개별 검증 |
| \`/commit\` | Gate PASS 후 커밋 |
| \`/review\` | 코드 리뷰 |

---

**📚 상세 사용법**: Clouvel Pro 문서 참고
`,

  // 커맨드 파일들
  commands: {
    "gate.md": `# /gate - Gate 검증 (Shovel 핵심)

> lint → test → build 순차 실행, 하나라도 실패하면 중단

## 실행

\`\`\`bash
pnpm gate
# 또는
bash scripts/gate.sh
\`\`\`

## 단계

| 순서 | 단계 | 실패 시 |
|------|------|---------|
| 1 | \`pnpm lint\` | 즉시 중단 |
| 2 | \`pnpm test\` | 즉시 중단 |
| 3 | \`pnpm build\` | 즉시 중단 |

## 성공 시

EVIDENCE.md 자동 생성:
\`\`\`markdown
# Gate Evidence

- **Status**: PASS ✅
- **Generated**: {timestamp}
- **Lint**: PASS
- **Test**: PASS
- **Build**: PASS
\`\`\`

## 실패 시

\`\`\`markdown
# Gate Evidence

- **Status**: FAIL ❌
- **Failed Step**: {step}
- **Error**: {error_message}
\`\`\`
`,

    "plan.md": `# /plan - 계획 수립 (Shovel v2)

> PRD 기반 태스크 계획 수립

## 사용법

\`\`\`
/plan 로그인 기능 구현
/plan DB 스키마 설계
\`\`\`

## 프로세스

1. PRD.md 확인
2. 관련 섹션 추출
3. 단계별 계획 작성
4. 사용자 승인 대기

## 계획 형식

\`\`\`markdown
## 계획: {태스크명}

### 단계
1. [ ] Step 1
2. [ ] Step 2
3. [ ] Step 3

### 수정 파일
- src/auth/login.ts
- src/auth/types.ts

### 검증
- \`pnpm test\`
- \`pnpm lint\`
\`\`\`
`,

    "implement.md": `# /implement - 구현 실행

> 승인된 계획 기반 구현

## 전제조건

- /plan으로 계획 수립됨
- 사용자 승인 완료

## 프로세스

1. PLAN.md 로드
2. 단계별 구현
3. 각 단계 완료 시 체크
4. 전체 완료 후 /gate 안내
`,

    "commit.md": `# /commit - 커밋 (Gate PASS 필수)

> Gate PASS 확인 후 커밋

## 사전 조건

EVIDENCE.md 확인:
- 존재 여부
- 최신 여부 (오늘 날짜)
- PASS 상태

## 커밋 메시지 형식

\`\`\`
<type>(<scope>): <description>

[optional body]

Gate: PASS ({timestamp})
\`\`\`

### Type
| Type | 설명 |
|------|------|
| feat | 새 기능 |
| fix | 버그 수정 |
| refactor | 리팩토링 |
| test | 테스트 |
| docs | 문서 |
`,

    "start.md": `# /start - 프로젝트 온보딩

> 새 프로젝트 Shovel 설정

## 프로세스

1. 프로젝트 분석
2. PRD 존재 확인
3. .claude/ 구조 확인
4. Gate 스크립트 확인

## 생성 파일

\`\`\`
.claude/
├── commands/
├── templates/
├── evidence/
├── logs/
└── plans/
\`\`\`
`,

    "verify.md": `# /verify - 검증 (Shovel + Boris)

> Context Bias 제거 후 검증

## 프로세스

1. 이전 작업 내용 확인
2. 코드 리뷰
3. 테스트 확인
4. Gate 실행 권장

## 체크리스트

- [ ] 구현이 계획과 일치?
- [ ] 테스트 통과?
- [ ] 린트 통과?
- [ ] 빌드 통과?
`,

    "review.md": `# /review - 코드 리뷰

> 구현 코드 리뷰 + 학습 기록

## 프로세스

1. 변경 파일 확인
2. 코드 품질 체크
3. 개선점 제안
4. 학습 포인트 기록
`,

    "error-log.md": `# /error-log - 에러 학습

> 에러 기록 및 분석

## 사용법

\`\`\`
/error-log TypeError: Cannot read property
\`\`\`

## 기록 내용

- 에러 타입
- 발생 위치
- 해결 방법
- 예방책
`,

    "learn-error.md": `# /learn-error - 에러 학습 자동화

> 쌓인 에러 패턴 분석 → CLAUDE.md 규칙화

## 프로세스

1. ERROR_LOG.md 분석
2. 반복 패턴 추출
3. NEVER/ALWAYS 규칙 생성
4. CLAUDE.md 업데이트 제안
`,

    "deep-debug.md": `# /deep-debug - 반복 에러 근본 원인 분석

> 3회 이상 반복 에러 시 자동 트리거

## 프로세스

1. 에러 히스토리 분석
2. 근본 원인 탐색 (5 Whys)
3. 구조적 해결책 제안
4. 테스트 케이스 추가
`,

    "verify-server.md": `# /verify-server - 서버 로직 검증

> 서버 코드, 환경변수, API 검증

## 체크리스트

- [ ] 환경변수 설정됨?
- [ ] API 라우트 정상?
- [ ] 외부 의존성 연결?
- [ ] 에러 핸들링?
`,

    "ssot-check.md": `# /ssot-check - SSOT 검사

> Single Source of Truth 위반 검사

## 검사 항목

- 중복 정의 없음?
- PRD가 유일한 스펙?
- 설정 파일 일관성?
`,

    "handoff.md": `# /handoff - Step 완료 시 의도 기록

> Context Bias 제거 검증 준비

## 기록 내용

- 이번 Step에서 한 일
- 왜 이렇게 했는지
- 주의할 점
- 다음 Step 안내
`,

    "check-complete.md": `# /check-complete - 껍데기/미연결 코드 검사

> 진짜 완료인지 확인

## 체크리스트

### 껍데기 검사
- [ ] TODO, placeholder 없음?
- [ ] 하드코딩 더미 데이터 없음?
- [ ] console.log만 있는 함수 없음?

### 연결 검사
- [ ] import/export 체인 완성?
- [ ] 라우팅 연결됨?
- [ ] UI에서 호출됨?
- [ ] DB/API 연결됨?

### 동작 검사
- [ ] 앱 실행 시 기능 보임?
- [ ] 버튼 누르면 동작?
- [ ] E2E 플로우 완성?
`,

    "c-level.md": `# /c-level - C-Level 역할 협업 시스템

> 5개 역할이 유기적으로 협업하여 다중 관점 제공

## 역할

| 역할 | 관점 | 핵심 질문 | 성격 |
|------|------|-----------|------|
| 🔧 **CTO** | 기술 | "확장 가능? 보안은?" | 신중한 엔지니어 |
| 🎨 **CDO** | 디자인/UX | "사용자가 이해하나?" | 완벽주의자 |
| 📊 **CPO** | 제품 | "고객 문제 해결하나?" | 데이터 기반 |
| 💰 **CFO** | 재무 | "얼마 벌 수 있나?" | 현실주의 |
| 📢 **CMO** | 마케팅 | "한 문장으로 설명?" | 스토리텔러 |

## 자동 리드 감지

질문의 키워드를 분석하여 자동으로 적합한 역할이 리드합니다.

| 키워드 | 리드 |
|--------|------|
| DB, API, 서버, 보안 | 🔧 CTO |
| UI, UX, 디자인 | 🎨 CDO |
| 기능, 우선순위, MVP | 📊 CPO |
| 가격, 비용, ROI | 💰 CFO |
| 마케팅, GTM, 브랜드 | 📢 CMO |

## 사용법

\`\`\`bash
# 자동 모드 (키워드 감지)
"DB 어떻게 설계할까?"  → CTO 리드

# 특정 역할 지정
/cto 이 아키텍처 검토해줘
/cdo 이 UI 피드백 줘
/cpo 이 기능 우선순위 어때?
/cfo 이 가격 정책 괜찮아?
/cmo 이거 어떻게 홍보할까?
\`\`\`

## 응답 형식

### 1. 리드 의견 (상세)
- 핵심 관점
- 상세 분석
- 권장안
- 체크리스트
- 리스크

### 2. 나머지 역할 의견 (간략)
- 각 역할별 1-3줄 코멘트

### 3. 종합 결론
- 리드 권고
- 각 역할 반영 사항
- 다음 단계

## 설정

모든 역할 설정은 \`config/roles.yaml\`에서 관리:
- 키워드 추가/삭제
- 역할 성격 변경
- 체크리스트 수정
- 새 역할 추가

**핵심**: "단일 관점 = 아마추어, 다중 관점 = 프로"
`
  },

  // 설정 파일
  settings: {
    "settings.json": JSON.stringify({
      "version": "1.0.0",
      "gate": {
        "lint": "pnpm lint",
        "test": "pnpm test",
        "build": "pnpm build"
      }
    }, null, 2)
  },

  // 템플릿
  templates: {
    "PRD.template.md": `# PRD: {프로젝트명}

## 개요
{한 줄 설명}

## 목표
- 목표 1
- 목표 2

## 기능 요구사항
### 필수 (MVP)
- [ ] 기능 1
- [ ] 기능 2

### 선택 (Phase 2)
- [ ] 기능 3

## 비기능 요구사항
- 성능:
- 보안:

## 제약사항
-
`,

    "web.claude.md": `# {프로젝트명}

> 웹 프로젝트

## 기술 스택
- Framework:
- Styling:
- State:

## 구조
\`\`\`
src/
├── components/
├── pages/
├── hooks/
└── utils/
\`\`\`

## 커맨드
\`\`\`bash
pnpm dev      # 개발 서버
pnpm build    # 빌드
pnpm test     # 테스트
pnpm lint     # 린트
\`\`\`
`
  },

  // 역할 설정 (C-Level)
  config: {
    "roles.yaml": `# C-Level 역할 정의 (SSOT)
roles:
  cto:
    name: "CTO"
    emoji: "🔧"
    persona:
      experience: "20년차"
      style: "신중한 엔지니어"
      catchphrase: "될 것 같은데 리스크 먼저 봅시다"
    keywords: ["DB", "API", "서버", "보안", "인프라", "스케일", "아키텍처"]
    priority: 1

  cdo:
    name: "CDO"
    emoji: "🎨"
    persona:
      experience: "20년차"
      style: "사용자 중심 디자이너"
      catchphrase: "사용자가 어떻게 느낄지 생각해봅시다"
    keywords: ["UI", "UX", "디자인", "사용성", "접근성", "인터페이스"]
    priority: 2

  cpo:
    name: "CPO"
    emoji: "📊"
    persona:
      experience: "20년차"
      style: "데이터 기반 PM"
      catchphrase: "고객 가치로 측정합시다"
    keywords: ["기능", "우선순위", "로드맵", "MVP", "요구사항", "스펙"]
    priority: 3

  cfo:
    name: "CFO"
    emoji: "💰"
    persona:
      experience: "20년차"
      style: "숫자로 말하는 전략가"
      catchphrase: "ROI 먼저 계산해봅시다"
    keywords: ["비용", "수익", "가격", "예산", "ROI", "투자"]
    priority: 4

  cmo:
    name: "CMO"
    emoji: "📢"
    persona:
      experience: "20년차"
      style: "시장 감각 마케터"
      catchphrase: "이걸 한 문장으로 설명할 수 있어야 합니다"
    keywords: ["마케팅", "브랜드", "고객", "시장", "포지셔닝", "GTM"]
    priority: 5
`
  }
};

// 7일 잠금 기간
const PREMIUM_UNLOCK_DAYS = 7;

// ============================================================
// Rate Limiting 설정
// ============================================================

const RATE_LIMITS = {
  // 엔드포인트별 제한 (requests per window)
  '/content/bundle': { requests: 10, windowSeconds: 60 },   // 분당 10회
  '/content/manifest': { requests: 20, windowSeconds: 60 }, // 분당 20회
  '/check': { requests: 30, windowSeconds: 60 },            // 분당 30회
  '/webhook': { requests: 100, windowSeconds: 60 },         // 분당 100회 (Lemon Squeezy)
  '/heartbeat': { requests: 5, windowSeconds: 60 },         // 분당 5회 (24시간마다 1회면 충분)
  'default': { requests: 60, windowSeconds: 60 }            // 기본: 분당 60회
};

// 브루트포스 감지 임계값
const BRUTE_FORCE_THRESHOLD = 50;  // 1분에 50회 이상 실패 시 차단
const BLOCK_DURATION_SECONDS = 3600;  // 1시간 차단

// ============================================================
// 감사 로그 시스템
// ============================================================

const AUDIT_EVENT_TYPES = {
  AUTH_FAILURE: 'auth_failure',           // 인증 실패
  RATE_LIMITED: 'rate_limited',           // Rate Limit 초과
  BRUTE_FORCE_BLOCKED: 'brute_force',     // 브루트포스 차단
  REVOKED_ACCESS: 'revoked_access',       // 환불된 라이선스 사용 시도
  SEAT_LIMIT: 'seat_limit',               // 시트 제한 초과
  HEARTBEAT_OK: 'heartbeat_ok',           // Heartbeat 성공
  LICENSE_ACTIVATED: 'license_activated', // 라이선스 활성화
  REFUND_PROCESSED: 'refund_processed',   // 환불 처리
};

// 감사 로그 보관 기간 (초)
const AUDIT_LOG_TTL = 7 * 24 * 60 * 60;  // 7일

/**
 * 감사 이벤트 로깅
 */
async function logAuditEvent(env, eventType, data) {
  const timestamp = new Date().toISOString();
  const eventId = `${Date.now()}-${Math.random().toString(36).substring(2, 8)}`;

  const event = {
    id: eventId,
    type: eventType,
    timestamp,
    ...data
  };

  // KV에 저장 (이벤트 타입별로 최근 100개만 유지)
  const listKey = `audit:${eventType}:list`;
  const eventKey = `audit:event:${eventId}`;

  try {
    // 이벤트 저장
    await env.REVOKED_LICENSES.put(eventKey, JSON.stringify(event), {
      expirationTtl: AUDIT_LOG_TTL
    });

    // 이벤트 목록 업데이트
    const listData = await env.REVOKED_LICENSES.get(listKey);
    let eventList = listData ? JSON.parse(listData) : [];
    eventList.unshift(eventId);

    // 최근 100개만 유지
    if (eventList.length > 100) {
      eventList = eventList.slice(0, 100);
    }

    await env.REVOKED_LICENSES.put(listKey, JSON.stringify(eventList), {
      expirationTtl: AUDIT_LOG_TTL
    });

    // 일일 통계 업데이트
    const today = timestamp.split('T')[0];
    const statsKey = `audit:stats:${today}`;
    const statsData = await env.REVOKED_LICENSES.get(statsKey);
    let stats = statsData ? JSON.parse(statsData) : {};

    stats[eventType] = (stats[eventType] || 0) + 1;
    stats.total = (stats.total || 0) + 1;

    await env.REVOKED_LICENSES.put(statsKey, JSON.stringify(stats), {
      expirationTtl: AUDIT_LOG_TTL
    });

    // 보안 이벤트는 Discord 알림
    if ([AUDIT_EVENT_TYPES.BRUTE_FORCE_BLOCKED, AUDIT_EVENT_TYPES.REVOKED_ACCESS].includes(eventType)) {
      await sendSecurityAlert(env.DISCORD_WEBHOOK_URL, {
        type: eventType,
        ...data
      });
    }

    return { success: true, eventId };
  } catch (error) {
    console.error('Audit log error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * 감사 통계 조회
 */
async function getAuditStats(env, days = 7) {
  const stats = {
    period: `${days} days`,
    daily: {},
    totals: {},
    recent_events: {}
  };

  const today = new Date();

  // 일별 통계 수집
  for (let i = 0; i < days; i++) {
    const date = new Date(today);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const statsKey = `audit:stats:${dateStr}`;
    const dayStats = await env.REVOKED_LICENSES.get(statsKey);

    if (dayStats) {
      stats.daily[dateStr] = JSON.parse(dayStats);

      // 합계 계산
      const parsed = JSON.parse(dayStats);
      for (const [key, value] of Object.entries(parsed)) {
        stats.totals[key] = (stats.totals[key] || 0) + value;
      }
    }
  }

  // 이벤트 타입별 최근 5개
  for (const eventType of Object.values(AUDIT_EVENT_TYPES)) {
    const listKey = `audit:${eventType}:list`;
    const listData = await env.REVOKED_LICENSES.get(listKey);

    if (listData) {
      const eventIds = JSON.parse(listData).slice(0, 5);
      const events = [];

      for (const eventId of eventIds) {
        const eventKey = `audit:event:${eventId}`;
        const eventData = await env.REVOKED_LICENSES.get(eventKey);
        if (eventData) {
          events.push(JSON.parse(eventData));
        }
      }

      if (events.length > 0) {
        stats.recent_events[eventType] = events;
      }
    }
  }

  return stats;
}

// ============================================================
// ============================================================
// 클라이언트 무결성 검증
// ============================================================

// 클라이언트 버전 요구사항
const CLIENT_VERSION_CONFIG = {
  // 최소 지원 버전 (이전 버전은 차단)
  MIN_SUPPORTED_VERSION: '1.0.0',
  // 권장 버전 (이전 버전은 경고)
  RECOMMENDED_VERSION: '1.2.0',
  // 현재 최신 버전
  LATEST_VERSION: '1.2.0',
  // 강제 업데이트 필요 버전 목록 (보안 취약점)
  BLOCKED_VERSIONS: ['0.9.0', '0.9.1'],
  // 버전 체크 활성화
  ENABLED: true
};

// 버전 비교 함수 (semver 간단 구현)
function compareVersions(v1, v2) {
  const parts1 = v1.split('.').map(Number);
  const parts2 = v2.split('.').map(Number);

  for (let i = 0; i < 3; i++) {
    const p1 = parts1[i] || 0;
    const p2 = parts2[i] || 0;
    if (p1 > p2) return 1;
    if (p1 < p2) return -1;
  }
  return 0;
}

// 클라이언트 버전 검증
function validateClientVersion(clientVersion) {
  if (!CLIENT_VERSION_CONFIG.ENABLED || !clientVersion) {
    return { valid: true, status: 'unknown' };
  }

  // 차단된 버전 체크
  if (CLIENT_VERSION_CONFIG.BLOCKED_VERSIONS.includes(clientVersion)) {
    return {
      valid: false,
      status: 'blocked',
      message: `버전 ${clientVersion}은(는) 보안 취약점으로 차단되었습니다. 업데이트해주세요.`,
      latest_version: CLIENT_VERSION_CONFIG.LATEST_VERSION
    };
  }

  // 최소 버전 체크
  if (compareVersions(clientVersion, CLIENT_VERSION_CONFIG.MIN_SUPPORTED_VERSION) < 0) {
    return {
      valid: false,
      status: 'unsupported',
      message: `버전 ${clientVersion}은(는) 더 이상 지원되지 않습니다. ${CLIENT_VERSION_CONFIG.MIN_SUPPORTED_VERSION} 이상으로 업데이트해주세요.`,
      min_version: CLIENT_VERSION_CONFIG.MIN_SUPPORTED_VERSION,
      latest_version: CLIENT_VERSION_CONFIG.LATEST_VERSION
    };
  }

  // 권장 버전 체크
  if (compareVersions(clientVersion, CLIENT_VERSION_CONFIG.RECOMMENDED_VERSION) < 0) {
    return {
      valid: true,
      status: 'outdated',
      message: `새 버전 ${CLIENT_VERSION_CONFIG.LATEST_VERSION}이(가) 있습니다. 업데이트를 권장합니다.`,
      current_version: clientVersion,
      latest_version: CLIENT_VERSION_CONFIG.LATEST_VERSION
    };
  }

  return {
    valid: true,
    status: 'current',
    current_version: clientVersion
  };
}

// 버전 체크 핸들러
function handleVersionCheck(request) {
  const url = new URL(request.url);
  const clientVersion = url.searchParams.get('v') || url.searchParams.get('version');

  const result = validateClientVersion(clientVersion);

  return new Response(JSON.stringify({
    ...result,
    config: {
      min_supported: CLIENT_VERSION_CONFIG.MIN_SUPPORTED_VERSION,
      recommended: CLIENT_VERSION_CONFIG.RECOMMENDED_VERSION,
      latest: CLIENT_VERSION_CONFIG.LATEST_VERSION,
      blocked_versions: CLIENT_VERSION_CONFIG.BLOCKED_VERSIONS
    }
  }), { headers: corsHeaders() });
}

// ============================================================
// 이상 탐지 시스템 (Anomaly Detection)
// ============================================================

// 이상 탐지 임계값
const ANOMALY_THRESHOLDS = {
  // 24시간 내 다른 국가 접속 수
  MAX_COUNTRIES_24H: 3,
  // 1시간 내 다른 머신 ID 수
  MAX_MACHINES_1H: 5,
  // 평소 대비 요청 배율 (10배 이상이면 이상)
  REQUEST_SPIKE_MULTIPLIER: 10,
  // 새벽 시간 집중 접속 비율 (70% 이상이면 봇 의심)
  NIGHT_ACCESS_RATIO: 0.7,
  // 의심 점수 임계값
  SUSPICION_LEVEL_1: 30,   // 로그만
  SUSPICION_LEVEL_2: 60,   // Discord 알림
  SUSPICION_LEVEL_3: 90,   // 자동 일시 차단
};

// 이상 탐지 데이터 TTL
const ANOMALY_DATA_TTL = 24 * 60 * 60;  // 24시간

/**
 * 사용자 활동 기록
 */
async function recordUserActivity(env, licenseKey, data) {
  const { ip, machineId, endpoint, country } = data;
  const now = Date.now();
  const hour = Math.floor(now / (60 * 60 * 1000));  // 시간 단위
  const day = new Date().toISOString().split('T')[0];

  try {
    // 1. 시간별 요청 카운트
    const hourlyKey = `activity:hourly:${licenseKey}:${hour}`;
    const hourlyCount = await env.REVOKED_LICENSES.get(hourlyKey);
    const newHourlyCount = (hourlyCount ? parseInt(hourlyCount, 10) : 0) + 1;
    await env.REVOKED_LICENSES.put(hourlyKey, newHourlyCount.toString(), {
      expirationTtl: 2 * 60 * 60  // 2시간 후 만료
    });

    // 2. 일별 요청 카운트
    const dailyKey = `activity:daily:${licenseKey}:${day}`;
    const dailyCount = await env.REVOKED_LICENSES.get(dailyKey);
    const newDailyCount = (dailyCount ? parseInt(dailyCount, 10) : 0) + 1;
    await env.REVOKED_LICENSES.put(dailyKey, newDailyCount.toString(), {
      expirationTtl: ANOMALY_DATA_TTL
    });

    // 3. 국가별 접속 기록 (24시간)
    if (country) {
      const countryKey = `activity:countries:${licenseKey}:${day}`;
      const countryData = await env.REVOKED_LICENSES.get(countryKey);
      const countries = countryData ? JSON.parse(countryData) : {};
      countries[country] = (countries[country] || 0) + 1;
      await env.REVOKED_LICENSES.put(countryKey, JSON.stringify(countries), {
        expirationTtl: ANOMALY_DATA_TTL
      });
    }

    // 4. 머신 ID 기록 (1시간)
    if (machineId) {
      const machineKey = `activity:machines:${licenseKey}:${hour}`;
      const machineData = await env.REVOKED_LICENSES.get(machineKey);
      const machines = machineData ? JSON.parse(machineData) : {};
      machines[machineId] = now;
      await env.REVOKED_LICENSES.put(machineKey, JSON.stringify(machines), {
        expirationTtl: 2 * 60 * 60  // 2시간 후 만료
      });
    }

    // 5. 시간대별 접속 기록 (봇 감지용)
    const currentHour = new Date().getUTCHours();
    const hourDistKey = `activity:hours:${licenseKey}:${day}`;
    const hourDistData = await env.REVOKED_LICENSES.get(hourDistKey);
    const hourDist = hourDistData ? JSON.parse(hourDistData) : {};
    hourDist[currentHour] = (hourDist[currentHour] || 0) + 1;
    await env.REVOKED_LICENSES.put(hourDistKey, JSON.stringify(hourDist), {
      expirationTtl: ANOMALY_DATA_TTL
    });

    return { success: true };
  } catch (error) {
    console.error('Record activity error:', error);
    return { success: false, error: error.message };
  }
}

/**
 * 이상 징후 분석
 */
async function analyzeAnomalies(env, licenseKey) {
  const now = Date.now();
  const hour = Math.floor(now / (60 * 60 * 1000));
  const day = new Date().toISOString().split('T')[0];

  let suspicionScore = 0;
  const anomalies = [];

  try {
    // 1. 다국가 접속 체크
    const countryKey = `activity:countries:${licenseKey}:${day}`;
    const countryData = await env.REVOKED_LICENSES.get(countryKey);
    if (countryData) {
      const countries = JSON.parse(countryData);
      const countryCount = Object.keys(countries).length;
      if (countryCount >= ANOMALY_THRESHOLDS.MAX_COUNTRIES_24H) {
        suspicionScore += 40;
        anomalies.push({
          type: 'multi_country',
          detail: `24시간 내 ${countryCount}개국 접속`,
          countries: Object.keys(countries)
        });
      }
    }

    // 2. 다중 머신 체크
    const machineKey = `activity:machines:${licenseKey}:${hour}`;
    const machineData = await env.REVOKED_LICENSES.get(machineKey);
    if (machineData) {
      const machines = JSON.parse(machineData);
      const machineCount = Object.keys(machines).length;
      if (machineCount >= ANOMALY_THRESHOLDS.MAX_MACHINES_1H) {
        suspicionScore += 50;
        anomalies.push({
          type: 'multi_machine',
          detail: `1시간 내 ${machineCount}대 머신 사용`,
          count: machineCount
        });
      }
    }

    // 3. 새벽 시간 집중 접속 체크 (봇 의심)
    const hourDistKey = `activity:hours:${licenseKey}:${day}`;
    const hourDistData = await env.REVOKED_LICENSES.get(hourDistKey);
    if (hourDistData) {
      const hourDist = JSON.parse(hourDistData);
      let totalRequests = 0;
      let nightRequests = 0;  // 0-6시 UTC

      for (const [h, count] of Object.entries(hourDist)) {
        totalRequests += count;
        if (parseInt(h, 10) >= 0 && parseInt(h, 10) <= 6) {
          nightRequests += count;
        }
      }

      if (totalRequests > 10) {  // 충분한 샘플이 있을 때만
        const nightRatio = nightRequests / totalRequests;
        if (nightRatio >= ANOMALY_THRESHOLDS.NIGHT_ACCESS_RATIO) {
          suspicionScore += 30;
          anomalies.push({
            type: 'bot_pattern',
            detail: `새벽 시간 접속 비율 ${Math.round(nightRatio * 100)}%`,
            night_ratio: nightRatio
          });
        }
      }
    }

    // 4. 요청 급증 체크
    const dailyKey = `activity:daily:${licenseKey}:${day}`;
    const dailyCount = await env.REVOKED_LICENSES.get(dailyKey);
    if (dailyCount) {
      const todayCount = parseInt(dailyCount, 10);

      // 어제 데이터와 비교
      const yesterday = new Date();
      yesterday.setDate(yesterday.getDate() - 1);
      const yesterdayStr = yesterday.toISOString().split('T')[0];
      const yesterdayKey = `activity:daily:${licenseKey}:${yesterdayStr}`;
      const yesterdayCount = await env.REVOKED_LICENSES.get(yesterdayKey);

      if (yesterdayCount) {
        const prevCount = parseInt(yesterdayCount, 10);
        if (prevCount > 0 && todayCount > prevCount * ANOMALY_THRESHOLDS.REQUEST_SPIKE_MULTIPLIER) {
          suspicionScore += 35;
          anomalies.push({
            type: 'request_spike',
            detail: `요청 ${Math.round(todayCount / prevCount)}배 급증`,
            today: todayCount,
            yesterday: prevCount
          });
        }
      }
    }

    // 의심 레벨 결정
    let level = 0;
    if (suspicionScore >= ANOMALY_THRESHOLDS.SUSPICION_LEVEL_3) {
      level = 3;
    } else if (suspicionScore >= ANOMALY_THRESHOLDS.SUSPICION_LEVEL_2) {
      level = 2;
    } else if (suspicionScore >= ANOMALY_THRESHOLDS.SUSPICION_LEVEL_1) {
      level = 1;
    }

    return {
      license_key_masked: maskLicenseKey(licenseKey),
      suspicion_score: suspicionScore,
      suspicion_level: level,
      anomalies,
      analyzed_at: new Date().toISOString()
    };
  } catch (error) {
    console.error('Analyze anomalies error:', error);
    return {
      suspicion_score: 0,
      suspicion_level: 0,
      anomalies: [],
      error: error.message
    };
  }
}

/**
 * 이상 징후 대응
 */
async function handleAnomalyResponse(env, licenseKey, analysis) {
  const { suspicion_level, suspicion_score, anomalies } = analysis;

  if (suspicion_level === 0) {
    return { action: 'none' };
  }

  // 반복 위반 카운트 조회 및 증가
  const violationKey = `violations:${licenseKey}`;
  const violationData = await env.REVOKED_LICENSES.get(violationKey);
  let violations = violationData ? JSON.parse(violationData) : { count: 0, history: [] };

  violations.count++;
  violations.history.push({
    timestamp: new Date().toISOString(),
    level: suspicion_level,
    score: suspicion_score
  });

  // 최근 10개만 유지
  if (violations.history.length > 10) {
    violations.history = violations.history.slice(-10);
  }

  await env.REVOKED_LICENSES.put(violationKey, JSON.stringify(violations), {
    expirationTtl: 7 * 24 * 60 * 60  // 7일 후 리셋
  });

  // Level 1: 로그만
  await logAuditEvent(env, 'anomaly_detected', {
    license_key_masked: maskLicenseKey(licenseKey),
    suspicion_score,
    suspicion_level,
    violation_count: violations.count,
    anomalies
  });

  // Level 2: Discord 알림 + Rate Limit 강화
  if (suspicion_level >= 2) {
    // Discord 알림
    if (env.DISCORD_WEBHOOK_URL) {
      await sendSecurityAlert(env.DISCORD_WEBHOOK_URL, {
        type: `anomaly_level_${suspicion_level}`,
        license_key_masked: maskLicenseKey(licenseKey),
        suspicion_score,
        anomalies,
        message: `위반 횟수: ${violations.count}회 (7일간)`
      });
    }

    // Rate Limit 강화 플래그 설정 (2시간)
    const rateLimitKey = `enhanced_rate_limit:${licenseKey}`;
    await env.REVOKED_LICENSES.put(rateLimitKey, JSON.stringify({
      multiplier: 0.5,  // 요청 한도 50% 감소
      set_at: new Date().toISOString()
    }), {
      expirationTtl: 2 * 60 * 60  // 2시간
    });
  }

  // Level 3: 자동 일시 차단 (반복 위반 시 시간 증가)
  if (suspicion_level >= 3) {
    // 반복 위반에 따른 차단 시간 계산
    let suspendHours = 1;  // 기본 1시간
    if (violations.count >= 5) suspendHours = 24;  // 5회 이상: 24시간
    else if (violations.count >= 3) suspendHours = 6;  // 3회 이상: 6시간
    else if (violations.count >= 2) suspendHours = 2;  // 2회: 2시간

    const suspendKey = `suspended:${licenseKey}`;
    await env.REVOKED_LICENSES.put(suspendKey, JSON.stringify({
      suspended_at: new Date().toISOString(),
      reason: 'anomaly_detected',
      suspicion_score,
      violation_count: violations.count,
      suspend_hours: suspendHours,
      anomalies
    }), {
      expirationTtl: suspendHours * 60 * 60
    });

    // Level 3 자동 차단 Discord 알림
    if (env.DISCORD_WEBHOOK_URL) {
      await sendSecurityAlert(env.DISCORD_WEBHOOK_URL, {
        type: 'anomaly_level_3',
        license_key_masked: maskLicenseKey(licenseKey),
        suspicion_score,
        anomalies,
        action: `자동 일시정지 ${suspendHours}시간 (위반 ${violations.count}회)`
      });
    }

    return {
      action: 'suspended',
      duration: `${suspendHours} hour(s)`,
      violation_count: violations.count,
      reason: 'Suspicious activity detected'
    };
  }

  return {
    action: suspicion_level >= 2 ? 'alerted_rate_limited' : 'logged',
    suspicion_level,
    violation_count: violations.count
  };
}

/**
 * 이상 징후 Discord 알림
 */
async function sendAnomalyAlert(webhookUrl, data) {
  if (!webhookUrl) return;

  const levelEmoji = data.suspicion_level >= 3 ? '🚨' : '⚠️';
  const levelText = data.suspicion_level >= 3 ? 'CRITICAL' : 'WARNING';

  const anomalyFields = data.anomalies.map(a => ({
    name: a.type,
    value: a.detail,
    inline: true
  }));

  const embed = {
    title: `${levelEmoji} 이상 징후 감지 (${levelText})`,
    color: data.suspicion_level >= 3 ? 0xff0000 : 0xff9900,
    fields: [
      { name: '라이선스', value: data.license_key_masked, inline: true },
      { name: '의심 점수', value: String(data.suspicion_score), inline: true },
      { name: '레벨', value: String(data.suspicion_level), inline: true },
      ...anomalyFields
    ],
    footer: { text: 'Clouvel Anomaly Detection' },
    timestamp: new Date().toISOString()
  };

  try {
    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ embeds: [embed] })
    });
  } catch (e) {
    console.error('Anomaly alert failed:', e);
  }
}

/**
 * 일시 정지 상태 확인
 */
async function checkSuspended(env, licenseKey) {
  const suspendKey = `suspended:${licenseKey}`;
  const suspended = await env.REVOKED_LICENSES.get(suspendKey);

  if (suspended) {
    const data = JSON.parse(suspended);
    return {
      suspended: true,
      ...data
    };
  }

  return { suspended: false };
}

/**
 * Rate Limit 체크
 * @returns {Object} { allowed: boolean, remaining: number, resetAt: number }
 */
async function checkRateLimit(env, identifier, endpoint) {
  const limits = RATE_LIMITS[endpoint] || RATE_LIMITS['default'];
  const key = `ratelimit:${endpoint}:${identifier}`;
  const now = Math.floor(Date.now() / 1000);
  const windowStart = now - (now % limits.windowSeconds);
  const windowKey = `${key}:${windowStart}`;

  try {
    // 현재 카운트 조회
    const currentData = await env.REVOKED_LICENSES.get(windowKey);
    let count = currentData ? parseInt(currentData, 10) : 0;

    if (count >= limits.requests) {
      return {
        allowed: false,
        remaining: 0,
        resetAt: windowStart + limits.windowSeconds,
        limit: limits.requests
      };
    }

    // 카운트 증가 (TTL 설정으로 자동 만료)
    count++;
    await env.REVOKED_LICENSES.put(windowKey, count.toString(), {
      expirationTtl: limits.windowSeconds * 2  // 윈도우의 2배 후 자동 삭제
    });

    return {
      allowed: true,
      remaining: limits.requests - count,
      resetAt: windowStart + limits.windowSeconds,
      limit: limits.requests
    };
  } catch (error) {
    console.error('Rate limit check error:', error);
    // 에러 시 허용 (fail-open)
    return { allowed: true, remaining: -1, resetAt: 0, limit: limits.requests };
  }
}

/**
 * 브루트포스 감지 및 차단
 */
async function checkBruteForce(env, ip, isFailure) {
  const key = `bruteforce:${ip}`;
  const blockKey = `blocked:${ip}`;

  try {
    // 이미 차단된 IP인지 확인
    const blocked = await env.REVOKED_LICENSES.get(blockKey);
    if (blocked) {
      return { blocked: true, reason: 'IP blocked due to suspicious activity' };
    }

    if (!isFailure) {
      return { blocked: false };
    }

    // 실패 카운트 증가
    const currentData = await env.REVOKED_LICENSES.get(key);
    let count = currentData ? parseInt(currentData, 10) : 0;
    count++;

    if (count >= BRUTE_FORCE_THRESHOLD) {
      // IP 차단
      await env.REVOKED_LICENSES.put(blockKey, JSON.stringify({
        blocked_at: new Date().toISOString(),
        reason: 'brute_force',
        failure_count: count
      }), {
        expirationTtl: BLOCK_DURATION_SECONDS
      });

      // Discord 알림
      if (env.DISCORD_WEBHOOK_URL) {
        await sendSecurityAlert(env.DISCORD_WEBHOOK_URL, {
          type: 'BRUTE_FORCE_BLOCKED',
          ip: ip,
          failure_count: count
        });
      }

      return { blocked: true, reason: 'Too many failed attempts' };
    }

    // 카운트 저장 (1분 후 만료)
    await env.REVOKED_LICENSES.put(key, count.toString(), {
      expirationTtl: 60
    });

    return { blocked: false, failureCount: count };
  } catch (error) {
    console.error('Brute force check error:', error);
    return { blocked: false };
  }
}

/**
 * 보안 알림 전송
 */
// 알림 유형별 설정
const ALERT_CONFIG = {
  brute_force: {
    title: '🚨 브루트포스 공격 감지',
    color: 0xFF0000,  // 빨강
    priority: 'critical'
  },
  revoked_access: {
    title: '⚠️ 환불 라이선스 사용 시도',
    color: 0xFF6600,  // 주황
    priority: 'high'
  },
  anomaly_level_3: {
    title: '🔴 심각한 이상 징후 (Level 3)',
    color: 0xFF0000,  // 빨강
    priority: 'critical'
  },
  anomaly_level_2: {
    title: '🟠 이상 징후 경고 (Level 2)',
    color: 0xFF6600,  // 주황
    priority: 'high'
  },
  anomaly_level_1: {
    title: '🟡 이상 징후 모니터링 (Level 1)',
    color: 0xFFCC00,  // 노랑
    priority: 'medium'
  },
  license_sharing: {
    title: '👥 라이선스 공유 의심',
    color: 0xFF6600,  // 주황
    priority: 'high'
  },
  concurrent_limit: {
    title: '📱 동시 사용 제한 초과',
    color: 0x0EA5E9,  // 파랑 (정보)
    priority: 'info'
  },
  daily_report: {
    title: '📊 일일 보안 리포트',
    color: 0x10B981,  // 초록
    priority: 'info'
  }
};

async function sendSecurityAlert(webhookUrl, data) {
  if (!webhookUrl) return;

  const config = ALERT_CONFIG[data.type] || {
    title: `🔔 보안 알림: ${data.type}`,
    color: 0x6B7280,
    priority: 'info'
  };

  const fields = [
    { name: '시각', value: new Date().toISOString(), inline: true }
  ];

  // 타입별 필드 추가
  if (data.ip) fields.push({ name: 'IP', value: data.ip, inline: true });
  if (data.license_key_masked) fields.push({ name: '라이선스', value: data.license_key_masked, inline: true });
  if (data.failure_count) fields.push({ name: '실패 횟수', value: String(data.failure_count), inline: true });
  if (data.machine_id) fields.push({ name: '머신 ID', value: data.machine_id, inline: true });
  if (data.country) fields.push({ name: '국가', value: data.country, inline: true });

  // 이상 탐지 관련 필드
  if (data.suspicion_score !== undefined) fields.push({ name: '의심 점수', value: String(data.suspicion_score), inline: true });
  if (data.anomalies && data.anomalies.length > 0) {
    const anomalyList = data.anomalies.map(a => `• ${a.detail || a.type}`).join('\n');
    fields.push({ name: '탐지된 이상 징후', value: anomalyList, inline: false });
  }

  // 라이선스 공유 관련 필드
  if (data.unique_ips) fields.push({ name: '고유 IP 수', value: String(data.unique_ips), inline: true });
  if (data.countries && Array.isArray(data.countries)) {
    fields.push({ name: '접속 국가', value: data.countries.join(', '), inline: true });
  }

  // 일일 리포트 필드
  if (data.total_requests !== undefined) fields.push({ name: '총 요청', value: String(data.total_requests), inline: true });
  if (data.blocked_count !== undefined) fields.push({ name: '차단 횟수', value: String(data.blocked_count), inline: true });
  if (data.active_licenses !== undefined) fields.push({ name: '활성 라이선스', value: String(data.active_licenses), inline: true });

  // 상세 메시지
  if (data.message) fields.push({ name: '상세', value: data.message, inline: false });

  // 조치 내용
  if (data.action) fields.push({ name: '자동 조치', value: data.action, inline: false });

  const embed = {
    title: config.title,
    color: config.color,
    fields: fields,
    footer: { text: `Clouvel Security | Priority: ${config.priority}` },
    timestamp: new Date().toISOString()
  };

  try {
    await fetch(webhookUrl, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ embeds: [embed] })
    });
  } catch (e) {
    console.error('Security alert failed:', e);
  }
}

/**
 * Rate Limit 응답 헤더 추가
 */
function addRateLimitHeaders(response, rateLimitInfo) {
  const headers = new Headers(response.headers);
  headers.set('X-RateLimit-Limit', String(rateLimitInfo.limit));
  headers.set('X-RateLimit-Remaining', String(rateLimitInfo.remaining));
  headers.set('X-RateLimit-Reset', String(rateLimitInfo.resetAt));
  return new Response(response.body, {
    status: response.status,
    headers
  });
}

// ============================================================
// 유틸리티 함수
// ============================================================

// 웹훅 서명 검증
async function verifyWebhookSignature(request, secret) {
  const signature = request.headers.get('X-Signature');
  if (!signature) return false;

  const body = await request.clone().text();
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signatureBuffer = await crypto.subtle.sign('HMAC', key, encoder.encode(body));
  const expectedSignature = Array.from(new Uint8Array(signatureBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');

  return signature === expectedSignature;
}

// Discord 알림
async function sendDiscordNotification(webhookUrl, data) {
  if (!webhookUrl) return;

  const embed = {
    title: '🔴 환불 감지',
    color: 0xff0000,
    fields: [
      { name: '주문 ID', value: data.order_id || 'N/A', inline: true },
      { name: '라이선스 키', value: maskLicenseKey(data.license_key), inline: true },
      { name: '이메일', value: data.email || 'N/A', inline: true },
      { name: '금액', value: data.total || 'N/A', inline: true },
      { name: '상품', value: data.product_name || 'N/A', inline: true },
      { name: '시각', value: new Date().toISOString(), inline: true },
    ],
    footer: { text: 'Clouvel License System' }
  };

  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ embeds: [embed] })
  });
}

// 라이선스 키 마스킹
function maskLicenseKey(key) {
  if (!key) return 'N/A';
  if (key.length <= 8) return '****';
  return key.substring(0, 4) + '****' + key.substring(key.length - 4);
}

// Lemon Squeezy 라이선스 검증
async function validateLicenseWithLemonSqueezy(licenseKey) {
  try {
    const response = await fetch('https://api.lemonsqueezy.com/v1/licenses/validate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        license_key: licenseKey,
        instance_name: 'clouvel-content-api'
      })
    });

    if (response.ok) {
      const data = await response.json();
      return {
        valid: data.valid === true,
        meta: data.meta || {},
        license_key: data.license_key || {}
      };
    }
    return { valid: false };
  } catch (error) {
    console.error('License validation error:', error);
    return { valid: false, error: error.message };
  }
}

// CORS 헤더
function corsHeaders() {
  return {
    'Access-Control-Allow-Origin': '*',
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type, Authorization',
    'Content-Type': 'application/json'
  };
}

// ============================================================
// 메인 핸들러
// ============================================================

export default {
  async fetch(request, env) {
    const url = new URL(request.url);
    const clientIP = request.headers.get('CF-Connecting-IP') ||
                     request.headers.get('X-Forwarded-For')?.split(',')[0] ||
                     'unknown';

    // CORS 프리플라이트
    if (request.method === 'OPTIONS') {
      return new Response(null, { headers: corsHeaders() });
    }

    // Health 엔드포인트는 Rate Limit 제외
    if (url.pathname === '/health') {
      return handleHealth();
    }

    // 브루트포스 차단 확인
    const bruteForceCheck = await checkBruteForce(env, clientIP, false);
    if (bruteForceCheck.blocked) {
      return new Response(JSON.stringify({
        error: 'IP_BLOCKED',
        message: bruteForceCheck.reason
      }), {
        status: 403,
        headers: corsHeaders()
      });
    }

    // Rate Limiting 체크
    const rateLimitInfo = await checkRateLimit(env, clientIP, url.pathname);
    if (!rateLimitInfo.allowed) {
      // Rate Limit 감사 로그
      logAuditEvent(env, AUDIT_EVENT_TYPES.RATE_LIMITED, {
        ip: clientIP,
        endpoint: url.pathname,
        limit: rateLimitInfo.limit
      }).catch(console.error);

      const response = new Response(JSON.stringify({
        error: 'RATE_LIMITED',
        message: 'Too many requests. Please try again later.',
        retry_after: rateLimitInfo.resetAt - Math.floor(Date.now() / 1000)
      }), {
        status: 429,
        headers: corsHeaders()
      });
      return addRateLimitHeaders(response, rateLimitInfo);
    }

    // 라우팅
    let response;
    switch (url.pathname) {
      // 기존 엔드포인트
      case '/webhook':
        response = await handleWebhook(request, env);
        break;
      case '/check':
        response = await handleCheck(request, env);
        break;

      // 콘텐츠 API (신규)
      case '/content/bundle':
        response = await handleContentBundle(request, env);
        break;
      case '/content/manifest':
        response = await handleContentManifest(request, env);
        break;

      // 통계 API (신규)
      case '/stats/rate-limits':
        response = await handleRateLimitStats(request, env, clientIP);
        break;
      case '/stats/audit':
        response = await handleAuditStats(request, env);
        break;
      case '/test/audit':
        response = await handleTestAudit(request, env);
        break;
      case '/test/refund':
        response = await handleTestRefund(request, env);
        break;
      case '/test/anomaly':
        response = await handleTestAnomaly(request, env);
        break;
      case '/test/team-license':
        response = await handleTestTeamLicense(request, env);
        break;

      // 이상 탐지 API
      case '/stats/anomaly':
        response = await handleAnomalyStats(request, env);
        break;
      case '/analyze/license':
        response = await handleAnalyzeLicense(request, env);
        break;

      // 라이선스 관리 API (신규)
      case '/license/status':
        response = await handleLicenseStatus(request, env);
        break;
      case '/license/machines':
        response = await handleListMachines(request, env);
        break;
      case '/license/deactivate-machine':
        response = await handleDeactivateMachine(request, env);
        break;

      // 오프라인 토큰 API (신규)
      case '/token/issue':
        response = await handleTokenIssue(request, env);
        break;
      case '/token/verify':
        response = await handleTokenVerify(request, env);
        break;

      // 관리자 대시보드 API (신규)
      case '/admin/dashboard':
        response = await handleAdminDashboard(request, env);
        break;
      case '/admin/block':
        response = await handleAdminBlock(request, env);
        break;
      case '/admin/unblock':
        response = await handleAdminUnblock(request, env);
        break;
      case '/admin/daily-report':
        response = await handleDailyReport(request, env);
        break;
      case '/admin/check-sharing':
        response = await handleCheckLicenseSharing(request, env);
        break;
      case '/version/check':
        response = handleVersionCheck(request);
        break;

      // Heartbeat API (신규)
      case '/heartbeat':
        response = await handleHeartbeat(request, env);
        break;

      // Team API (Phase 4)
      case '/team/invite':
        response = await handleTeamInvite(request, env);
        break;
      case '/team/members':
        response = await handleTeamMembers(request, env);
        break;
      case '/team/remove':
        response = await handleTeamRemove(request, env);
        break;
      case '/team/role':
        response = await handleTeamRole(request, env);
        break;
      case '/team/settings':
        response = await handleTeamSettings(request, env);
        break;
      case '/team/errors/sync':
        response = await handleTeamErrorsSync(request, env);
        break;
      case '/team/errors':
        response = await handleTeamErrors(request, env);
        break;
      case '/team/errors/rules':
        response = await handleTeamErrorRules(request, env);
        break;
      case '/team/project/sync':
        response = await handleTeamProjectSync(request, env);
        break;
      case '/team/project':
        response = await handleTeamProject(request, env);
        break;
      case '/team/review/rules':
        response = await handleTeamReviewRules(request, env);
        break;

      default:
        response = new Response(JSON.stringify({ error: 'Not Found' }), {
          status: 404,
          headers: corsHeaders()
        });
    }

    // 인증 실패 시 브루트포스 카운트 증가 및 감사 로그
    if (response.status === 401 || response.status === 403) {
      await checkBruteForce(env, clientIP, true);

      // 감사 로그 (비동기로 처리, 응답 지연 방지)
      logAuditEvent(env, AUDIT_EVENT_TYPES.AUTH_FAILURE, {
        ip: clientIP,
        endpoint: url.pathname,
        status: response.status
      }).catch(console.error);
    }

    // Rate Limit 헤더 추가
    return addRateLimitHeaders(response, rateLimitInfo);
  }
};

// ============================================================
// 웹훅 핸들러 (기존)
// ============================================================

async function handleWebhook(request, env) {
  if (request.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405 });
  }

  const isValid = await verifyWebhookSignature(request, env.LEMON_SQUEEZY_WEBHOOK_SECRET);
  if (!isValid) {
    console.error('Invalid webhook signature');
    return new Response('Unauthorized', { status: 401 });
  }

  try {
    const payload = await request.json();
    const eventName = payload.meta?.event_name;

    console.log(`Received event: ${eventName}`);

    if (eventName === 'order_refunded') {
      const data = payload.data?.attributes || {};
      const licenseKey = data.first_order_item?.license_key;
      const orderId = data.identifier || data.order_number;

      if (licenseKey) {
        const refundData = {
          license_key: licenseKey,
          refunded_at: new Date().toISOString(),
          order_id: orderId,
          reason: 'refund',
          email: data.user_email,
          product_name: data.first_order_item?.product_name,
          total: data.total_formatted
        };

        // 환불 라이선스 저장
        await env.REVOKED_LICENSES.put(licenseKey, JSON.stringify(refundData));

        // 환불 목록에 추가
        await env.REVOKED_LICENSES.put(`refund:${licenseKey}`, JSON.stringify(refundData));
        const refundListData = await env.REVOKED_LICENSES.get('refunds:list');
        const refundList = refundListData ? JSON.parse(refundListData) : [];
        if (!refundList.includes(licenseKey)) {
          refundList.unshift(licenseKey);  // 최신순
          await env.REVOKED_LICENSES.put('refunds:list', JSON.stringify(refundList.slice(0, 200)));
        }

        console.log(`License revoked: ${maskLicenseKey(licenseKey)}`);

        // 감사 로그
        await logAuditEvent(env, AUDIT_EVENT_TYPES.REFUND_PROCESSED, {
          order_id: orderId,
          license_key_masked: maskLicenseKey(licenseKey),
          email: data.user_email,
          product_name: data.first_order_item?.product_name,
          total: data.total_formatted
        });

        await sendDiscordNotification(env.DISCORD_WEBHOOK_URL, {
          order_id: orderId,
          license_key: licenseKey,
          email: data.user_email,
          product_name: data.first_order_item?.product_name,
          total: data.total_formatted
        });
      }
    }

    return new Response(JSON.stringify({ success: true }), {
      headers: { 'Content-Type': 'application/json' }
    });

  } catch (error) {
    console.error('Webhook error:', error);
    return new Response(JSON.stringify({ error: error.message }), {
      status: 500,
      headers: { 'Content-Type': 'application/json' }
    });
  }
}

// ============================================================
// 라이선스 체크 (기존)
// ============================================================

async function handleCheck(request, env) {
  const url = new URL(request.url);
  const licenseKey = url.searchParams.get('key');

  if (!licenseKey) {
    return new Response(JSON.stringify({ error: 'Missing key parameter' }), {
      status: 400,
      headers: corsHeaders()
    });
  }

  const revoked = await env.REVOKED_LICENSES.get(licenseKey);

  if (revoked) {
    const data = JSON.parse(revoked);
    return new Response(JSON.stringify({
      revoked: true,
      revoked_at: data.revoked_at,
      reason: data.reason
    }), { headers: corsHeaders() });
  }

  return new Response(JSON.stringify({ revoked: false }), {
    headers: corsHeaders()
  });
}

// ============================================================
// 헬스 체크 (기존)
// ============================================================

async function handleHealth() {
  return new Response(JSON.stringify({
    status: 'ok',
    timestamp: new Date().toISOString(),
    service: 'clouvel-license-webhook',
    version: '2.0.0',  // Week 2: Rate Limiting 추가
    content_version: PREMIUM_CONTENT.version,
    features: {
      rate_limiting: true,
      brute_force_protection: true,
      machine_id_binding: true,
      premium_lock_days: PREMIUM_UNLOCK_DAYS
    }
  }), { headers: { 'Content-Type': 'application/json' } });
}

// Rate Limit 통계 (현재 사용자의 상태만)
async function handleRateLimitStats(request, env, clientIP) {
  // 현재 IP의 rate limit 상태
  const endpoints = ['/content/bundle', '/content/manifest', '/check'];
  const stats = {};
  const now = Math.floor(Date.now() / 1000);

  for (const endpoint of endpoints) {
    const limits = RATE_LIMITS[endpoint] || RATE_LIMITS['default'];
    const windowStart = now - (now % limits.windowSeconds);
    const key = `ratelimit:${endpoint}:${clientIP}:${windowStart}`;

    const count = await env.REVOKED_LICENSES.get(key);
    stats[endpoint] = {
      used: count ? parseInt(count, 10) : 0,
      limit: limits.requests,
      remaining: limits.requests - (count ? parseInt(count, 10) : 0),
      window_seconds: limits.windowSeconds,
      resets_at: new Date((windowStart + limits.windowSeconds) * 1000).toISOString()
    };
  }

  // 브루트포스 상태
  const blockKey = `blocked:${clientIP}`;
  const blocked = await env.REVOKED_LICENSES.get(blockKey);

  return new Response(JSON.stringify({
    ip: clientIP.substring(0, 8) + '***',  // 부분 마스킹
    blocked: !!blocked,
    endpoints: stats,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// 테스트용 감사 로그 생성 핸들러
async function handleTestAudit(request, env) {
  // 테스트 이벤트 생성
  const result = await logAuditEvent(env, AUDIT_EVENT_TYPES.AUTH_FAILURE, {
    ip: 'test-ip',
    endpoint: '/test/audit',
    status: 999,
    test: true
  });

  // 방금 생성한 이벤트 확인
  const stats = await getAuditStats(env, 1);

  return new Response(JSON.stringify({
    log_result: result,
    stats: stats,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// 테스트 환불 데이터 추가
async function handleTestRefund(request, env) {
  // 관리자 인증
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Admin API key required'
    }), { status: 401, headers: corsHeaders() });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    body = {};
  }

  const licenseKey = body.license_key || `TEST-REFUND-${Date.now()}`;
  const refundData = {
    license_key: licenseKey,
    refunded_at: body.refunded_at || new Date().toISOString(),
    order_id: body.order_id || `ORD-TEST-${Date.now()}`,
    reason: body.reason || 'Test refund',
    email: body.email || 'test@example.com',
    product_name: body.product_name || 'Clouvel Pro Personal',
    total: body.total || '$29.00'
  };

  // 환불 데이터 저장
  await env.REVOKED_LICENSES.put(licenseKey, JSON.stringify({
    ...refundData,
    revoked_at: refundData.refunded_at
  }));

  // refund: 키로도 저장
  await env.REVOKED_LICENSES.put(`refund:${licenseKey}`, JSON.stringify(refundData));

  // 환불 목록에 추가
  const refundListData = await env.REVOKED_LICENSES.get('refunds:list');
  const refundList = refundListData ? JSON.parse(refundListData) : [];
  if (!refundList.includes(licenseKey)) {
    refundList.unshift(licenseKey);
    await env.REVOKED_LICENSES.put('refunds:list', JSON.stringify(refundList.slice(0, 200)));
  }

  // 감사 로그
  await logAuditEvent(env, AUDIT_EVENT_TYPES.REFUND_PROCESSED, {
    license_key_masked: maskLicenseKey(licenseKey),
    order_id: refundData.order_id,
    test: true
  });

  return new Response(JSON.stringify({
    success: true,
    refund: refundData,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// 테스트 이상 탐지 데이터 추가
async function handleTestAnomaly(request, env) {
  // 관리자 인증
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Admin API key required'
    }), { status: 401, headers: corsHeaders() });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    body = {};
  }

  const licenseKey = body.license_key || `TEST-ANOMALY-${Date.now()}`;
  const day = new Date().toISOString().split('T')[0];
  const hour = Math.floor(Date.now() / (60 * 60 * 1000));

  // 1. 라이선스 목록에 추가
  const licenseListData = await env.REVOKED_LICENSES.get('licenses:list');
  const licenseList = licenseListData ? JSON.parse(licenseListData) : [];
  if (!licenseList.includes(licenseKey)) {
    licenseList.unshift(licenseKey);
    await env.REVOKED_LICENSES.put('licenses:list', JSON.stringify(licenseList.slice(0, 500)));
  }

  // 2. 라이선스 정보 저장
  await env.REVOKED_LICENSES.put(`license:${licenseKey}`, JSON.stringify({
    tier: body.tier || 'personal',
    status: 'active',
    last_active: new Date().toISOString()
  }));

  // 3. 다국가 접속 데이터 추가 (의심 점수 +40)
  const countries = body.countries || ['KR', 'US', 'CN', 'JP', 'DE'];
  const countryData = {};
  countries.forEach(c => { countryData[c] = Math.floor(Math.random() * 10) + 1; });
  await env.REVOKED_LICENSES.put(`activity:countries:${licenseKey}:${day}`, JSON.stringify(countryData));

  // 4. 다중 머신 데이터 추가 (의심 점수 +50)
  const machineCount = body.machines || 6;
  const machineData = {};
  for (let i = 0; i < machineCount; i++) {
    machineData[`machine-${i}-${Date.now()}`] = Date.now() - i * 60000;
  }
  await env.REVOKED_LICENSES.put(`activity:machines:${licenseKey}:${hour}`, JSON.stringify(machineData));

  // 5. IP 데이터 추가 (공유 탐지용)
  const ipCount = body.ips || 7;
  const ipData = {};
  for (let i = 0; i < ipCount; i++) {
    ipData[`192.168.${i}.${Math.floor(Math.random() * 255)}`] = Date.now() - i * 60000;
  }
  await env.REVOKED_LICENSES.put(`activity:ips:${licenseKey}:${day}`, JSON.stringify(ipData));

  // 6. 감사 로그
  await logAuditEvent(env, AUDIT_EVENT_TYPES.ANOMALY_DETECTED, {
    license_key_masked: maskLicenseKey(licenseKey),
    countries: countries.length,
    machines: machineCount,
    ips: ipCount,
    test: true
  });

  return new Response(JSON.stringify({
    success: true,
    anomaly_data: {
      license_key: licenseKey,
      countries: countries,
      machines: machineCount,
      ips: ipCount,
      expected_score: 40 + 50  // multi_country + multi_machine
    },
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// 이상 탐지 통계 핸들러
async function handleAnomalyStats(request, env) {
  // 관리자 인증
  const authHeader = request.headers.get('Authorization');
  const adminKey = env.ADMIN_API_KEY;

  if (adminKey && (!authHeader || authHeader !== `Bearer ${adminKey}`)) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Admin API key required'
    }), { status: 401, headers: corsHeaders() });
  }

  // === 이상 탐지된 라이선스 목록 수집 ===
  const anomalies = [];
  let level1_count = 0, level2_count = 0, level3_count = 0, sharing_suspects = 0;

  // 라이선스 목록에서 이상 탐지 분석
  const licenseListData = await env.REVOKED_LICENSES.get('licenses:list');
  const licenseKeys = licenseListData ? JSON.parse(licenseListData) : [];

  for (const key of licenseKeys.slice(0, 50)) {  // 최대 50개 분석
    try {
      const analysis = await analyzeAnomalies(env, key);
      if (analysis.suspicion_score > 0) {
        // anomalies 배열에서 countries/machines 정보 추출
        const multiCountry = analysis.anomalies?.find(a => a.type === 'multi_country');
        const multiMachine = analysis.anomalies?.find(a => a.type === 'multi_machine');

        anomalies.push({
          license_key: key,
          suspicion_score: analysis.suspicion_score,
          countries: multiCountry?.countries?.length || 0,
          machines: multiMachine?.count || 0,
          factors: analysis.anomalies?.map(a => a.type) || []
        });

        // 레벨별 카운트
        if (analysis.suspicion_score >= ANOMALY_THRESHOLDS.SUSPICION_LEVEL_3) {
          level3_count++;
        } else if (analysis.suspicion_score >= ANOMALY_THRESHOLDS.SUSPICION_LEVEL_2) {
          level2_count++;
        } else if (analysis.suspicion_score >= ANOMALY_THRESHOLDS.SUSPICION_LEVEL_1) {
          level1_count++;
        }

        // 공유 의심 (50점 이상)
        if (analysis.suspicion_score >= 50) {
          sharing_suspects++;
        }
      }
    } catch (e) {
      // 분석 실패 무시
    }
  }

  // 점수 높은 순 정렬
  anomalies.sort((a, b) => b.suspicion_score - a.suspicion_score);

  return new Response(JSON.stringify({
    success: true,
    level1_count,
    level2_count,
    level3_count,
    sharing_suspects,
    anomalies: anomalies.slice(0, 20),  // 상위 20개
    thresholds: ANOMALY_THRESHOLDS,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// 특정 라이선스 이상 탐지 분석
async function handleAnalyzeLicense(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed',
      message: 'Use POST method'
    }), { status: 405, headers: corsHeaders() });
  }

  // 관리자 인증
  const authHeader = request.headers.get('Authorization');
  const adminKey = env.ADMIN_API_KEY;

  if (adminKey && (!authHeader || authHeader !== `Bearer ${adminKey}`)) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Admin API key required'
    }), { status: 401, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key } = body;
  if (!license_key) {
    return new Response(JSON.stringify({
      error: 'license_key required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 이상 탐지 분석 실행
  const analysis = await analyzeAnomalies(env, license_key);

  // 일시 정지 상태 확인
  const suspendStatus = await checkSuspended(env, license_key);

  return new Response(JSON.stringify({
    success: true,
    analysis,
    suspended: suspendStatus,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 테스트용 Team 라이선스 생성
 */
async function handleTestTeamLicense(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: corsHeaders()
    });
  }

  const { license_key, tier = 'team' } = body;

  if (!license_key) {
    return new Response(JSON.stringify({ error: 'license_key required' }), {
      status: 400, headers: corsHeaders()
    });
  }

  // 라이선스 정보 저장
  await env.REVOKED_LICENSES.put(`license:${license_key}`, JSON.stringify({
    tier: tier,
    status: 'active',
    created_at: new Date().toISOString(),
    activated_at: new Date().toISOString()
  }));

  // 라이선스 목록에 추가
  const licenseListData = await env.REVOKED_LICENSES.get('licenses:list');
  const licenseList = licenseListData ? JSON.parse(licenseListData) : [];
  if (!licenseList.includes(license_key)) {
    licenseList.unshift(license_key);
    await env.REVOKED_LICENSES.put('licenses:list', JSON.stringify(licenseList.slice(0, 500)));
  }

  return new Response(JSON.stringify({
    success: true,
    license_key,
    tier,
    message: `Test ${tier} license created`
  }), { headers: corsHeaders() });
}

// ============================================================
// 라이선스 관리 API
// ============================================================

// 머신 해제 일일 제한
const DAILY_DEACTIVATION_LIMIT = 3;

/**
 * 라이선스 상태 조회
 */
async function handleLicenseStatus(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key } = body;
  if (!license_key) {
    return new Response(JSON.stringify({
      error: 'license_key required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 환불 체크
  const revoked = await env.REVOKED_LICENSES.get(license_key);
  if (revoked) {
    const revokeData = JSON.parse(revoked);
    return new Response(JSON.stringify({
      status: 'revoked',
      revoked_at: revokeData.revoked_at,
      reason: revokeData.reason
    }), { status: 403, headers: corsHeaders() });
  }

  // Lemon Squeezy 검증
  const validation = await validateLicenseWithLemonSqueezy(license_key);
  if (!validation.valid) {
    return new Response(JSON.stringify({
      status: 'invalid',
      message: 'License validation failed'
    }), { status: 403, headers: corsHeaders() });
  }

  // 티어 정보
  const productName = (validation.meta?.product_name || '').toLowerCase();
  let tier = 'personal';
  if (productName.includes('team')) tier = 'team';
  else if (productName.includes('enterprise')) tier = 'enterprise';

  const concurrentLimit = TIER_CONCURRENT_LIMITS[tier];

  // 등록된 머신 및 활성 세션
  const machineData = await getMachinesForLicense(env, license_key);
  const totalMachines = machineData.machines.length;
  const activeSessions = getActiveSessions(machineData.machines);
  const activeCount = activeSessions.length;

  // 일시 정지 상태
  const suspendStatus = await checkSuspended(env, license_key);

  return new Response(JSON.stringify({
    status: 'valid',
    tier,
    tier_name: tier.charAt(0).toUpperCase() + tier.slice(1),
    concurrent: {
      active: activeCount,
      limit: concurrentLimit > 0 ? concurrentLimit : 'unlimited',
      available: concurrentLimit > 0 ? Math.max(0, concurrentLimit - activeCount) : 'unlimited'
    },
    machines: {
      total_registered: totalMachines,
      active_sessions: activeCount
    },
    suspended: suspendStatus.suspended,
    product_name: validation.meta?.product_name,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 등록된 머신 목록 조회
 */
async function handleListMachines(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key } = body;
  if (!license_key) {
    return new Response(JSON.stringify({
      error: 'license_key required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 환불 체크
  const revoked = await env.REVOKED_LICENSES.get(license_key);
  if (revoked) {
    return new Response(JSON.stringify({
      error: 'License revoked'
    }), { status: 403, headers: corsHeaders() });
  }

  // Lemon Squeezy 검증
  const validation = await validateLicenseWithLemonSqueezy(license_key);
  if (!validation.valid) {
    return new Response(JSON.stringify({
      error: 'Invalid license'
    }), { status: 403, headers: corsHeaders() });
  }

  // 등록된 머신 목록
  const machineData = await getMachinesForLicense(env, license_key);

  // 활성 세션 확인
  const activeSessions = getActiveSessions(machineData.machines);
  const activeIds = new Set(activeSessions.map(m => m.id));

  // 머신 정보 포맷팅 (ID 마스킹 + 활성 상태 표시)
  const machines = machineData.machines.map((m, index) => ({
    index: index + 1,
    machine_id_masked: m.id.substring(0, 8) + '...',
    machine_id_full: m.id,  // 본인 확인용
    registered_at: m.registered_at,
    last_seen: m.last_seen || m.registered_at,
    is_active: activeIds.has(m.id)  // 24시간 이내 활성
  }));

  // 티어 정보
  const productName = (validation.meta?.product_name || '').toLowerCase();
  let tier = 'personal';
  if (productName.includes('team')) tier = 'team';
  else if (productName.includes('enterprise')) tier = 'enterprise';

  const concurrentLimit = TIER_CONCURRENT_LIMITS[tier];

  return new Response(JSON.stringify({
    success: true,
    machines,
    total_registered: machines.length,
    active_sessions: activeSessions.length,
    concurrent_limit: concurrentLimit > 0 ? concurrentLimit : 'unlimited',
    tier,
    note: '등록은 무제한. 동시 사용만 제한됩니다. 24시간 미사용 시 자동으로 비활성화됩니다.',
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 머신 해제 (Self-Service)
 */
async function handleDeactivateMachine(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key, machine_id } = body;
  if (!license_key || !machine_id) {
    return new Response(JSON.stringify({
      error: 'license_key and machine_id required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 환불 체크
  const revoked = await env.REVOKED_LICENSES.get(license_key);
  if (revoked) {
    return new Response(JSON.stringify({
      error: 'License revoked'
    }), { status: 403, headers: corsHeaders() });
  }

  // Lemon Squeezy 검증
  const validation = await validateLicenseWithLemonSqueezy(license_key);
  if (!validation.valid) {
    return new Response(JSON.stringify({
      error: 'Invalid license'
    }), { status: 403, headers: corsHeaders() });
  }

  // 일일 해제 횟수 확인
  const today = new Date().toISOString().split('T')[0];
  const deactivationCountKey = `deactivation:${license_key}:${today}`;
  const countData = await env.REVOKED_LICENSES.get(deactivationCountKey);
  const deactivationCount = countData ? parseInt(countData, 10) : 0;

  if (deactivationCount >= DAILY_DEACTIVATION_LIMIT) {
    return new Response(JSON.stringify({
      error: 'Daily limit exceeded',
      message: `일일 머신 해제 한도(${DAILY_DEACTIVATION_LIMIT}회)를 초과했습니다. 내일 다시 시도하세요.`,
      limit: DAILY_DEACTIVATION_LIMIT,
      used: deactivationCount
    }), { status: 429, headers: corsHeaders() });
  }

  // 머신 목록에서 제거
  const machineData = await getMachinesForLicense(env, license_key);
  const machineIndex = machineData.machines.findIndex(m => m.id === machine_id);

  if (machineIndex === -1) {
    return new Response(JSON.stringify({
      error: 'Machine not found',
      message: '해당 머신이 등록되어 있지 않습니다.'
    }), { status: 404, headers: corsHeaders() });
  }

  // 머신 제거
  machineData.machines.splice(machineIndex, 1);

  // 저장
  const machinesKey = `machines:${license_key}`;
  await env.REVOKED_LICENSES.put(machinesKey, JSON.stringify(machineData));

  // 해제 횟수 증가
  await env.REVOKED_LICENSES.put(deactivationCountKey, (deactivationCount + 1).toString(), {
    expirationTtl: 24 * 60 * 60  // 24시간 후 만료
  });

  // 감사 로그
  await logAuditEvent(env, 'machine_deactivated', {
    license_key_masked: maskLicenseKey(license_key),
    machine_id_masked: machine_id.substring(0, 8) + '...',
    remaining_machines: machineData.machines.length
  });

  return new Response(JSON.stringify({
    success: true,
    message: '머신이 해제되었습니다.',
    remaining_machines: machineData.machines.length,
    deactivations_today: deactivationCount + 1,
    daily_limit: DAILY_DEACTIVATION_LIMIT,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// ============================================================
// 오프라인 토큰 시스템
// ============================================================

// 토큰 유효 기간 (7일)
const TOKEN_VALIDITY_DAYS = 7;

/**
 * HMAC-SHA256 서명 생성
 */
async function createSignature(data, secret) {
  const encoder = new TextEncoder();
  const key = await crypto.subtle.importKey(
    'raw',
    encoder.encode(secret),
    { name: 'HMAC', hash: 'SHA-256' },
    false,
    ['sign']
  );

  const signatureBuffer = await crypto.subtle.sign(
    'HMAC',
    key,
    encoder.encode(data)
  );

  return Array.from(new Uint8Array(signatureBuffer))
    .map(b => b.toString(16).padStart(2, '0'))
    .join('');
}

/**
 * 오프라인 토큰 발급
 */
async function handleTokenIssue(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key, machine_id } = body;
  if (!license_key || !machine_id) {
    return new Response(JSON.stringify({
      error: 'license_key and machine_id required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 환불 체크
  const revoked = await env.REVOKED_LICENSES.get(license_key);
  if (revoked) {
    return new Response(JSON.stringify({
      error: 'License revoked'
    }), { status: 403, headers: corsHeaders() });
  }

  // Lemon Squeezy 검증
  const validation = await validateLicenseWithLemonSqueezy(license_key);
  if (!validation.valid) {
    return new Response(JSON.stringify({
      error: 'Invalid license'
    }), { status: 403, headers: corsHeaders() });
  }

  // 티어 확인
  const productName = (validation.meta?.product_name || '').toLowerCase();
  let tier = 'personal';
  if (productName.includes('team')) tier = 'team';
  else if (productName.includes('enterprise')) tier = 'enterprise';

  // 토큰 데이터 생성
  const now = new Date();
  const expiresAt = new Date(now.getTime() + TOKEN_VALIDITY_DAYS * 24 * 60 * 60 * 1000);

  const tokenData = {
    license_key_hash: await createSignature(license_key, 'clouvel-hash'),
    machine_id,
    tier,
    issued_at: now.toISOString(),
    expires_at: expiresAt.toISOString(),
    version: '1.0'
  };

  // 서명 생성 (TOKEN_SECRET 환경변수 사용, 없으면 기본값)
  const tokenSecret = env.TOKEN_SECRET || 'clouvel-offline-token-secret-v1';
  const dataString = JSON.stringify(tokenData);
  const signature = await createSignature(dataString, tokenSecret);

  // Base64 인코딩
  const token = btoa(JSON.stringify({
    data: tokenData,
    signature
  }));

  // 토큰 발급 기록
  await logAuditEvent(env, 'token_issued', {
    license_key_masked: maskLicenseKey(license_key),
    machine_id_masked: machine_id.substring(0, 8) + '...',
    tier,
    expires_at: expiresAt.toISOString()
  });

  return new Response(JSON.stringify({
    success: true,
    token,
    expires_at: expiresAt.toISOString(),
    validity_days: TOKEN_VALIDITY_DAYS,
    tier,
    message: '오프라인 토큰이 발급되었습니다. 로컬에 안전하게 저장하세요.'
  }), { headers: corsHeaders() });
}

/**
 * 오프라인 토큰 검증 (테스트/디버깅용)
 */
async function handleTokenVerify(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { token, machine_id } = body;
  if (!token) {
    return new Response(JSON.stringify({
      error: 'token required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 토큰 파싱
  let tokenObj;
  try {
    tokenObj = JSON.parse(atob(token));
  } catch (e) {
    return new Response(JSON.stringify({
      valid: false,
      error: 'Invalid token format'
    }), { status: 400, headers: corsHeaders() });
  }

  const { data, signature } = tokenObj;
  if (!data || !signature) {
    return new Response(JSON.stringify({
      valid: false,
      error: 'Malformed token'
    }), { status: 400, headers: corsHeaders() });
  }

  // 서명 검증
  const tokenSecret = env.TOKEN_SECRET || 'clouvel-offline-token-secret-v1';
  const expectedSignature = await createSignature(JSON.stringify(data), tokenSecret);

  if (signature !== expectedSignature) {
    return new Response(JSON.stringify({
      valid: false,
      error: 'Invalid signature'
    }), { status: 403, headers: corsHeaders() });
  }

  // 만료 확인
  const expiresAt = new Date(data.expires_at);
  const now = new Date();

  if (now > expiresAt) {
    return new Response(JSON.stringify({
      valid: false,
      error: 'Token expired',
      expired_at: data.expires_at
    }), { status: 403, headers: corsHeaders() });
  }

  // 머신 ID 확인 (선택적)
  if (machine_id && data.machine_id !== machine_id) {
    return new Response(JSON.stringify({
      valid: false,
      error: 'Machine ID mismatch'
    }), { status: 403, headers: corsHeaders() });
  }

  // 남은 유효 기간 계산
  const remainingMs = expiresAt.getTime() - now.getTime();
  const remainingDays = Math.ceil(remainingMs / (24 * 60 * 60 * 1000));

  return new Response(JSON.stringify({
    valid: true,
    tier: data.tier,
    machine_id: data.machine_id,
    issued_at: data.issued_at,
    expires_at: data.expires_at,
    remaining_days: remainingDays,
    timestamp: now.toISOString()
  }), { headers: corsHeaders() });
}

// ============================================================
// 관리자 대시보드 API
// ============================================================

/**
 * 관리자 인증 확인
 */
function checkAdminAuth(request, env) {
  const authHeader = request.headers.get('Authorization');
  const adminKey = env.ADMIN_API_KEY;

  // ADMIN_API_KEY가 설정되지 않으면 모두 허용 (개발용)
  if (!adminKey) return { authorized: true, warning: 'ADMIN_API_KEY not set' };

  if (!authHeader || authHeader !== `Bearer ${adminKey}`) {
    return { authorized: false };
  }

  return { authorized: true };
}

/**
 * 관리자 대시보드 - 전체 통계
 */
async function handleAdminDashboard(request, env) {
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Admin API key required'
    }), { status: 401, headers: corsHeaders() });
  }

  const today = new Date().toISOString().split('T')[0];

  // 오늘 감사 통계
  const auditStatsKey = `audit:stats:${today}`;
  const auditStatsData = await env.REVOKED_LICENSES.get(auditStatsKey);
  const todayAuditStats = auditStatsData ? JSON.parse(auditStatsData) : {};

  // === 라이선스 목록 수집 ===
  const licenses = [];
  const licenseListData = await env.REVOKED_LICENSES.get('licenses:list');
  const licenseKeys = licenseListData ? JSON.parse(licenseListData) : [];

  for (const key of licenseKeys.slice(0, 100)) {  // 최대 100개
    const licenseData = await env.REVOKED_LICENSES.get(`license:${key}`);
    if (licenseData) {
      const license = JSON.parse(licenseData);
      licenses.push({
        license_key: key,
        tier: license.tier || 'personal',
        status: license.status || 'active',
        machines: license.machines?.length || 0,
        last_active: license.last_active || license.activated_at,
        activated_at: license.activated_at
      });
    }
  }

  // === 환불 목록 수집 ===
  const refunds = [];
  const refundListData = await env.REVOKED_LICENSES.get('refunds:list');
  const refundKeys = refundListData ? JSON.parse(refundListData) : [];

  for (const key of refundKeys.slice(0, 50)) {  // 최대 50개
    const refundData = await env.REVOKED_LICENSES.get(`refund:${key}`);
    if (refundData) {
      refunds.push(JSON.parse(refundData));
    }
  }

  // === 최근 이벤트 수집 ===
  const recent_events = [];
  for (const eventType of Object.values(AUDIT_EVENT_TYPES)) {
    const listKey = `audit:${eventType}:list`;
    const listData = await env.REVOKED_LICENSES.get(listKey);

    if (listData) {
      const eventIds = JSON.parse(listData).slice(0, 5);
      for (const eventId of eventIds) {
        const eventKey = `audit:event:${eventId}`;
        const eventData = await env.REVOKED_LICENSES.get(eventKey);
        if (eventData) {
          recent_events.push(JSON.parse(eventData));
        }
      }
    }
  }

  // 시간순 정렬
  recent_events.sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  // === 통계 계산 ===
  const stats = {
    total: licenses.length,
    active: licenses.filter(l => l.status === 'active').length,
    blocked: licenses.filter(l => l.status === 'blocked').length,
    suspended: licenses.filter(l => l.status === 'suspended').length,
    refunded: refunds.length,
    requests_24h: todayAuditStats.total_requests || 0,
    anomalies_24h: todayAuditStats.anomaly_detected || 0
  };

  // 시스템 정보
  const systemInfo = {
    version: '4.0.0',  // Week 4
    content_version: PREMIUM_CONTENT.version,
    premium_unlock_days: PREMIUM_UNLOCK_DAYS,
    token_validity_days: TOKEN_VALIDITY_DAYS,
    offline_grace_days: OFFLINE_GRACE_PERIOD_SECONDS / (24 * 60 * 60)
  };

  return new Response(JSON.stringify({
    success: true,
    stats,
    licenses,
    refunds,
    recent_events: recent_events.slice(0, 20),
    dashboard: {
      date: today,
      audit_stats: todayAuditStats,
      anomaly_thresholds: ANOMALY_THRESHOLDS,
      rate_limits: RATE_LIMITS,
      system: systemInfo
    },
    warning: auth.warning || null,
    generated_at: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 관리자 - 라이선스/IP 차단
 */
async function handleAdminBlock(request, env) {
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized'
    }), { status: 401, headers: corsHeaders() });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { type, target, reason, duration_hours } = body;

  if (!type || !target) {
    return new Response(JSON.stringify({
      error: 'type and target required',
      valid_types: ['license', 'ip']
    }), { status: 400, headers: corsHeaders() });
  }

  const blockReason = reason || 'admin_block';
  const durationSeconds = (duration_hours || 24) * 60 * 60;

  let blockKey;
  if (type === 'license') {
    blockKey = `suspended:${target}`;
  } else if (type === 'ip') {
    blockKey = `blocked:${target}`;
  } else {
    return new Response(JSON.stringify({
      error: 'Invalid type',
      valid_types: ['license', 'ip']
    }), { status: 400, headers: corsHeaders() });
  }

  await env.REVOKED_LICENSES.put(blockKey, JSON.stringify({
    blocked_at: new Date().toISOString(),
    reason: blockReason,
    blocked_by: 'admin',
    duration_hours: duration_hours || 24
  }), {
    expirationTtl: durationSeconds
  });

  // 라이선스 목록에 추가 (대시보드용)
  if (type === 'license') {
    const licenseListData = await env.REVOKED_LICENSES.get('licenses:list');
    const licenseList = licenseListData ? JSON.parse(licenseListData) : [];
    if (!licenseList.includes(target)) {
      licenseList.unshift(target);
      await env.REVOKED_LICENSES.put('licenses:list', JSON.stringify(licenseList.slice(0, 500)));
    }

    // 라이선스 상세 정보 저장
    await env.REVOKED_LICENSES.put(`license:${target}`, JSON.stringify({
      tier: 'personal',
      status: 'blocked',
      blocked_at: new Date().toISOString(),
      reason: blockReason
    }));
  }

  // 감사 로그
  await logAuditEvent(env, 'admin_block', {
    type,
    target: type === 'license' ? maskLicenseKey(target) : target.substring(0, 10) + '...',
    reason: blockReason,
    duration_hours: duration_hours || 24
  });

  return new Response(JSON.stringify({
    success: true,
    blocked: {
      type,
      target: type === 'license' ? maskLicenseKey(target) : target.substring(0, 10) + '...',
      reason: blockReason,
      expires_in_hours: duration_hours || 24
    },
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 관리자 - 차단 해제
 */
async function handleAdminUnblock(request, env) {
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized'
    }), { status: 401, headers: corsHeaders() });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { type, target } = body;

  if (!type || !target) {
    return new Response(JSON.stringify({
      error: 'type and target required'
    }), { status: 400, headers: corsHeaders() });
  }

  let blockKey;
  if (type === 'license') {
    blockKey = `suspended:${target}`;
  } else if (type === 'ip') {
    blockKey = `blocked:${target}`;
  } else {
    return new Response(JSON.stringify({
      error: 'Invalid type'
    }), { status: 400, headers: corsHeaders() });
  }

  // 차단 해제
  await env.REVOKED_LICENSES.delete(blockKey);

  // 라이선스 상태 업데이트 (대시보드용)
  if (type === 'license') {
    const existingData = await env.REVOKED_LICENSES.get(`license:${target}`);
    const licenseInfo = existingData ? JSON.parse(existingData) : { tier: 'personal' };
    await env.REVOKED_LICENSES.put(`license:${target}`, JSON.stringify({
      ...licenseInfo,
      status: 'active',
      unblocked_at: new Date().toISOString()
    }));
  }

  // 감사 로그
  await logAuditEvent(env, 'admin_unblock', {
    type,
    target: type === 'license' ? maskLicenseKey(target) : target.substring(0, 10) + '...'
  });

  return new Response(JSON.stringify({
    success: true,
    unblocked: {
      type,
      target: type === 'license' ? maskLicenseKey(target) : target.substring(0, 10) + '...'
    },
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 일일 보안 리포트 생성 및 Discord 전송
 */
async function handleDailyReport(request, env) {
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized'
    }), { status: 401, headers: corsHeaders() });
  }

  const today = new Date().toISOString().split('T')[0];
  const yesterday = new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString().split('T')[0];

  // 오늘 감사 통계
  const auditStatsKey = `audit:stats:${today}`;
  const auditStatsData = await env.REVOKED_LICENSES.get(auditStatsKey);
  const todayStats = auditStatsData ? JSON.parse(auditStatsData) : {};

  // 어제 감사 통계 (비교용)
  const yesterdayStatsKey = `audit:stats:${yesterday}`;
  const yesterdayStatsData = await env.REVOKED_LICENSES.get(yesterdayStatsKey);
  const yesterdayStats = yesterdayStatsData ? JSON.parse(yesterdayStatsData) : {};

  // 리포트 데이터 구성
  const report = {
    date: today,
    summary: {
      total_events: todayStats.total || 0,
      auth_failures: todayStats.auth_failure || 0,
      rate_limited: todayStats.rate_limited || 0,
      brute_force_blocked: todayStats.brute_force || 0,
      revoked_access_attempts: todayStats.revoked_access || 0,
      anomalies_detected: todayStats.anomaly_detected || 0
    },
    comparison: {
      total_change: (todayStats.total || 0) - (yesterdayStats.total || 0),
      auth_failures_change: (todayStats.auth_failure || 0) - (yesterdayStats.auth_failure || 0)
    }
  };

  // Discord로 전송 (옵션)
  const url = new URL(request.url);
  const sendDiscord = url.searchParams.get('send') === 'true';

  if (sendDiscord && env.DISCORD_WEBHOOK_URL) {
    await sendSecurityAlert(env.DISCORD_WEBHOOK_URL, {
      type: 'daily_report',
      total_requests: report.summary.total_events,
      blocked_count: report.summary.brute_force_blocked + report.summary.rate_limited,
      message: `인증 실패: ${report.summary.auth_failures} | 이상 탐지: ${report.summary.anomalies_detected} | 환불 시도: ${report.summary.revoked_access_attempts}`
    });
  }

  return new Response(JSON.stringify({
    success: true,
    report,
    discord_sent: sendDiscord,
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

/**
 * 라이선스 공유 의심 탐지
 */
async function handleCheckLicenseSharing(request, env) {
  const auth = checkAdminAuth(request, env);
  if (!auth.authorized) {
    return new Response(JSON.stringify({
      error: 'Unauthorized'
    }), { status: 401, headers: corsHeaders() });
  }

  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key } = body;

  if (!license_key) {
    return new Response(JSON.stringify({
      error: 'license_key required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 활동 데이터 조회
  const activityKey = `activity:${license_key}`;
  const activityData = await env.REVOKED_LICENSES.get(activityKey);

  if (!activityData) {
    return new Response(JSON.stringify({
      success: true,
      sharing_suspected: false,
      message: 'No activity data found'
    }), { headers: corsHeaders() });
  }

  const activity = JSON.parse(activityData);

  // 공유 의심 분석
  const sharingIndicators = [];
  let sharingScore = 0;

  // 1. 24시간 내 다른 IP 수 확인
  const uniqueIps = new Set();
  const uniqueCountries = new Set();
  const now = Date.now();
  const dayAgo = now - 24 * 60 * 60 * 1000;

  if (activity.recent_ips) {
    for (const [ip, timestamp] of Object.entries(activity.recent_ips)) {
      if (new Date(timestamp).getTime() > dayAgo) {
        uniqueIps.add(ip);
      }
    }
  }

  if (activity.countries) {
    for (const [country, timestamp] of Object.entries(activity.countries)) {
      if (new Date(timestamp).getTime() > dayAgo) {
        uniqueCountries.add(country);
      }
    }
  }

  // 5개 이상 고유 IP = 의심
  if (uniqueIps.size >= 5) {
    sharingScore += 40;
    sharingIndicators.push({
      type: 'multiple_ips',
      detail: `24시간 내 ${uniqueIps.size}개 고유 IP 접속`,
      count: uniqueIps.size
    });
  }

  // 3개 이상 국가 = 의심
  if (uniqueCountries.size >= 3) {
    sharingScore += 50;
    sharingIndicators.push({
      type: 'multiple_countries',
      detail: `24시간 내 ${uniqueCountries.size}개국 접속`,
      countries: Array.from(uniqueCountries)
    });
  }

  // 머신 등록 확인
  const machineData = await getMachinesForLicense(env, license_key);
  const activeSessions = getActiveSessions(machineData.machines);

  if (activeSessions.length >= 3) {
    sharingScore += 30;
    sharingIndicators.push({
      type: 'multiple_machines',
      detail: `동시 활성 세션 ${activeSessions.length}개`,
      count: activeSessions.length
    });
  }

  const sharingSuspected = sharingScore >= 50;

  // Discord 알림 (의심도 높을 경우)
  if (sharingSuspected && env.DISCORD_WEBHOOK_URL) {
    await sendSecurityAlert(env.DISCORD_WEBHOOK_URL, {
      type: 'license_sharing',
      license_key_masked: maskLicenseKey(license_key),
      unique_ips: uniqueIps.size,
      countries: Array.from(uniqueCountries),
      anomalies: sharingIndicators,
      suspicion_score: sharingScore,
      action: sharingScore >= 70 ? '자동 모니터링 강화' : '수동 확인 권장'
    });
  }

  return new Response(JSON.stringify({
    success: true,
    license_key_masked: maskLicenseKey(license_key),
    sharing_suspected: sharingSuspected,
    sharing_score: sharingScore,
    indicators: sharingIndicators,
    stats: {
      unique_ips_24h: uniqueIps.size,
      unique_countries_24h: uniqueCountries.size,
      active_sessions: activeSessions.length
    },
    timestamp: new Date().toISOString()
  }), { headers: corsHeaders() });
}

// 감사 로그 통계 핸들러
async function handleAuditStats(request, env) {
  // 관리자 인증 (간단한 API Key 방식)
  const authHeader = request.headers.get('Authorization');
  const adminKey = env.ADMIN_API_KEY;  // 환경 변수로 설정

  // 인증이 설정되어 있고 헤더가 없거나 맞지 않으면 거부
  if (adminKey && (!authHeader || authHeader !== `Bearer ${adminKey}`)) {
    return new Response(JSON.stringify({
      error: 'Unauthorized',
      message: 'Admin API key required'
    }), { status: 401, headers: corsHeaders() });
  }

  const url = new URL(request.url);
  const days = parseInt(url.searchParams.get('days') || '7', 10);

  try {
    const stats = await getAuditStats(env, Math.min(days, 30));  // 최대 30일

    return new Response(JSON.stringify({
      success: true,
      generated_at: new Date().toISOString(),
      ...stats
    }), { headers: corsHeaders() });
  } catch (error) {
    return new Response(JSON.stringify({
      error: 'Failed to get audit stats',
      message: error.message
    }), { status: 500, headers: corsHeaders() });
  }
}

// ============================================================
// Heartbeat API (신규)
// ============================================================

// 오프라인 유예 기간 (초)
const OFFLINE_GRACE_PERIOD_SECONDS = 3 * 24 * 60 * 60;  // 3일

/**
 * Heartbeat 핸들러
 * - 라이선스 상태 확인
 * - 마지막 heartbeat 시간 기록
 * - 환불 여부 즉시 반영
 */
async function handleHeartbeat(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({
      error: 'Method not allowed',
      message: 'Use POST method'
    }), { status: 405, headers: corsHeaders() });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON',
      message: 'Request body must be valid JSON'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key, machine_id, client_version } = body;

  if (!license_key) {
    return new Response(JSON.stringify({
      error: 'Missing license_key',
      message: 'license_key is required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 1. 환불/취소 체크
  const revoked = await env.REVOKED_LICENSES.get(license_key);
  if (revoked) {
    const revokeData = JSON.parse(revoked);
    return new Response(JSON.stringify({
      status: 'revoked',
      revoked_at: revokeData.revoked_at,
      reason: revokeData.reason,
      message: '라이선스가 취소되었습니다.'
    }), { status: 403, headers: corsHeaders() });
  }

  // 2. Lemon Squeezy 실시간 검증
  const lsResult = await validateLicenseWithLemonSqueezy(license_key);
  if (!lsResult.valid) {
    return new Response(JSON.stringify({
      status: 'invalid',
      message: '유효하지 않은 라이선스입니다.'
    }), { status: 403, headers: corsHeaders() });
  }

  // 3. Machine ID 처리 (동시 사용 방식 - 등록 무제한, Heartbeat로 last_seen 업데이트)
  if (machine_id) {
    const tier = lsResult.meta?.variant_name?.toLowerCase() || 'personal';
    // 머신 등록 및 last_seen 업데이트 (등록은 무제한)
    await registerMachineForLicense(env, license_key, machine_id, tier);
  }

  // 4. Heartbeat 기록
  const heartbeatKey = `heartbeat:${license_key}`;
  const now = new Date().toISOString();

  await env.REVOKED_LICENSES.put(heartbeatKey, JSON.stringify({
    last_heartbeat: now,
    machine_id: machine_id || null,
    client_version: client_version || null,
    ip: request.headers.get('CF-Connecting-IP') || 'unknown'
  }), {
    expirationTtl: OFFLINE_GRACE_PERIOD_SECONDS * 2  // 유예기간의 2배 후 자동 삭제
  });

  // 5. 성공 응답
  return new Response(JSON.stringify({
    status: 'valid',
    timestamp: now,
    next_heartbeat_seconds: 24 * 60 * 60,  // 24시간 후
    offline_grace_seconds: OFFLINE_GRACE_PERIOD_SECONDS,
    tier: lsResult.meta?.variant_name || 'personal',
    features: {
      premium_unlocked: true,  // Heartbeat는 7일 후에만 가능하므로 항상 true
      rate_limiting: true,
      machine_binding: true
    }
  }), { headers: corsHeaders() });
}

/**
 * 마지막 Heartbeat 시간 조회
 */
async function getLastHeartbeat(env, licenseKey) {
  const key = `heartbeat:${licenseKey}`;
  const data = await env.REVOKED_LICENSES.get(key);
  if (!data) return null;

  try {
    return JSON.parse(data);
  } catch {
    return null;
  }
}

// ============================================================
// 콘텐츠 API (신규)
// ============================================================

// 콘텐츠 매니페스트 (목록만, 내용 없음)
async function handleContentManifest(request, env) {
  // 라이선스 검증 (기본만, 7일 체크 안함)
  const authHeader = request.headers.get('Authorization');
  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return new Response(JSON.stringify({
      error: 'Missing license key',
      message: 'Authorization: Bearer YOUR_LICENSE_KEY'
    }), { status: 401, headers: corsHeaders() });
  }

  const licenseKey = authHeader.replace('Bearer ', '').trim();

  // 환불 체크
  const revoked = await env.REVOKED_LICENSES.get(licenseKey);
  if (revoked) {
    // 환불된 라이선스 사용 시도 감사 로그
    logAuditEvent(env, AUDIT_EVENT_TYPES.REVOKED_ACCESS, {
      license_key_masked: maskLicenseKey(licenseKey),
      endpoint: '/content/manifest'
    }).catch(console.error);

    return new Response(JSON.stringify({
      error: 'License revoked',
      message: '라이선스가 환불로 차단되었습니다.'
    }), { status: 403, headers: corsHeaders() });
  }

  // Lemon Squeezy 검증
  const validation = await validateLicenseWithLemonSqueezy(licenseKey);
  if (!validation.valid) {
    return new Response(JSON.stringify({
      error: 'Invalid license',
      message: '유효하지 않은 라이선스입니다.'
    }), { status: 403, headers: corsHeaders() });
  }

  // 매니페스트 반환 (내용 없이 목록만)
  return new Response(JSON.stringify({
    version: PREMIUM_CONTENT.version,
    updated_at: PREMIUM_CONTENT.updated_at,
    commands: Object.keys(PREMIUM_CONTENT.commands),
    templates: Object.keys(PREMIUM_CONTENT.templates),
    config: Object.keys(PREMIUM_CONTENT.config),
    premium_unlock_days: PREMIUM_UNLOCK_DAYS
  }), { headers: corsHeaders() });
}

// 티어별 동시 사용 제한 (등록은 무제한, 동시 사용만 제한)
const TIER_CONCURRENT_LIMITS = {
  personal: 1,   // 동시 1대
  team: 10,      // 동시 10대
  enterprise: -1 // 무제한
};

// 활성 세션 판단 기준 (24시간)
const ACTIVE_SESSION_HOURS = 24;

// 활성 세션 목록 조회 (24시간 이내 last_seen)
function getActiveSessions(machines) {
  const now = new Date();
  const cutoff = new Date(now.getTime() - ACTIVE_SESSION_HOURS * 60 * 60 * 1000);

  return machines.filter(m => {
    if (!m.last_seen) return false;
    const lastSeen = new Date(m.last_seen);
    return lastSeen > cutoff;
  });
}

// 라이선스의 등록된 머신 목록 조회
async function getMachinesForLicense(env, licenseKey) {
  const key = `machines:${licenseKey}`;
  const data = await env.REVOKED_LICENSES.get(key);
  if (data) {
    return JSON.parse(data);
  }
  return { machines: [], tier: 'personal' };
}

// 라이선스에 머신 등록
async function registerMachineForLicense(env, licenseKey, machineId, tier) {
  const key = `machines:${licenseKey}`;
  const existing = await getMachinesForLicense(env, licenseKey);

  // 이미 등록된 머신인지 확인
  const existingMachine = existing.machines.find(m => m.id === machineId);
  if (existingMachine) {
    // 마지막 접근 시간 업데이트
    existingMachine.last_seen = new Date().toISOString();
  } else {
    // 새 머신 추가
    existing.machines.push({
      id: machineId,
      registered_at: new Date().toISOString(),
      last_seen: new Date().toISOString()
    });
  }

  existing.tier = tier;

  await env.REVOKED_LICENSES.put(key, JSON.stringify(existing));
  return existing;
}

// 콘텐츠 번들 (전체 내용)
async function handleContentBundle(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method must be POST' }), {
      status: 405,
      headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({
      error: 'Invalid JSON body',
      message: 'Request body must be JSON with license_key, activated_at, machine_id'
    }), { status: 400, headers: corsHeaders() });
  }

  const { license_key, activated_at, machine_id, client_version } = body;

  // 클라이언트 버전 검증
  const versionCheck = validateClientVersion(client_version);
  if (!versionCheck.valid) {
    return new Response(JSON.stringify({
      error: 'Client version not allowed',
      ...versionCheck
    }), { status: 403, headers: corsHeaders() });
  }

  if (!license_key) {
    return new Response(JSON.stringify({
      error: 'Missing license_key',
      message: 'license_key is required'
    }), { status: 400, headers: corsHeaders() });
  }

  if (!machine_id) {
    return new Response(JSON.stringify({
      error: 'Missing machine_id',
      message: 'machine_id is required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 1. 환불 체크
  const revoked = await env.REVOKED_LICENSES.get(license_key);
  if (revoked) {
    // 환불된 라이선스 사용 시도 감사 로그
    logAuditEvent(env, AUDIT_EVENT_TYPES.REVOKED_ACCESS, {
      license_key_masked: maskLicenseKey(license_key),
      machine_id: machine_id?.substring(0, 8) + '...',
      endpoint: '/content/bundle'
    }).catch(console.error);

    return new Response(JSON.stringify({
      error: 'License revoked',
      message: '라이선스가 환불로 차단되었습니다.',
      revoked: true
    }), { status: 403, headers: corsHeaders() });
  }

  // 1.5. 일시 정지 상태 확인
  const suspendStatus = await checkSuspended(env, license_key);
  if (suspendStatus.suspended) {
    return new Response(JSON.stringify({
      error: 'License suspended',
      message: '이상 활동으로 인해 일시 정지되었습니다. 잠시 후 다시 시도하세요.',
      suspended_at: suspendStatus.suspended_at,
      reason: suspendStatus.reason
    }), { status: 403, headers: corsHeaders() });
  }

  // 2. Lemon Squeezy 검증
  const validation = await validateLicenseWithLemonSqueezy(license_key);
  if (!validation.valid) {
    return new Response(JSON.stringify({
      error: 'Invalid license',
      message: '유효하지 않은 라이선스입니다.'
    }), { status: 403, headers: corsHeaders() });
  }

  // 2.5. 활동 기록 및 이상 탐지 (비동기)
  const clientIP = request.headers.get('CF-Connecting-IP') || 'unknown';
  const country = request.cf?.country || null;

  recordUserActivity(env, license_key, {
    ip: clientIP,
    machineId: machine_id,
    endpoint: '/content/bundle',
    country
  }).then(() => {
    // 이상 탐지 분석 (백그라운드)
    return analyzeAnomalies(env, license_key);
  }).then(analysis => {
    // 이상 징후 대응 (백그라운드)
    if (analysis.suspicion_level > 0) {
      return handleAnomalyResponse(env, license_key, analysis);
    }
  }).catch(console.error);

  // 티어 추출
  const productName = (validation.meta?.product_name || '').toLowerCase();
  let tier = 'personal';
  if (productName.includes('team')) tier = 'team';
  else if (productName.includes('enterprise')) tier = 'enterprise';

  const concurrentLimit = TIER_CONCURRENT_LIMITS[tier];

  // 3. Machine ID 검증 (동시 사용 제한 - 등록은 무제한)
  const machineData = await getMachinesForLicense(env, license_key);
  const isRegistered = machineData.machines.some(m => m.id === machine_id);

  // 활성 세션 확인 (24시간 이내 last_seen)
  const activeSessions = getActiveSessions(machineData.machines);
  const isCurrentMachineActive = activeSessions.some(m => m.id === machine_id);

  // 동시 사용 제한 확인 (새 머신이고, 활성 세션이 제한에 도달한 경우)
  if (!isCurrentMachineActive && concurrentLimit > 0 && activeSessions.length >= concurrentLimit) {
    // 동시 사용 초과 - 가장 오래된 활성 세션 정보 제공
    const oldestSession = activeSessions.sort((a, b) =>
      new Date(a.last_seen) - new Date(b.last_seen)
    )[0];

    return new Response(JSON.stringify({
      error: 'Concurrent limit exceeded',
      message: `${tier.toUpperCase()} 티어는 동시에 ${concurrentLimit}대만 사용 가능합니다. 다른 기기에서 사용을 중지하면 자동으로 해제됩니다.`,
      tier: tier,
      concurrent_limit: concurrentLimit,
      active_sessions: activeSessions.length,
      active_machines: activeSessions.map(m => ({
        id: m.id.substring(0, 8) + '...',
        last_seen: m.last_seen
      })),
      hint: `다른 기기에서 24시간 동안 사용하지 않으면 자동으로 슬롯이 해제됩니다.`
    }), { status: 403, headers: corsHeaders() });
  }

  // 4. 7일 잠금 체크
  if (!activated_at) {
    return new Response(JSON.stringify({
      error: 'Missing activated_at',
      message: 'activated_at is required for premium content'
    }), { status: 400, headers: corsHeaders() });
  }

  const activatedDate = new Date(activated_at);
  const now = new Date();
  const daysSinceActivation = Math.floor((now - activatedDate) / (1000 * 60 * 60 * 24));

  if (daysSinceActivation < PREMIUM_UNLOCK_DAYS) {
    const remaining = PREMIUM_UNLOCK_DAYS - daysSinceActivation;
    return new Response(JSON.stringify({
      error: 'Premium locked',
      message: `프리미엄 기능은 활성화 후 ${PREMIUM_UNLOCK_DAYS}일이 지나야 사용할 수 있습니다.`,
      days_since_activation: daysSinceActivation,
      days_remaining: remaining,
      unlock_date: new Date(activatedDate.getTime() + PREMIUM_UNLOCK_DAYS * 24 * 60 * 60 * 1000).toISOString()
    }), { status: 403, headers: corsHeaders() });
  }

  // 5. 머신 등록 (성공 시)
  await registerMachineForLicense(env, license_key, machine_id, tier);

  // 5.5. 라이선스 목록에 추가 (대시보드용)
  const licenseListData = await env.REVOKED_LICENSES.get('licenses:list');
  const licenseList = licenseListData ? JSON.parse(licenseListData) : [];
  if (!licenseList.includes(license_key)) {
    licenseList.unshift(license_key);  // 최신순
    await env.REVOKED_LICENSES.put('licenses:list', JSON.stringify(licenseList.slice(0, 500)));
  }

  // 라이선스 상세 정보 저장/업데이트
  const existingLicense = await env.REVOKED_LICENSES.get(`license:${license_key}`);
  const licenseInfo = existingLicense ? JSON.parse(existingLicense) : {};
  await env.REVOKED_LICENSES.put(`license:${license_key}`, JSON.stringify({
    ...licenseInfo,
    tier,
    status: 'active',
    last_active: new Date().toISOString(),
    activated_at: licenseInfo.activated_at || activated_at,
    machines: machineData.machines.map(m => m.id)
  }));

  // 6. 콘텐츠 반환
  return new Response(JSON.stringify({
    success: true,
    version: PREMIUM_CONTENT.version,
    updated_at: PREMIUM_CONTENT.updated_at,
    tier: tier,
    machine_id: machine_id.substring(0, 8) + '...',
    content: {
      claude_md: PREMIUM_CONTENT.claude_md,
      commands: PREMIUM_CONTENT.commands,
      templates: PREMIUM_CONTENT.templates,
      config: PREMIUM_CONTENT.config,
      settings: PREMIUM_CONTENT.settings
    }
  }), { headers: corsHeaders() });
}

// ============================================================
// Team API (Phase 4)
// ============================================================

/**
 * 팀 라이선스 검증 (Team 티어인지 확인)
 */
async function verifyTeamLicense(env, licenseKey) {
  // 라이선스 정보 조회
  const licenseData = await env.REVOKED_LICENSES.get(`license:${licenseKey}`);
  if (!licenseData) {
    return { valid: false, error: 'License not found' };
  }

  const license = JSON.parse(licenseData);

  // Team 또는 Enterprise 티어 확인
  if (!['team', 'enterprise'].includes(license.tier)) {
    return { valid: false, error: 'Team license required', tier: license.tier };
  }

  // 활성 상태 확인
  if (license.status !== 'active') {
    return { valid: false, error: 'License not active', status: license.status };
  }

  return { valid: true, license };
}

/**
 * 팀 데이터 조회/생성
 */
async function getTeamData(env, licenseKey) {
  const teamKey = `team:${licenseKey}`;
  const data = await env.TEAM_DATA.get(teamKey);

  if (data) {
    return JSON.parse(data);
  }

  // 기본 팀 구조 생성
  return {
    owner: null,
    members: [],
    settings: {
      enabled_roles: {
        cto: true,
        cdo: true,
        cpo: true,
        cfo: true,
        cmo: true
      }
    },
    max_seats: 10,
    created_at: new Date().toISOString()
  };
}

/**
 * 팀 데이터 저장
 */
async function saveTeamData(env, licenseKey, teamData) {
  const teamKey = `team:${licenseKey}`;
  teamData.updated_at = new Date().toISOString();
  await env.TEAM_DATA.put(teamKey, JSON.stringify(teamData));
}

/**
 * 팀 멤버 초대
 */
async function handleTeamInvite(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: corsHeaders()
    });
  }

  const { license_key, requester_email, invite_email, role = 'member' } = body;

  if (!license_key || !requester_email || !invite_email) {
    return new Response(JSON.stringify({
      error: 'license_key, requester_email, invite_email required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, license_key);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  // 팀 데이터 조회
  const teamData = await getTeamData(env, license_key);

  // 오너 설정 (첫 번째 요청자가 오너)
  if (!teamData.owner) {
    teamData.owner = requester_email;
    teamData.members.push({
      email: requester_email,
      role: 'admin',
      joined_at: new Date().toISOString()
    });
  }

  // Admin 권한 확인
  const requester = teamData.members.find(m => m.email === requester_email);
  if (!requester || requester.role !== 'admin') {
    return new Response(JSON.stringify({
      error: 'Admin permission required'
    }), { status: 403, headers: corsHeaders() });
  }

  // 시트 제한 확인
  if (teamData.members.length >= teamData.max_seats) {
    return new Response(JSON.stringify({
      error: 'Seat limit reached',
      max_seats: teamData.max_seats,
      current: teamData.members.length
    }), { status: 400, headers: corsHeaders() });
  }

  // 이미 멤버인지 확인
  if (teamData.members.find(m => m.email === invite_email)) {
    return new Response(JSON.stringify({
      error: 'Already a member'
    }), { status: 400, headers: corsHeaders() });
  }

  // 멤버 추가
  teamData.members.push({
    email: invite_email,
    role: role === 'admin' ? 'admin' : 'member',
    invited_by: requester_email,
    joined_at: new Date().toISOString()
  });

  await saveTeamData(env, license_key, teamData);

  // 감사 로그
  await logAuditEvent(env, 'team_invite', {
    license_key_masked: maskLicenseKey(license_key),
    inviter: requester_email,
    invitee: invite_email,
    role
  });

  return new Response(JSON.stringify({
    success: true,
    message: `${invite_email} invited as ${role}`,
    members_count: teamData.members.length,
    seats_remaining: teamData.max_seats - teamData.members.length
  }), { headers: corsHeaders() });
}

/**
 * 팀 멤버 목록 조회
 */
async function handleTeamMembers(request, env) {
  const url = new URL(request.url);
  const licenseKey = url.searchParams.get('license_key');

  if (!licenseKey) {
    return new Response(JSON.stringify({ error: 'license_key required' }), {
      status: 400, headers: corsHeaders()
    });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, licenseKey);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  const teamData = await getTeamData(env, licenseKey);

  return new Response(JSON.stringify({
    success: true,
    owner: teamData.owner,
    members: teamData.members.map(m => ({
      email: m.email,
      role: m.role,
      joined_at: m.joined_at
    })),
    seats: {
      used: teamData.members.length,
      max: teamData.max_seats,
      remaining: teamData.max_seats - teamData.members.length
    }
  }), { headers: corsHeaders() });
}

/**
 * 팀 멤버 제거
 */
async function handleTeamRemove(request, env) {
  if (request.method !== 'POST' && request.method !== 'DELETE') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: corsHeaders()
    });
  }

  const { license_key, requester_email, target_email } = body;

  if (!license_key || !requester_email || !target_email) {
    return new Response(JSON.stringify({
      error: 'license_key, requester_email, target_email required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, license_key);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  const teamData = await getTeamData(env, license_key);

  // 본인 탈퇴 또는 Admin 권한 확인
  const requester = teamData.members.find(m => m.email === requester_email);
  const isSelfRemove = requester_email === target_email;

  if (!isSelfRemove) {
    if (!requester || requester.role !== 'admin') {
      return new Response(JSON.stringify({
        error: 'Admin permission required (or remove yourself)'
      }), { status: 403, headers: corsHeaders() });
    }
  }

  // 오너는 제거 불가
  if (target_email === teamData.owner) {
    return new Response(JSON.stringify({
      error: 'Cannot remove team owner'
    }), { status: 400, headers: corsHeaders() });
  }

  // 멤버 제거
  const memberIndex = teamData.members.findIndex(m => m.email === target_email);
  if (memberIndex === -1) {
    return new Response(JSON.stringify({ error: 'Member not found' }), {
      status: 404, headers: corsHeaders()
    });
  }

  teamData.members.splice(memberIndex, 1);
  await saveTeamData(env, license_key, teamData);

  // 감사 로그
  await logAuditEvent(env, 'team_remove', {
    license_key_masked: maskLicenseKey(license_key),
    remover: requester_email,
    removed: target_email,
    self_remove: isSelfRemove
  });

  return new Response(JSON.stringify({
    success: true,
    message: `${target_email} removed from team`,
    members_count: teamData.members.length
  }), { headers: corsHeaders() });
}

/**
 * 팀 멤버 역할 변경
 */
async function handleTeamRole(request, env) {
  if (request.method !== 'PUT' && request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: corsHeaders()
    });
  }

  const { license_key, requester_email, target_email, new_role } = body;

  if (!license_key || !requester_email || !target_email || !new_role) {
    return new Response(JSON.stringify({
      error: 'license_key, requester_email, target_email, new_role required'
    }), { status: 400, headers: corsHeaders() });
  }

  if (!['admin', 'member'].includes(new_role)) {
    return new Response(JSON.stringify({
      error: 'Invalid role. Use: admin, member'
    }), { status: 400, headers: corsHeaders() });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, license_key);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  const teamData = await getTeamData(env, license_key);

  // Admin 권한 확인
  const requester = teamData.members.find(m => m.email === requester_email);
  if (!requester || requester.role !== 'admin') {
    return new Response(JSON.stringify({
      error: 'Admin permission required'
    }), { status: 403, headers: corsHeaders() });
  }

  // 대상 멤버 찾기
  const target = teamData.members.find(m => m.email === target_email);
  if (!target) {
    return new Response(JSON.stringify({ error: 'Member not found' }), {
      status: 404, headers: corsHeaders()
    });
  }

  // 오너 역할은 변경 불가
  if (target_email === teamData.owner && new_role !== 'admin') {
    return new Response(JSON.stringify({
      error: 'Cannot change owner role'
    }), { status: 400, headers: corsHeaders() });
  }

  target.role = new_role;
  await saveTeamData(env, license_key, teamData);

  return new Response(JSON.stringify({
    success: true,
    message: `${target_email} role changed to ${new_role}`
  }), { headers: corsHeaders() });
}

/**
 * 팀 설정 조회/수정 (C-Level 역할 토글)
 */
async function handleTeamSettings(request, env) {
  const url = new URL(request.url);

  if (request.method === 'GET') {
    const licenseKey = url.searchParams.get('license_key');

    if (!licenseKey) {
      return new Response(JSON.stringify({ error: 'license_key required' }), {
        status: 400, headers: corsHeaders()
      });
    }

    const teamCheck = await verifyTeamLicense(env, licenseKey);
    if (!teamCheck.valid) {
      return new Response(JSON.stringify({ error: teamCheck.error }), {
        status: 403, headers: corsHeaders()
      });
    }

    const teamData = await getTeamData(env, licenseKey);

    return new Response(JSON.stringify({
      success: true,
      settings: teamData.settings
    }), { headers: corsHeaders() });
  }

  if (request.method === 'PUT' || request.method === 'POST') {
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
        status: 400, headers: corsHeaders()
      });
    }

    const { license_key, requester_email, settings } = body;

    if (!license_key || !requester_email || !settings) {
      return new Response(JSON.stringify({
        error: 'license_key, requester_email, settings required'
      }), { status: 400, headers: corsHeaders() });
    }

    const teamCheck = await verifyTeamLicense(env, license_key);
    if (!teamCheck.valid) {
      return new Response(JSON.stringify({ error: teamCheck.error }), {
        status: 403, headers: corsHeaders()
      });
    }

    const teamData = await getTeamData(env, license_key);

    // Admin 권한 확인
    const requester = teamData.members.find(m => m.email === requester_email);
    if (!requester || requester.role !== 'admin') {
      return new Response(JSON.stringify({
        error: 'Admin permission required'
      }), { status: 403, headers: corsHeaders() });
    }

    // 설정 업데이트 (enabled_roles만)
    if (settings.enabled_roles) {
      teamData.settings.enabled_roles = {
        cto: !!settings.enabled_roles.cto,
        cdo: !!settings.enabled_roles.cdo,
        cpo: !!settings.enabled_roles.cpo,
        cfo: !!settings.enabled_roles.cfo,
        cmo: !!settings.enabled_roles.cmo
      };
    }

    await saveTeamData(env, license_key, teamData);

    return new Response(JSON.stringify({
      success: true,
      settings: teamData.settings
    }), { headers: corsHeaders() });
  }

  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405, headers: corsHeaders()
  });
}

/**
 * 팀 에러 패턴 동기화 (업로드)
 */
async function handleTeamErrorsSync(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: corsHeaders()
    });
  }

  const { license_key, member_email, errors } = body;

  if (!license_key || !member_email || !errors || !Array.isArray(errors)) {
    return new Response(JSON.stringify({
      error: 'license_key, member_email, errors[] required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, license_key);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  // 팀 멤버 확인
  const teamData = await getTeamData(env, license_key);
  const isMember = teamData.members.find(m => m.email === member_email);
  if (!isMember) {
    return new Response(JSON.stringify({ error: 'Not a team member' }), {
      status: 403, headers: corsHeaders()
    });
  }

  // 팀 에러 데이터 조회
  const errorsKey = `team:${license_key}:errors`;
  const existingData = await env.TEAM_DATA.get(errorsKey);
  const teamErrors = existingData ? JSON.parse(existingData) : { patterns: [] };

  // 에러 패턴 병합
  for (const error of errors) {
    const existing = teamErrors.patterns.find(p =>
      p.type === error.type && p.signature === error.signature
    );

    if (existing) {
      // 기존 패턴 업데이트 (count 증가)
      existing.count = (existing.count || 1) + 1;
      existing.last_seen = new Date().toISOString();
      if (error.never && !existing.never) existing.never = error.never;
      if (error.always && !existing.always) existing.always = error.always;
    } else {
      // 새 패턴 추가
      teamErrors.patterns.push({
        type: error.type,
        signature: error.signature,
        never: error.never || null,
        always: error.always || null,
        count: 1,
        created_by: member_email,
        created_at: new Date().toISOString(),
        last_seen: new Date().toISOString()
      });
    }
  }

  teamErrors.last_sync = new Date().toISOString();
  await env.TEAM_DATA.put(errorsKey, JSON.stringify(teamErrors));

  return new Response(JSON.stringify({
    success: true,
    synced: errors.length,
    total_patterns: teamErrors.patterns.length
  }), { headers: corsHeaders() });
}

/**
 * 팀 에러 패턴 조회
 */
async function handleTeamErrors(request, env) {
  const url = new URL(request.url);
  const licenseKey = url.searchParams.get('license_key');

  if (!licenseKey) {
    return new Response(JSON.stringify({ error: 'license_key required' }), {
      status: 400, headers: corsHeaders()
    });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, licenseKey);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  const errorsKey = `team:${licenseKey}:errors`;
  const data = await env.TEAM_DATA.get(errorsKey);
  const teamErrors = data ? JSON.parse(data) : { patterns: [] };

  return new Response(JSON.stringify({
    success: true,
    patterns: teamErrors.patterns,
    total: teamErrors.patterns.length,
    last_sync: teamErrors.last_sync || null
  }), { headers: corsHeaders() });
}

/**
 * 팀 NEVER/ALWAYS 규칙 조회
 */
async function handleTeamErrorRules(request, env) {
  const url = new URL(request.url);
  const licenseKey = url.searchParams.get('license_key');

  if (!licenseKey) {
    return new Response(JSON.stringify({ error: 'license_key required' }), {
      status: 400, headers: corsHeaders()
    });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, licenseKey);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  const errorsKey = `team:${licenseKey}:errors`;
  const data = await env.TEAM_DATA.get(errorsKey);
  const teamErrors = data ? JSON.parse(data) : { patterns: [] };

  // NEVER/ALWAYS 규칙만 추출
  const rules = {
    never: [],
    always: []
  };

  for (const pattern of teamErrors.patterns) {
    if (pattern.never) {
      rules.never.push({
        rule: pattern.never,
        type: pattern.type,
        count: pattern.count,
        created_by: pattern.created_by
      });
    }
    if (pattern.always) {
      rules.always.push({
        rule: pattern.always,
        type: pattern.type,
        count: pattern.count,
        created_by: pattern.created_by
      });
    }
  }

  return new Response(JSON.stringify({
    success: true,
    rules,
    total_never: rules.never.length,
    total_always: rules.always.length
  }), { headers: corsHeaders() });
}

/**
 * 프로젝트 컨텍스트 동기화
 */
async function handleTeamProjectSync(request, env) {
  if (request.method !== 'POST') {
    return new Response(JSON.stringify({ error: 'Method not allowed' }), {
      status: 405, headers: corsHeaders()
    });
  }

  let body;
  try {
    body = await request.json();
  } catch (e) {
    return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
      status: 400, headers: corsHeaders()
    });
  }

  const { license_key, member_email, project_id, context } = body;

  if (!license_key || !member_email || !project_id || !context) {
    return new Response(JSON.stringify({
      error: 'license_key, member_email, project_id, context required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, license_key);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  // 팀 멤버 확인
  const teamData = await getTeamData(env, license_key);
  const isMember = teamData.members.find(m => m.email === member_email);
  if (!isMember) {
    return new Response(JSON.stringify({ error: 'Not a team member' }), {
      status: 403, headers: corsHeaders()
    });
  }

  // 프로젝트 컨텍스트 저장
  const projectKey = `team:${license_key}:project:${project_id}`;
  const existingData = await env.TEAM_DATA.get(projectKey);
  const projectData = existingData ? JSON.parse(existingData) : {
    created_at: new Date().toISOString(),
    decisions: [],
    review_rules: []
  };

  // 컨텍스트 업데이트
  if (context.prd) projectData.prd = context.prd;
  if (context.claude_md) projectData.claude_md = context.claude_md;
  if (context.structure) projectData.structure = context.structure;

  // 결정사항 추가 (있으면)
  if (context.decision) {
    projectData.decisions.push({
      ...context.decision,
      recorded_by: member_email,
      recorded_at: new Date().toISOString()
    });
  }

  projectData.updated_at = new Date().toISOString();
  projectData.updated_by = member_email;

  await env.TEAM_DATA.put(projectKey, JSON.stringify(projectData));

  return new Response(JSON.stringify({
    success: true,
    project_id,
    updated_at: projectData.updated_at,
    decisions_count: projectData.decisions.length
  }), { headers: corsHeaders() });
}

/**
 * 프로젝트 컨텍스트 조회
 */
async function handleTeamProject(request, env) {
  const url = new URL(request.url);
  const licenseKey = url.searchParams.get('license_key');
  const projectId = url.searchParams.get('project_id');

  if (!licenseKey || !projectId) {
    return new Response(JSON.stringify({
      error: 'license_key and project_id required'
    }), { status: 400, headers: corsHeaders() });
  }

  // 팀 라이선스 검증
  const teamCheck = await verifyTeamLicense(env, licenseKey);
  if (!teamCheck.valid) {
    return new Response(JSON.stringify({ error: teamCheck.error }), {
      status: 403, headers: corsHeaders()
    });
  }

  const projectKey = `team:${licenseKey}:project:${projectId}`;
  const data = await env.TEAM_DATA.get(projectKey);

  if (!data) {
    return new Response(JSON.stringify({
      success: true,
      project_id: projectId,
      context: null,
      message: 'Project context not found'
    }), { headers: corsHeaders() });
  }

  const projectData = JSON.parse(data);

  return new Response(JSON.stringify({
    success: true,
    project_id: projectId,
    context: {
      prd: projectData.prd || null,
      claude_md: projectData.claude_md || null,
      structure: projectData.structure || null,
      decisions: projectData.decisions || [],
      review_rules: projectData.review_rules || []
    },
    updated_at: projectData.updated_at,
    updated_by: projectData.updated_by
  }), { headers: corsHeaders() });
}

/**
 * 리뷰 룰 관리
 */
async function handleTeamReviewRules(request, env) {
  const url = new URL(request.url);

  if (request.method === 'GET') {
    const licenseKey = url.searchParams.get('license_key');
    const projectId = url.searchParams.get('project_id');

    if (!licenseKey || !projectId) {
      return new Response(JSON.stringify({
        error: 'license_key and project_id required'
      }), { status: 400, headers: corsHeaders() });
    }

    const teamCheck = await verifyTeamLicense(env, licenseKey);
    if (!teamCheck.valid) {
      return new Response(JSON.stringify({ error: teamCheck.error }), {
        status: 403, headers: corsHeaders()
      });
    }

    const projectKey = `team:${licenseKey}:project:${projectId}`;
    const data = await env.TEAM_DATA.get(projectKey);
    const projectData = data ? JSON.parse(data) : { review_rules: [] };

    return new Response(JSON.stringify({
      success: true,
      rules: projectData.review_rules || []
    }), { headers: corsHeaders() });
  }

  if (request.method === 'POST' || request.method === 'PUT') {
    let body;
    try {
      body = await request.json();
    } catch (e) {
      return new Response(JSON.stringify({ error: 'Invalid JSON' }), {
        status: 400, headers: corsHeaders()
      });
    }

    const { license_key, member_email, project_id, rule } = body;

    if (!license_key || !member_email || !project_id || !rule) {
      return new Response(JSON.stringify({
        error: 'license_key, member_email, project_id, rule required'
      }), { status: 400, headers: corsHeaders() });
    }

    const teamCheck = await verifyTeamLicense(env, license_key);
    if (!teamCheck.valid) {
      return new Response(JSON.stringify({ error: teamCheck.error }), {
        status: 403, headers: corsHeaders()
      });
    }

    // 팀 멤버 확인 (Admin만 룰 추가 가능)
    const teamData = await getTeamData(env, license_key);
    const member = teamData.members.find(m => m.email === member_email);
    if (!member || member.role !== 'admin') {
      return new Response(JSON.stringify({
        error: 'Admin permission required'
      }), { status: 403, headers: corsHeaders() });
    }

    const projectKey = `team:${license_key}:project:${project_id}`;
    const existingData = await env.TEAM_DATA.get(projectKey);
    const projectData = existingData ? JSON.parse(existingData) : {
      created_at: new Date().toISOString(),
      decisions: [],
      review_rules: []
    };

    projectData.review_rules.push({
      rule: rule.rule,
      priority: rule.priority || 'medium',
      created_by: member_email,
      created_at: new Date().toISOString()
    });

    await env.TEAM_DATA.put(projectKey, JSON.stringify(projectData));

    return new Response(JSON.stringify({
      success: true,
      rules_count: projectData.review_rules.length
    }), { headers: corsHeaders() });
  }

  return new Response(JSON.stringify({ error: 'Method not allowed' }), {
    status: 405, headers: corsHeaders()
  });
}
