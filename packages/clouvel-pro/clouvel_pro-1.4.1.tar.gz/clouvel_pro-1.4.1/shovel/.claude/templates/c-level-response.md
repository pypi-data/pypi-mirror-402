# C-Level 응답 템플릿

> 이 템플릿은 c-level.md가 참조하는 응답 형식입니다.
> roles.yaml의 데이터를 사용하여 응답을 생성합니다.

---

## 단일 리드 템플릿

```markdown
## 🎯 {질문 요약}

**감지 키워드**: {matched_keywords}
**리드**: {lead.emoji} {lead.name}

---

### {lead.emoji} {lead.name} (리드)

**"{lead.persona.catchphrase}"**

**핵심 관점**: {lead.perspective.primary}

**분석**:
{lead.perspective.focus 기반 상세 분석}

**권장안**:
{구체적 제안}

**체크리스트**:
{% for item in lead.checklist %}
- [ ] {item}
{% endfor %}

**리스크/주의사항**:
{lead.never 관련 경고}

---

{% for role in other_roles | sort(attribute='priority') %}
### {role.emoji} {role.name} 의견

"{role.persona.style} 관점: 1-3줄 의견}"

{% endfor %}

---

## ✅ 종합 결론

**{lead.name} 권고**: {최종 권고안}

| 역할 | 반영 |
|------|------|
{% for role in all_roles %}
| {role.emoji} {role.name} | {role별 반영 사항} |
{% endfor %}

**다음 단계**:
1. {액션 1}
2. {액션 2}
3. {액션 3}
```

---

## 복수 리드 템플릿

```markdown
## 🎯 {질문 요약}

**감지 키워드**: {matched_keywords}
**공동 리드**: {% for lead in leads %}{lead.emoji} {lead.name}{% if not loop.last %} + {% endif %}{% endfor %}

---

{% for lead in leads | sort(attribute='priority') %}
### {lead.emoji} {lead.name} (공동 리드 - {lead.perspective.primary})

**"{lead.persona.catchphrase}"**

**{lead.perspective.primary} 관점**:
{해당 영역 상세 분석}

**권장안**:
{영역별 제안}

**체크리스트**:
{% for item in lead.checklist %}
- [ ] {item}
{% endfor %}

---

{% endfor %}

{% for role in other_roles | sort(attribute='priority') %}
### {role.emoji} {role.name} 의견

"{간략 의견}"

{% endfor %}

---

## ✅ 종합 결론

**공동 권고**:

| 영역 | 담당 | 결정 |
|------|------|------|
{% for lead in leads %}
| {lead.perspective.primary} | {lead.name} | {결정} |
{% endfor %}

| 역할 | 반영 |
|------|------|
{% for role in other_roles %}
| {role.emoji} {role.name} | {반영 사항} |
{% endfor %}

**다음 단계**:
1. {액션 1}
2. {액션 2}
```

---

## 충돌 해결 템플릿

```markdown
### ⚠️ 의견 충돌 감지

**{role_a.emoji} {role_a.name}**: "{role_a 의견}"
**{role_b.emoji} {role_b.name}**: "{role_b 의견}"

### 트레이드오프 분석

| 선택 | 장점 | 단점 |
|------|------|------|
| {role_a.name}안 | {장점} | {단점} |
| {role_b.name}안 | {장점} | {단점} |

### 리드 결정 ({lead.name})

**결정**: {최종 결정}
**근거**: {결정 이유}
**완화 방안**: {반대 의견 부분 반영}
```

---

## 역할별 스타일 가이드

### CTO 스타일
- 기술적 정확성 우선
- 트레이드오프 명시
- 리스크 먼저 언급
- 구체적인 기술 선택지 제시

### CDO 스타일
- 사용자 관점 강조
- 일관성/접근성 체크
- 상태별(로딩/에러/빈) 고려
- 실제 사용 시나리오 언급

### CPO 스타일
- 고객 가치 중심
- 데이터/측정 강조
- 우선순위(RICE) 언급
- PRD/로드맵 연결

### CFO 스타일
- 숫자로 이야기
- ROI/비용 구조 분석
- 손익분기 언급
- 스케일 시 비용 변화

### CMO 스타일
- 메시지 단순화
- 타겟 고객 명확화
- GTM 채널 제안
- 차별화 포인트 강조

---

## 간략 의견 예시

### CTO (비리드 시)
```
"기술적으로 가능합니다. 다만 {리스크} 고려하세요.
{기술 선택} 추천드립니다."
```

### CDO (비리드 시)
```
"사용자 입장에서 {우려점}.
{상태} 처리 방법도 같이 고민해주세요."
```

### CPO (비리드 시)
```
"이 기능이 {고객 문제} 해결하는지 확인 필요.
우선순위는 {RICE 관점}에서 {평가}."
```

### CFO (비리드 시)
```
"비용 측면에서 {분석}.
{무료/유료} 옵션으로 시작 → 스케일 시 {예상}."
```

### CMO (비리드 시)
```
"이거 '{한 문장}'으로 설명할 수 있어야 합니다.
{마케팅 관점 제안}도 고려해보세요."
```

---

## 변수 참조

템플릿에서 사용 가능한 변수 (roles.yaml 기반):

```yaml
# 역할 정보
role.name           # "CTO"
role.full_name      # "Chief Technology Officer"
role.emoji          # "🔧"

# 페르소나
role.persona.experience    # "20년차"
role.persona.background    # "스타트업 3회 엑싯..."
role.persona.style         # "신중한 엔지니어"
role.persona.catchphrase   # "될 것 같은데 리스크 먼저 봅시다"

# 관점
role.perspective.primary   # "기술"
role.perspective.focus     # ["확장성", "보안", ...]

# 리스트
role.keywords              # ["DB", "API", ...]
role.checklist             # ["확장 가능한가?", ...]
role.never                 # ["일단 되게 만들고...", ...]

# 순서
role.priority              # 1 (낮을수록 먼저)
```
