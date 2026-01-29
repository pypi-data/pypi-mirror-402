# Clouvel License Webhook

> Lemon Squeezy 환불 감지 → 라이선스 차단

---

## 아키텍처

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

---

## 배포 가이드

### 1. Cloudflare 계정 준비

1. [Cloudflare](https://cloudflare.com) 가입 (무료)
2. Workers & Pages 활성화

### 2. Wrangler CLI 설치

```bash
npm install -g wrangler
wrangler login
```

### 3. KV 네임스페이스 생성

```bash
cd webhook
wrangler kv:namespace create REVOKED_LICENSES
```

출력된 ID를 `wrangler.toml`에 입력:

```toml
[[kv_namespaces]]
binding = "REVOKED_LICENSES"
id = "출력된_ID_여기에"
```

### 4. 환경변수 설정

```bash
# Lemon Squeezy 웹훅 서명 시크릿
wrangler secret put LEMON_SQUEEZY_WEBHOOK_SECRET

# Discord 웹훅 URL (선택)
wrangler secret put DISCORD_WEBHOOK_URL
```

### 5. 배포

```bash
wrangler deploy
```

배포 후 URL 확인:
```
https://clouvel-license-webhook.<your-subdomain>.workers.dev
```

### 6. Lemon Squeezy 웹훅 등록

1. [Lemon Squeezy 대시보드](https://app.lemonsqueezy.com) → Settings → Webhooks
2. Add Webhook:
   - URL: `https://clouvel-license-webhook.<your-subdomain>.workers.dev/webhook`
   - Events: `order_refunded` 선택
   - Signing Secret: 복사 → `LEMON_SQUEEZY_WEBHOOK_SECRET`에 설정

---

## API 엔드포인트

### POST /webhook

Lemon Squeezy 웹훅 수신

- Headers: `X-Signature` (HMAC-SHA256)
- Body: Lemon Squeezy 웹훅 페이로드

### GET /check?key=LICENSE_KEY

라이선스 차단 여부 확인

**응답 (정상):**
```json
{ "revoked": false }
```

**응답 (차단됨):**
```json
{
  "revoked": true,
  "revoked_at": "2026-01-17T12:00:00Z",
  "reason": "refund"
}
```

### GET /health

헬스 체크

```json
{
  "status": "ok",
  "timestamp": "2026-01-17T12:00:00Z",
  "service": "clouvel-license-webhook"
}
```

---

## 테스트

### 로컬 테스트

```bash
wrangler dev
```

### 헬스 체크

```bash
curl https://clouvel-license-webhook.<subdomain>.workers.dev/health
```

### 차단 확인

```bash
curl "https://clouvel-license-webhook.<subdomain>.workers.dev/check?key=TEST-KEY"
```

---

## Discord 알림 설정 (선택)

1. Discord 서버 → 채널 설정 → 연동 → 웹후크
2. 새 웹후크 생성 → URL 복사
3. `wrangler secret put DISCORD_WEBHOOK_URL`

---

## 비용

- Cloudflare Workers: **무료** (일 10만 요청)
- Cloudflare KV: **무료** (일 10만 읽기, 1만 쓰기)
- Discord Webhook: **무료**

---

## 파일 구조

```
webhook/
├── wrangler.toml      # Cloudflare 설정
├── src/
│   └── index.js       # 웹훅 핸들러
└── README.md          # 이 파일
```
