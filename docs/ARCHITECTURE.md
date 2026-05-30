# 아키텍처 노트

## 한 줄 요약
`사용자 입력 → 7단계 시스템 프롬프트 → tool_use 루프 (법령/판례/검증) → 후처리(마스킹·면책·인젝션) → Word 출력`

## 모듈 책임

| 모듈 | 책임 |
|---|---|
| `config.py` | 환경변수 로딩, mock/real 모드 결정 |
| `tools/schema.py` | Anthropic tool_use 스키마 (6종 도구) |
| `tools/law_lookup.py` | 법령 검색·조문 조회 (법제처 OPEN API) |
| `tools/precedent_search.py` | 판례 목록·본문 (법제처 OPEN API) |
| `tools/citation_guard.py` | 인용 환각 방지 (verify_citation + audit) |
| `tools/ktx.py` | KTX 추천 (mock + Computer Use stub) |
| `tools/mocks.py` | 오프라인 데모용 모의 데이터 |
| `prompts/base.md` | 운영 래퍼 (마스킹·면책·인젝션·인용) |
| `prompts/<domain>.md` | 도메인별 7단계 시스템 프롬프트 |
| `agent/safety.py` | 후처리 (mask, ensure_disclaimer, detect_injection) |
| `agent/tool_router.py` | tool_name → 함수 디스패치 |
| `agent/orchestrator.py` | 실행 루프 (mock 시뮬레이터 + real SDK) |
| `render/docx_render.py` | 결과 → Word (또는 .md fallback) |
| `cli.py` | 명령행 진입점 |

## 도구 호출 흐름 (real 모드)

```
[user]  사건 JSON 입력
  ↓
[Claude]  prompts/<domain>.md 따라 작업 시작
  ↓
[tool_use] search_law("근로기준법")
  ↓
[tool_result] 법령 ID 등 메타
  ↓
[tool_use] get_law_article("근로기준법", "제26조")
  ↓
[tool_result] 조문 본문
  ↓
[tool_use] search_precedent("해고", court="대법원")
  ↓
[tool_use] verify_citation("law", "근로기준법 제26조")
  ↓
[Claude]  검증된 인용만 본문에 사용
  ↓
[safety]  mask + ensure_disclaimer + detect_injection
  ↓
[render]  Word 저장
```

## mock 모드 동작

`is_mock=True` 일 때 도구 호출은 `mocks.py` 의 미리 준비된 응답을 반환합니다.
LLM 자체를 호출하지 않으므로 API 비용 0원이고 오프라인에서 완전 동작합니다.
시뮬레이터(`_simulate_*` 함수들)가 결과 본문을 직접 생성합니다 — 워크숍에서
"흐름이 보이는" 데모용입니다. real 모드는 실제 Claude를 호출합니다.

## 실 데이터 연동 시 점검 항목

1. `.env` 의 `LAW_GO_KR_OC` 가 `open.law.go.kr` 에서 발급된 OC ID 인가
2. `tools/law_lookup.py` 의 응답 파싱이 실제 JSON 구조와 맞는가
   (현재 코드는 `LawSearch.law` 배열을 가정 — 실 호출로 검증 필요)
3. KTX 에이전트의 real 모드는 stub만 제공 — Anthropic Computer Use API 또는
   Playwright 통합이 별도 작업으로 필요
