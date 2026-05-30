# korean-domain-agent

한국 법무·노무·세무 등 도메인 실무자가 본인 업무에 맞춰 커스터마이징할 수 있는 LLM 에이전트 키트.
법제처 OPEN API 기반 인용 환각 가드와 한국 식별정보 마스킹을 기본 탑재.

## 핵심 특징

- 6개 모드 자동 분류 — 작성·검토·퇴고·요약·리서치·자문
- 법제처 OPEN API 래퍼 + 환각 방지 인용 검증 (`verify_citation`)
- 한국 식별정보 자동 마스킹 — 주민·법인번호·전화·계좌·이메일·사업자번호·카드
- Anthropic prompt cache 적용 — system+tools 캐싱으로 입력 토큰 최대 90% 절감
- 모드별 temperature 자동 분리 (요약/리서치 0.0, 자문 0.3)
- 인용 검증 결과 메모이즈 — 동일 (kind, ref) 반복 호출 차단
- mock 모드 — API 키 없이 워크숍·교육 환경에서 즉시 동작
- python-docx Word 출력

## 라이선스 구성

| 범위 | 라이선스 | 적용 파일 |
|---|---|---|
| 전체 (프레임워크) | MIT | 루트 `LICENSE` |
| 보안·환각 가드 | PolyForm Noncommercial 1.0.0 | `LICENSE-GUARDRAILS` |

PolyForm-NC 적용 파일

```
src/agent/safety.py
src/tools/citation_guard.py
src/tools/law_lookup.py
src/tools/precedent_search.py
```

비상업(개인 학습·교육기관·비영리·정부·연구) 사용은 자유. 로펌·기업·SaaS 등 상업 사용은 별도 라이선스 필요.
문의: kimlawtech@gmail.com

## 폴더 구조

```
korean-domain-agent/
├─ LICENSE                       # MIT
├─ LICENSE-GUARDRAILS            # PolyForm-NC 1.0.0
├─ README.md
├─ CLAUDE.md
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
│   │   ├─ ktx.py
│   │   └─ mocks.py
│   ├─ prompts/
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
└─ tests/
```

`[NC]` = PolyForm-Noncommercial 적용.

## 5분 안에 시작

### 1. 설치

```bash
git clone https://github.com/kimlawtech/korean-domain-agent.git
cd korean-domain-agent
python -m venv .venv
source .venv/bin/activate
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

### 3. real 모드 (Anthropic + 법제처)

```bash
cp .env.example .env
# .env 편집:
# ANTHROPIC_API_KEY=sk-ant-...
# LAW_GO_KR_OC=발급받은_OC_ID
# AGENT_MODE=real

python -m src.cli run --agent contract_review \
  --input data/samples/contract_001.json \
  --out out/contract_001.docx --mode real
```

법제처 OC ID는 https://open.law.go.kr 회원가입 후 무료 발급.

### 4. 테스트

```bash
pytest -v
```

## 6개 작업 모드

`general` 모드에서 사건 데이터의 키 구성에 따라 자동 분류.

| 모드 | 분류 키 (예시) | 온도 |
|---|---|---|
| 작성 | (기본값) 당사자·청구취지·사실관계 | 0.2 |
| 검토 | `원문`, `초안`, `검토_대상` | 0.1 |
| 퇴고 | `퇴고_대상`, `문체_대상` | 0.1 |
| 요약 | `요약_대상`, `판결문` | 0.0 |
| 리서치 | `리서치_주제`, `research_topic` | 0.0 |
| 자문 | `질의`, `쟁점` | 0.3 |

명시 지정: case JSON에 `"작업_모드": "자문"` 추가.

## 도메인 추가

새 도메인 .md 1장 추가 → 즉시 동작.

```bash
# 1) 프롬프트 작성
vim src/prompts/my_domain.md     # 7단계 구조 (역할·과업·지침·목차·사례·형식·제약)

# 2) 샘플 JSON
vim data/samples/my_001.json

# 3) CLI에 등록
# src/cli.py 의 AGENTS 리스트에 "my_domain" 추가

# 4) 실행
python -m src.cli run --agent my_domain --input data/samples/my_001.json --out out/my.docx
```

도메인 .md 는 `base.md + general.md + my_domain.md` 순서로 합성되어 도메인 지시가 최종 우선.

## Claude Code 스킬

`~/.claude/skills/korean-domain-agent/SKILL.md` 가 설치되어 있으면 Claude Code 세션에서
`/korean-domain-agent` 호출로 다음을 자동화:

- 본 레포 clone + venv 설치
- 도메인 프롬프트 인터뷰 작성
- MCP 점검 (환각·보안 MCP 연결 여부 확인)
- 첫 산출물 mock 생성

스킬 설치 (수동):

```bash
mkdir -p ~/.claude/skills/korean-domain-agent
curl -o ~/.claude/skills/korean-domain-agent/SKILL.md \
  https://raw.githubusercontent.com/kimlawtech/korean-domain-agent/main/skills/SKILL.md
```

## 도구 (Tools)

| 도구 | 역할 |
|---|---|
| `search_law` | 법령명·키워드 검색 |
| `get_law_article` | 특정 조문 본문 조회 |
| `search_precedent` | 판례 목록 검색 |
| `get_precedent_text` | 판례 본문 조회 |
| `verify_citation` | 인용 검증 (캐시 적용) |
| `recommend_ktx` | KTX 시간표 (출장 일정 있을 때) |

## 안전 정책

- 모든 출력 마지막에 면책 문구 자동 삽입
- 9종 식별정보 자동 마스킹 (주민·전화·계좌·이메일·사업자번호·신용카드 등)
- 인젝션 의심 입력 감지 → ⚠ 경고 추가
- 본문 인용은 `verify_citation` 통과한 것만 허용
- KTX 결제 자동 클릭 금지

## 참고

본 키트는 학습/실습용 베이스이며, 실제 의뢰인 사건에 적용할 때는
변호사·공인노무사·세무사 등의 직접 검토를 거쳐야 합니다.

## 변경 이력

- v0.2 — 범용 6모드 + prompt cache + 인용 캐시 + 마스킹 9종 + PolyForm-NC 가드
- v0.1 — 첫 동작 (mock + 4개 도메인 프롬프트)
