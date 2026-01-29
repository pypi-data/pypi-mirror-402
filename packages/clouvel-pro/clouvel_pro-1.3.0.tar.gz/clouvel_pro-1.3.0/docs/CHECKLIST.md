# Clouvel Pro 체크리스트

> 릴리스 및 검증용 체크리스트

---

## 릴리스 전 체크리스트

### 코드 품질

- [ ] TypeScript 타입 체크 통과
- [ ] Lint 에러 0개
- [ ] 테스트 8개 이상 작성
- [ ] 테스트 전체 통과
- [ ] 빌드 성공

### 라이선스 검증

- [ ] 온라인 검증 동작 확인
- [ ] 오프라인 캐시 폴백 확인
- [ ] 무효 키 거부 확인
- [ ] 환경변수 라이선스 키 인식

### Shovel 설치

- [ ] 모든 커맨드 파일 생성
- [ ] templates 폴더 생성
- [ ] settings.json 기본값
- [ ] 기존 파일 merge 동작

### Error Learning

- [ ] 에러 로그 기록
- [ ] 패턴 분석 동작
- [ ] NEVER/ALWAYS 규칙 생성
- [ ] ERROR_LOG.md 포맷 준수

### 문서

- [ ] README.md 최신화
- [ ] ROADMAP.md 업데이트
- [ ] CHANGELOG 작성

---

## Gate 체크리스트 (매 커밋)

```bash
# 순서 고정 - 하나라도 실패 시 중단
pnpm lint      # Step 1
pnpm test      # Step 2
pnpm build     # Step 3
pnpm audit     # Step 4
```

### Lint (Step 1)

- [ ] ESLint 에러 0개
- [ ] 경고는 허용 (단, 검토 필요)
- [ ] 자동 수정: `pnpm lint --fix`

### Test (Step 2)

- [ ] 테스트 파일 존재
- [ ] 최소 8개 테스트 케이스
- [ ] 성공/실패 케이스 모두 포함
- [ ] Flaky 테스트 없음

### Build (Step 3)

- [ ] TypeScript 컴파일 성공
- [ ] 번들 생성 확인
- [ ] 경로 별칭 해결

### Audit (Step 4)

- [ ] Critical 취약점 0개
- [ ] High는 경고 (통과 가능)

---

## Context Bias 제거 체크리스트 (Boris 방식)

### 검증 전

- [ ] /handoff 실행 (의도 기록)
- [ ] /clear 실행 또는 새 세션
- [ ] 충분한 시간 경과 (선택)

### 검증 시

- [ ] 기록된 의도만 보고 검증
- [ ] 코드 직접 확인
- [ ] 요구사항과 비교

---

## PyPI 배포 체크리스트

### 준비

- [ ] 버전 번호 업데이트 (pyproject.toml)
- [ ] CHANGELOG 작성
- [ ] Git 태그 생성

### 빌드

```bash
python -m build
```

- [ ] dist/ 폴더에 .whl, .tar.gz 생성

### 업로드

```bash
twine upload dist/*
```

- [ ] PyPI 업로드 성공
- [ ] pip install clouvel-pro 동작 확인

---

## Lemon Squeezy 연동 체크리스트

### 상품 설정

- [ ] Personal Pro ($29) 생성
- [ ] Team Pro ($79) 생성
- [ ] Enterprise Pro ($199) 생성 (선택)

### 라이선스 키

- [ ] 라이선스 키 형식 확인
- [ ] 활성화 횟수 제한 설정
- [ ] 티어별 구분 가능

### 웹훅 (Phase 2)

- [ ] order_refunded 이벤트 등록
- [ ] 서명 검증 구현
- [ ] KV 저장 동작

---

## 환불 처리 체크리스트

### 정책

- [ ] 14일 환불 정책 랜딩페이지 명시
- [ ] 구매 확인 이메일에 정책 안내

### 기술

- [ ] 웹훅 수신 확인
- [ ] KV에 revoked 저장
- [ ] clouvel-pro 검증 시 차단
- [ ] Discord 알림 수신

---

## 일일 체크리스트 (운영)

- [ ] Discord 알림 확인
- [ ] 환불 요청 처리
- [ ] 에러 로그 모니터링
- [ ] 신규 구매 확인

---

## 주간 체크리스트

- [ ] ROADMAP 진행 상황 검토
- [ ] 사용자 피드백 정리
- [ ] 백로그 우선순위 조정
- [ ] 버전 릴리스 계획
