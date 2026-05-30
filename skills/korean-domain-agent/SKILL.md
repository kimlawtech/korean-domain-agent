---
name: korean-domain-agent
description: 한국 도메인 특화 LLM 에이전트 키트(korean-domain-agent)를 설치하고 사용자 도메인에 맞춰 커스터마이징하는 스킬. 호출 시 ① 레포 clone+설치, ② 환각·보안 MCP 점검, ③ 도메인 프롬프트 인터뷰 작성, ④ 첫 mock 산출물 생성을 순서대로 진행. 호출 시 사용자가 “법률·노무·세무 등 도메인 에이전트 설치” “korean-domain-agent 설치” “법률 에이전트 도메인 추가” 등을 요청할 때 발동.
---

# korean-domain-agent — 도메인 에이전트 설치·커스터마이징 스킬

본 스킬은 https://github.com/kimlawtech/korean-domain-agent 키트를
사용자 환경에 설치하고, 사용자 도메인 영역에 맞춰 프롬프트를 생성한다.

## 0. 발동 시 점검 순서 (반드시 이 순서)

1) 레포 설치 여부 확인 → 없으면 clone + venv + pip install
2) 환각·보안 MCP 점검 (korean-contracts 등) → 미연결 시 안내
3) 사용자 도메인 인터뷰 → 프롬프트 파일 생성
4) 샘플 JSON 생성 + mock 실행 시연

## 1. 레포 설치 점검

기본 설치 경로: `~/dev/korean-domain-agent` (사용자가 다른 경로 원하면 변경).

```bash
# 1) 존재 확인
test -d ~/dev/korean-domain-agent && echo "installed" || echo "not_installed"

# 2) 미설치 시
mkdir -p ~/dev && cd ~/dev
git clone https://github.com/kimlawtech/korean-domain-agent.git
cd korean-domain-agent
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env

# 3) 설치 확인
.venv/bin/python -m pytest -q
```

35개 테스트가 통과하면 설치 성공.

## 2. 환각·보안 MCP 점검 (필수)

본 키트의 인용 검증·마스킹은 PolyForm-NC 라이선스 가드 모듈로 1차 보호하지만,
사용자가 추가 MCP(예: korean-contracts)를 연결하면 보호 레이어가 강화된다.

점검 절차:

1) 사용자 환경의 MCP 목록 확인
   ```bash
   ls ~/.claude/mcp_servers/ 2>/dev/null || echo "no mcp_servers dir"
   cat ~/.claude/config.json 2>/dev/null | grep -A2 mcpServers || true
   ```
2) `korean-contracts` MCP 가 보이면 연결 상태 양호.
3) 미연결 시 사용자에게 다음 1줄 안내 후 진행 여부 묻기:

   "환각·보안 MCP(korean-contracts)가 연결되어 있지 않습니다.
    본 키트의 기본 가드(citation_guard·safety)만으로 진행할까요?
    아니면 MCP 먼저 설치하고 진행할까요?"

4) MCP 설치를 선택하면 `/security` 스킬(글로벌)을 호출하도록 안내.

## 3. 도메인 인터뷰

다음 6개 질문을 순서대로. 각 질문은 1줄로 묻고 답을 받은 즉시 다음으로.

질문 1) 도메인 이름(영문 식별자, snake_case)
        예: `tax_objection`, `realestate_contract`, `medical_malpractice`
질문 2) 한글 표시명 (예: 조세불복 청구, 부동산 계약 검토)
질문 3) 변호사·전문가 페르소나 1줄
        예: "조세소송 15년 경력 변호사"
질문 4) 핵심 작업 모드 (작성 / 검토 / 퇴고 / 요약 / 리서치 / 자문 중 1개 또는 다수)
질문 5) 필수 적용 법령 1~3개 (예: 국세기본법 제55조, 행정심판법 제13조)
질문 6) 산출물 표준 양식 목차 (제1. / 가. / (1) 형식으로 4~6 항목)

답변이 모이면 다음 템플릿으로 `src/prompts/{도메인이름}.md` 작성:

```markdown
[1단계] 역할(맥락)
당신은 한국 {분야} 분야 {연차}년 경력의 {직역}입니다.
전문성:
    {핵심 법령 1~3개} 실무.
    {도메인 특수 경험}.
작업 수행 방식:
    {1줄}.
    {1줄}.

사건 맥락:
    사건 유형: {한글 표시명}
    당사자: {표시 패턴}
    {기타 도메인 필드}

[2단계] 과업 설명
{산출물 1줄 정의}.

[3단계] 지침
1) 정보 수집 — {핵심 항목}.
2) 사실관계 정리 — 시간순.
3) 법리 검토:
   {적용 법령 1}
   {적용 법령 2}
4) 주장 구성 — 사실 → 법리 → 증거 → 결론.

도구 사용:
- 적용 조문은 get_law_article 으로 받아 인용.
- 인용 직전 verify_citation 호출.
- 관련 판례는 search_precedent 으로 1~2건만.

[4단계] 목차
{사용자가 답한 표준 양식 4~6 항목 그대로}

[5단계] 작성 사례
{사용자에게 짧은 예시 받기 또는 생략}

[6단계] 작성 형식
날짜: YYYY. M. D.
금액: 금 ○○○원 (세자리 콤마)
목차: 제1. / 가. / (1)
종결: -습니다, -입니다
증거: [갑 제○호증 ○○○ 참조]
법령: [법령명] 제○조 제○항

[7단계] 추가 제약사항
정보 범위: 사용자가 제공한 정보만.
형식 금지: ** 금지, JSON 금지, 글머리 기호 금지.

품질 검증 체크리스트:
[ ] {질문 6에서 받은 항목 1}
[ ] {항목 2}
[ ] {적용 법령 verify_citation 통과}
[ ] 면책 문구 자동 삽입

자기 비평: 적용 법령·판례가 검증 통과했는지, 사용자 제공 사실 범위를 벗어나지 않았는지 검토.
```

작성 후 `src/cli.py` 의 `AGENTS` 리스트에 도메인 이름 추가.

## 4. 샘플 JSON 생성

사용자 도메인 필드를 기준으로 `data/samples/{도메인}_001.json` 생성.
실제 의뢰인 정보는 입력하지 말고, 모든 식별정보는 `[성명]`, `[주민]`, `[연락처]`, `[주소]` 로 마스킹된 가상값 사용.

## 5. 첫 mock 실행

```bash
cd ~/dev/korean-domain-agent
source .venv/bin/activate
python -m src.cli run --agent {도메인이름} \
  --input data/samples/{도메인}_001.json \
  --out out/{도메인}_001.docx \
  --mode mock
```

산출물 .docx 가 생성되면 사용자에게 경로 안내. 추가 도메인 작업 의향 묻기.

## 6. real 모드 전환 안내

mock 검증 후 real 모드로 가려면:

1) Anthropic 콘솔(https://console.anthropic.com)에서 API 키 발급
2) 법제처(https://open.law.go.kr) 회원가입 후 OC ID 발급
3) `.env` 편집:
   ```
   ANTHROPIC_API_KEY=sk-ant-...
   LAW_GO_KR_OC={OC_ID}
   AGENT_MODE=real
   ```
4) 동일 명령 재실행

## 7. 라이선스 안내 (사용자 고지)

본 키트는 두 라이선스로 배포됩니다:

- 프레임워크: MIT (자유 사용·상업 사용 포함)
- 보안·환각 가드 4개 파일: PolyForm Noncommercial 1.0.0
  (개인·교육·연구·비영리·정부 사용 무료, 상업 사용 별도 라이선스 필요)

상업 사용 문의: kimlawtech@gmail.com

## 8. 응답 스타일

- 한국어, 요약체.
- 단계별 진행 — 한 단계 완료 후 다음 단계.
- 사용자 답변이 불명확하면 1줄로 재확인.
- 산출물 경로는 절대경로로 명시.
