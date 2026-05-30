# korean-domain-agent

> 한국 도메인 실무자(변호사·노무사·세무사·회계사 등)가 본인 업무에 맞춰 커스터마이징할 수 있는 LLM 에이전트 키트.
> 법제처 OPEN API 기반 인용 환각 가드와 한국 식별정보 마스킹을 기본 탑재.

[![License](https://img.shields.io/badge/license-MIT_%2B_PolyForm--NC-blue.svg)](#라이선스)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue.svg)](#)
[![Tests](https://img.shields.io/badge/tests-35%2F35-brightgreen.svg)](#테스트)

본 키트는 [speciai.team](https://speciai.team) **도메인 AI 허브**의 공개 컴포넌트입니다.
도메인 AI 허브는 한국 전문직 실무자를 위한 도메인 특화 LLM 에이전트 카탈로그·인스톨러·MCP 가드를 한 곳에서 제공합니다.

---

## 목차

- [핵심 특징](#핵심-특징)
- [무엇을 해결하나](#무엇을-해결하나)
- [speciai.team 도메인 AI 허브](#speciaiteam-도메인-ai-허브)
- [5분 안에 시작](#5분-안에-시작)
- [6개 작업 모드](#6개-작업-모드)
- [도메인 추가하기](#도메인-추가하기)
- [Claude Code 스킬](#claude-code-스킬)
- [환각·보안 MCP 점검](#환각보안-mcp-점검)
- [폴더 구조](#폴더-구조)
- [도구 목록](#도구-목록)
- [안전 정책](#안전-정책)
- [라이선스](#라이선스)
- [변경 이력](#변경-이력)

---

## 핵심 특징

- **6개 작업 모드 자동 분류** — 작성·검토·퇴고·요약·리서치·자문. 사건 데이터의 키 구성에 따라 모드를 자동 선택.
- **환각 방지 인용 가드** — 법제처 OPEN API로 법령·판례 번호를 본문 인용 직전 실시간 검증. 검증 실패 인용은 `[확인 필요]`로 표기.
- **한국 식별정보 9종 마스킹** — 주민·법인등록·전화·계좌·이메일·사업자번호·신용카드·법인번호·법인등록번호.
- **Anthropic prompt cache 자동 적용** — system+tools 캐싱으로 입력 토큰 최대 90% 절감, 응답 속도 30%+ 단축.
- **모드별 temperature 분리** — 요약·리서치 0.0 / 작성 0.2 / 자문 0.3.
- **인용 검증 메모이즈** — 동일 `(kind, ref)` 반복 호출 0회.
- **인젝션 방어** — 한/영 키워드 기반 의심 입력 감지, `<<<DOCUMENT>>>` 입력 격리.
- **mock 모드** — API 키 없이 워크숍·교육 환경에서 즉시 동작.
- **python-docx Word 출력** — 한국 법률 문서 양식(제1. / 가. / (1)) 그대로.

## 무엇을 해결하나

한국 전문직 실무에서 LLM을 그대로 쓰면 다음 3가지가 발목을 잡습니다.

1. **법령·판례 환각** — 존재하지 않는 조문 번호·사건번호를 그럴듯하게 생성.
2. **식별정보 유출 위험** — 의뢰인 실명·주민번호·계좌가 프롬프트에 그대로 들어감.
3. **분야별 표준 양식 부재** — 한국 변호사 서면, 노무 이유서, 세무 의견서 양식이 LLM 기본값과 다름.

`korean-domain-agent`는 이 세 가지를 코드 레벨에서 차단·자동화합니다.

---

## speciai.team 도메인 AI 허브

본 레포는 [speciai.team](https://speciai.team)이 운영하는 **도메인 AI 허브**의 오픈 컴포넌트입니다.

도메인 AI 허브가 제공하는 것

- **도메인 에이전트 카탈로그** — 법률·노무·세무·특허·회계 등 도메인별로 검증된 시스템 프롬프트와 에이전트 키트.
- **인스톨러 스킬** — Claude Code 한 줄 호출로 키트 설치 + 도메인 인터뷰 + 첫 산출물 생성까지 자동화.
- **MCP 환각·보안 가드** — `korean-contracts` 등 MCP 서버로 인용 검증·개인정보 마스킹 레이어를 강화.
- **숏츠·콘텐츠 패키지** — 도메인 실무자가 본인 채널에서 키트를 소개·교육할 수 있는 자료팩.
- **상업 라이선스 협업** — 로펌·기업 SaaS에 가드 모듈을 통합하려는 팀을 위한 별도 라이선스.

본 `korean-domain-agent` 레포는 허브의 **법률·노무 기본 베이스**에 해당합니다. 같은 패턴으로 세무·특허·의료 등 다른 도메인 키트가 허브에 추가됩니다.

문의·협업: kimlawtech@gmail.com · https://speciai.team

---

## 5분 안에 시작

### 1. 설치

```bash
git clone https://github.com/kimlawtech/korean-domain-agent.git
cd korean-domain-agent
python -m venv .venv
source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -e .
```

### 2. mock 모드 (API 키 없이 즉시 실행)

```bash
# 도메인 미지정 → 범용(general) 모드
python -m src.cli run \
  --input data/samples/general_001.json \
  --out out/general_001.docx \
  --mode mock

# 도메인 특화
python -m src.cli run --agent unfair_dismissal \
  --input data/samples/dismissal_001.json \
  --out out/dismissal_001.docx --mode mock
```

`out/*.docx`가 생성되면 OK. 결과 본문에는 적용 법령 본문, 마스킹 알림, 면책 문구가 자동 포함됩니다.

### 3. real 모드 (Anthropic + 법제처 OPEN API)

```bash
cp .env.example .env
# .env 편집:
# ANTHROPIC_API_KEY=sk-ant-...
# LAW_GO_KR_OC=발급받은_OC_ID
# AGENT_MODE=real
# ANTHROPIC_MODEL=claude-sonnet-4-6

python -m src.cli run --agent contract_review \
  --input data/samples/contract_001.json \
  --out out/contract_001.docx --mode real
```

- Anthropic API 키: https://console.anthropic.com
- 법제처 OC ID: https://open.law.go.kr (무료 회원가입 후 발급)

### 4. 테스트

```bash
pytest -v
# 35 passed
```

---

## 6개 작업 모드

`general` 모드는 사건 데이터의 키 구성에 따라 작업 유형을 자동 분류합니다.

| 모드 | 자동 분류 키 (예시) | 기본 temperature | 산출물 예 |
|---|---|---|---|
| 작성 | (기본값) 당사자·청구취지·사실관계 | 0.2 | 의견서, 내용증명, 합의서, 계약서 초안 |
| 검토 | `원문`, `초안`, `검토_대상` | 0.1 | 법리·논리·리스크 평가표 |
| 퇴고 | `퇴고_대상`, `문체_대상` | 0.1 | 문체·가독성 개선안 (법적 결론 불변) |
| 요약 | `요약_대상`, `판결문` | 0.0 | 판결문·계약서 핵심 요약 |
| 리서치 | `리서치_주제`, `research_topic` | 0.0 | 법령·판례·해석론 카드 |
| 자문 | `질의`, `쟁점` | 0.3 | 쟁점·전략·주위적/예비적 분석 |

명시 지정:

```json
{
  "작업_모드": "자문",
  "사건명": "임대차 보증금 자문",
  "질의": "원상회복 비용 공제 가능 범위"
}
```

---

## 도메인 추가하기

새 도메인 `.md` 1장 추가 → 즉시 동작.

```bash
# 1) 시스템 프롬프트 작성 (7단계 구조)
vim src/prompts/tax_objection.md

# 2) 샘플 JSON
vim data/samples/tax_001.json

# 3) CLI에 등록 — src/cli.py 의 AGENTS 리스트에 도메인 이름 추가
#    AGENTS = ["general", ..., "tax_objection"]

# 4) 실행
python -m src.cli run --agent tax_objection \
  --input data/samples/tax_001.json \
  --out out/tax_001.docx --mode mock
```

도메인 프롬프트는 `base.md + general.md + 도메인.md` 순서로 합성되어 도메인 지시가 최종 우선합니다.

7단계 구조:
1. 역할(맥락) — 페르소나, 전문성, 작업 수행 방식
2. 과업 설명 — 산출물 1줄 정의
3. 지침 — 정보 수집·사실관계·법리 검토·주장 구성
4. 목차 — 산출물 표준 양식
5. 작성 사례
6. 작성 형식 — 날짜·금액·당사자·종결·증거·법령 표기
7. 추가 제약사항 + 품질 체크리스트

---

## Claude Code 스킬

본 키트는 Claude Code 사용자 스킬 `korean-domain-agent`로 등록되어 있어,
세션에서 `/korean-domain-agent` 호출 시 다음을 자동화합니다:

1. 레포 clone + venv 설치
2. 환각·보안 MCP 점검 (`korean-contracts` 등)
3. 도메인 6개 질문 인터뷰 → `src/prompts/{도메인}.md` 자동 생성
4. 샘플 JSON 생성
5. 첫 mock 산출물 실행

스킬 수동 설치:

```bash
mkdir -p ~/.claude/skills/korean-domain-agent
curl -L -o ~/.claude/skills/korean-domain-agent/SKILL.md \
  https://raw.githubusercontent.com/kimlawtech/korean-domain-agent/main/skills/korean-domain-agent/SKILL.md
```

설치 후 Claude Code 세션에서 `/korean-domain-agent` 입력으로 발동.

---

## 환각·보안 MCP 점검

본 키트는 자체 가드(`citation_guard.py`, `safety.py`)로 1차 보호를 제공하지만,
추가 MCP 서버를 연결하면 가드 레이어가 강화됩니다.

권장 MCP

- **korean-contracts** — 한국 계약서·문서 작성 시 개인정보 마스킹·법령 인용 검증 강화 MCP. speciai.team 도메인 AI 허브에서 배포.
- **법제처 OPEN API 래퍼 MCP** — 본 키트 내장 도구(`law_lookup.py`, `precedent_search.py`)와 동일 인터페이스로 외부 MCP 대체 가능.

세션 시작 시 점검 (Claude Code):

```
/security
```

(`security` 스킬이 설치되어 있으면 현재 세션·과거 세션의 MCP 호출 상태를 분석해 보고합니다.)

미연결 상태에서도 본 키트의 기본 가드만으로 동작합니다. 상업 환경에서는 MCP 연결을 권장.

---

## 폴더 구조

```
korean-domain-agent/
├─ LICENSE                       # MIT (프레임워크)
├─ LICENSE-GUARDRAILS            # PolyForm-NC 1.0.0 (가드 4개 파일)
├─ README.md
├─ CLAUDE.md                     # 절대 규칙 (마스킹·면책·한국어)
├─ pyproject.toml
├─ .env.example
├─ .gitignore
├─ src/
│   ├─ cli.py                    # 명령행 진입점
│   ├─ config.py                 # 환경변수·실행모드(mock/real)
│   ├─ tools/
│   │   ├─ schema.py             # Anthropic tool 정의
│   │   ├─ law_lookup.py         # [NC] 법령 검색·조문 조회
│   │   ├─ precedent_search.py   # [NC] 판례 검색·본문 조회
│   │   ├─ citation_guard.py     # [NC] 인용 환각 검증 + 캐시
│   │   ├─ ktx.py                # KTX 시간표 (출장 일정 있을 때)
│   │   └─ mocks.py              # mock 모드 응답
│   ├─ prompts/                  # 7단계 시스템 프롬프트
│   │   ├─ base.md               # 운영 래퍼 (마스킹·면책·인젝션 방어)
│   │   ├─ general.md            # 범용 6개 모드 분류
│   │   ├─ contract_review.md
│   │   ├─ criminal_opinion.md
│   │   ├─ unfair_dismissal.md
│   │   └─ rehab_creditor.md
│   ├─ agent/
│   │   ├─ orchestrator.py       # tool_use 루프 + prompt cache + 모드별 temperature
│   │   ├─ tool_router.py
│   │   └─ safety.py             # [NC] 마스킹·면책·인젝션 방어
│   └─ render/docx_render.py
├─ data/
│   ├─ samples/                  # 도메인별 가상 사건
│   └─ expected/                 # 회귀 테스트 기대 키워드
├─ skills/
│   └─ korean-domain-agent/
│       └─ SKILL.md              # Claude Code 인스톨러 스킬
└─ tests/                        # pytest 35개
```

`[NC]` = PolyForm Noncommercial 1.0.0 적용 파일.

---

## 도구 목록

| 도구 | 역할 | mock | real |
|---|---|---|---|
| `search_law` | 법령명·키워드 검색 | ✓ | ✓ |
| `get_law_article` | 특정 조문 본문 조회 | ✓ | ✓ |
| `search_precedent` | 판례 목록 검색 | ✓ | ✓ |
| `get_precedent_text` | 판례 본문 조회 | ✓ | ✓ |
| `verify_citation` | 인용 검증 (캐시 적용) | ✓ | ✓ |
| `recommend_ktx` | KTX 시간표 (법원 출장) | ✓ | ✓ |

---

## 안전 정책

- 모든 출력 마지막에 면책 문구 자동 삽입
- 9종 식별정보 자동 마스킹 (주민·전화·계좌·이메일·사업자번호·신용카드 등)
- 인젝션 의심 입력 감지 → ⚠ 경고 추가
- 본문 인용은 `verify_citation` 통과한 것만 허용
- KTX 결제 자동 클릭 금지

---

## 테스트

```bash
pytest -v
# 35 passed in 0.04s
```

- `test_smoke.py` — import + mock 모드 실행 + general 모드 분류
- `test_regression.py` — 4개 도메인 골든셋 키워드 회귀
- `test_safety.py` — 마스킹·면책·인젝션 단위
- `test_tools.py` — 인용 캐시·법령 파서·temperature 매핑·tools cache 마커

---

## 라이선스

본 키트는 두 라이선스로 배포됩니다.

| 범위 | 라이선스 | 적용 파일 | 상업 사용 |
|---|---|---|---|
| 프레임워크 (전체) | MIT | 루트 `LICENSE` | 자유 |
| 환각·보안 가드 | PolyForm Noncommercial 1.0.0 | `LICENSE-GUARDRAILS` | 별도 라이선스 필요 |

PolyForm-NC 적용 파일

```
src/agent/safety.py
src/tools/citation_guard.py
src/tools/law_lookup.py
src/tools/precedent_search.py
```

**비상업 사용 (무료)**: 개인 학습, 교육기관, 비영리, 정부, 공공 연구, 취미.
**상업 사용 (별도 라이선스)**: 로펌·기업 내부 도구화, SaaS 제공, 유료 컨설팅 결과물에 포함 등.

상업 라이선스 문의: **kimlawtech@gmail.com** · [speciai.team](https://speciai.team)

---

## 변경 이력

- **v0.2** — 범용 6모드 + prompt cache + 인용 캐시 + 마스킹 9종 + PolyForm-NC 가드 분리 + Claude Code 스킬 추가
- **v0.1** — 첫 동작 (mock + 4개 도메인 프롬프트)

---

## 면책

본 키트는 학습·실습·실무 보조용 베이스이며, 실제 의뢰인 사건·문서에 적용할 때는
변호사·공인노무사·세무사 등 자격 있는 전문가의 직접 검토를 거쳐야 합니다.
키트 사용으로 인한 결과에 대한 책임은 사용자에게 있습니다.

---

Made with care by [speciai.team](https://speciai.team) · 한국 도메인 AI 허브
