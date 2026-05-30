"""에이전트 본체 — Anthropic tool_use 루프 + 모의 모드.

real 모드는 anthropic SDK 의 messages.create + tool_use 응답 처리.
mock 모드는 SDK 없이 도메인별로 미리 짜둔 “골격 응답”을 만들어
도구 호출과 검증 흐름을 그대로 따라갑니다 (워크숍/오프라인 데모용).
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from ..config import Config, load_config
from ..tools.schema import TOOLS
from .safety import safe_postprocess
from .tool_router import dispatch
from ..tools.citation_guard import audit_citations


PROMPTS_DIR = Path(__file__).resolve().parent.parent / "prompts"


# 모드별 temperature — 사실·법령 인용이 많은 모드는 낮게, 자문/전략은 약간 높게.
_TEMPERATURE_BY_MODE = {
    "작성": 0.2,
    "검토": 0.1,
    "퇴고": 0.1,
    "요약": 0.0,
    "리서치": 0.0,
    "자문": 0.3,
}


def _attach_tools_cache_control(tools: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """tools 배열의 마지막 항목에 cache_control 부착.

    Anthropic prompt cache 는 cache 마커가 붙은 블록까지의 prefix 를 캐싱한다.
    tools 정의는 호출 간 변경되지 않으므로 마지막 tool 에만 마커를 달면
    전체 tools 블록이 캐시 대상이 된다.
    """
    if not tools:
        return tools
    out = [dict(t) for t in tools]
    out[-1] = {**out[-1], "cache_control": {"type": "ephemeral"}}
    return out


def load_system_prompt(agent_name: str | None) -> str:
    """시스템 프롬프트 합성.

    agent_name 이 None 또는 "general" 이면 base + general 만 사용.
    그 외에는 base + general + 도메인 .md 순서로 누적 (도메인 지시 우선).
    """
    base = (PROMPTS_DIR / "base.md").read_text(encoding="utf-8")
    general = (PROMPTS_DIR / "general.md").read_text(encoding="utf-8")
    if not agent_name or agent_name == "general":
        return base + "\n\n" + general
    domain = (PROMPTS_DIR / f"{agent_name}.md").read_text(encoding="utf-8")
    return base + "\n\n" + general + "\n\n" + domain


def fill_variables(template: str, values: dict[str, Any]) -> str:
    out = template
    for k, v in values.items():
        out = out.replace("{" + k + "}", str(v))
    return out


# ---------- mock 시뮬레이션 ----------

def _simulate_unfair_dismissal(case: dict[str, Any], cfg: Config) -> str:
    """부당해고 이유서 — 도구 호출 흐름까지 재현."""
    # 1) 법령 조회
    law_26 = dispatch("get_law_article", {"law_name": "근로기준법", "article_no": "제26조"}, mock=cfg.is_mock)
    law_27 = dispatch("get_law_article", {"law_name": "근로기준법", "article_no": "제27조"}, mock=cfg.is_mock)
    law_23 = dispatch("get_law_article", {"law_name": "근로기준법", "article_no": "제23조 제1항"}, mock=cfg.is_mock)
    # 2) 판례 검색
    prec = dispatch("search_precedent", {"query": "해고", "court": "대법원", "limit": 2}, mock=cfg.is_mock)
    # 3) 인용 검증
    for ref in ("근로기준법 제23조", "근로기준법 제26조", "근로기준법 제27조"):
        dispatch("verify_citation", {"kind": "law", "ref": ref}, mock=cfg.is_mock)

    body = f"""부당해고 구제신청 이유서

사    건: 부당해고 구제신청
신 청 인: {case.get('신청인_성명')} / {case.get('신청인_주소')}
피신청인: {case.get('회사명')} / 대표자 {case.get('대표자_성명')}
{case.get('관할_노동위원회')} 귀중

신 청 취 지 (원직복직 청구)

1. 피신청인이 {case.get('해고_효력일')}자로 신청인에 대하여 한 해고는 부당해고임을 인정한다.
2. 피신청인은 신청인을 원직에 복직시키고, 해고기간 동안 신청인이 정상적으로
   근무하였더라면 받을 수 있었던 임금 상당액을 지급하라.

라는 판정을 구합니다.

신 청 이 유

제1. 당사자의 관계
   가. 신청인은 {case.get('입사일')} 피신청인에 입사하여 {case.get('직위')} 로 근무하였습니다.
   나. 피신청인은 상시 {case.get('상시_근로자_수')}명을 사용하는 사용자입니다.

제2. 근로관계의 내용
   신청인은 입사 이래 {case.get('소속부서')} 소속으로 월 급여 금 {case.get('월급여')}원을 지급받았습니다.

제3. 해고의 경위
   가. 해고 통보
   피신청인은 {case.get('해고_통보일')} 신청인에게 {case.get('통보_방법')} 으로 해고를 통보하고,
   {case.get('해고_효력일')} 자로 해고하였습니다.
   해고사유로는 "{case.get('해고_사유')}"를 들고 있습니다.

   나. 해고 전 절차
   피신청인은 신청인에게 어떠한 사전 소명 기회도 부여하지 않았습니다.

제4. 해고의 부당성
   가. 절차적 부당성
   (1) 해고예고 위반 (근로기준법 제26조)
   {law_26.get('text', '확인 필요')}
   피신청인은 {case.get('해고_통보일')} 통보 후 {case.get('해고_효력일')} 해고하여
   30일 전 예고 의무를 위반하였습니다.

   (2) 서면통지 위반 (근로기준법 제27조)
   {law_27.get('text', '확인 필요')}
   피신청인은 서면이 아닌 {case.get('통보_방법')} 으로 통보하여 위 의무를 위반하였습니다.

   나. 실체적 부당성 (근로기준법 제23조 제1항)
   {law_23.get('text', '확인 필요')}
   피신청인이 들고 있는 "{case.get('해고_사유')}"는 객관적 자료에 부합하지 않으며,
   사회통념상 고용관계를 계속할 수 없을 정도의 사유에 해당하지 아니합니다.

제5. 적용 법조 및 판례
   근로기준법 제23조 제1항, 제26조, 제27조"""

    # 검증된 판례만 인용
    if prec.get("results"):
        first = prec["results"][0]
        body += f"\n   {first['court']} {first['decided_at']} 선고 {first['case_no']} 판결\n"
        body += f'   "{first["summary"]}"\n'

    body += """
제6. 결론
   따라서 본 건 해고는 절차적·실체적으로 모두 부당하므로 신청취지 기재와 같은 판정을 구합니다.

첨 부 서 류
   1. 갑 제1호증  근로계약서 사본
   2. 갑 제2호증  해고 통보 카카오톡 캡처
"""
    return body


def _simulate_contract_review(case: dict[str, Any], cfg: Config) -> str:
    law_390 = dispatch("get_law_article", {"law_name": "민법", "article_no": "제390조"}, mock=cfg.is_mock)
    law_393 = dispatch("get_law_article", {"law_name": "민법", "article_no": "제393조 제2항"}, mock=cfg.is_mock)
    return f"""계약서 위험 검토 의견서

의뢰인: {case.get('회사명')}    검토 대상: {case.get('계약_종류')} ({case.get('상대회사명')}과의 계약)

검 토 결 과 요 약

1. HIGH 위험 3건, MEDIUM 2건, LOW 1건.
2. 협상 우선순위 상위: 손해배상 상한 / 일방 해지권 / IP 귀속.

상 세 검 토

제3조 (단가 조정) — HIGH
   원문: 시장가격 변동을 이유로 일방적으로 단가 조정 가능.
   사유: 매수인의 비용 예측 불가, 분쟁 가능성.
   근거: 민법 제390조 (채무불이행)
   "{law_390.get('text', '확인 필요')}"
   권고 대안: "단가 조정은 양 당사자 서면 합의로만 가능하다."

제12조 (손해배상 상한 미설정) — HIGH
   원문: 손해배상 상한 정하지 아니함.
   사유: 매수인 무한책임.
   근거: 민법 제393조 제2항
   "{law_393.get('text', '확인 필요')}"
   권고 대안: "본 계약 위반으로 인한 손해배상의 상한은 직전 12개월 매매대금의 100%로 한다."

제7조 (지식재산권 일방 귀속) — HIGH
   권고 대안: 공동개발 결과물의 IP는 양 당사자 공동 보유 또는 라이선스 협의.

제5조 (검수 5일) — MEDIUM
   권고 대안: "검수 기간은 인도일로부터 30일로 한다."

제15조 (전속관할) — MEDIUM
   권고 대안: "관할은 원고의 주소지 법원으로 한다."

제9조 (해지 통지) — LOW
   권고 대안: 통지 기간을 90일로 연장.

협 상 카 드
   사수 항목: 손해배상 상한, IP 공동 보유.
   양보 가능: 검수 기간 일부 단축.
"""


def _simulate_criminal_opinion(case: dict[str, Any], cfg: Config) -> str:
    law_260 = dispatch("get_law_article", {"law_name": "형법", "article_no": "제260조 제1항"}, mock=cfg.is_mock)
    return f"""변 호 인 의 견 서

사    건: {case.get('사건번호')} {case.get('적용_죄명')}
피 고 인: {case.get('피고인_성명')}
변 호 인: {case.get('변호인_성명')}

I. 사 건 의 개 요
   {case.get('사건_개요')}

II. 변호인의 의견

   1. 공소사실의 요지
   {case.get('적용_죄명')} 혐의로 기소되었습니다.

   2. 변호인의 주장
   가. 사실관계 다툼
   피고인은 {case.get('피고인_진술_요지')}.
   객관 자료에 의하면 피해자 진술과의 사이에 다음의 차이가 있습니다.

   나. 법리상 다툼
   형법 제260조 제1항
   "{law_260.get('text', '확인 필요')}"

III. 양 형 에 관 한 의 견

   1. 감경 사유
   가. 합의 진행 상황: {case.get('합의_진행_상황')}
   나. 초범 또는 동종 전과 부재.

   2. 가중 사유 검토 결과 특이사항 없음.

IV. 결    론
   본 사건은 사실관계의 핵심 쟁점에 다툼이 있고, 양형상 다수의 감경 사유가 존재하므로
   적정한 양형에 따른 판단을 구합니다.
"""


def _simulate_rehab_creditor(case: dict[str, Any], cfg: Config) -> str:
    law_141 = dispatch("get_law_article", {"law_name": "채무자 회생 및 파산에 관한 법률", "article_no": "제141조 제1항"}, mock=cfg.is_mock)
    return f"""회 생 채 권 시 · 부 인 의 견 서

사    건: {case.get('사건번호')}  회생
채 권 자: {case.get('채권자명')}
{case.get('관할_법원')} 귀중

I. 채 권 의 개 요
   채권 발생 원인: {case.get('채권_원인')}
   채권액: 금 {case.get('채권액')}원
   담보 여부: {case.get('담보_여부')}
   담보 목적물: {case.get('담보_목적물')}

II. 채 권 의 분 류 에 관 한 의 견
   1. 우리 채권의 성격
   본 채권은 별지 부동산에 근저당권이 설정된 채권으로서 회생담보권에 해당합니다.
   ({case.get('담보_목적물')} 에 대한 근저당권을 보유합니다.)

   2. 적용 법조 및 근거
   채무자 회생 및 파산에 관한 법률 제141조 제1항
   "{law_141.get('text', '확인 필요')}"

III. 채 권 액 에 관 한 의 견
   원금·이자·지연손해금을 각각 분리하여 시인 의견을 제출합니다.

IV. 우 선 순 위 에 관 한 의 견
   회생담보권으로 시인되어야 하며, 일반회생채권자보다 우선 변제 받아야 합니다.

V. 결    론
   본 채권은 회생담보권에 해당하므로, 관리인의 이의를 기각하고 시인하여 주실 것을 요청합니다.
"""


def _infer_mode(case: dict[str, Any]) -> str:
    """case 데이터에서 작업 모드 추론."""
    explicit = (case.get("작업_모드") or case.get("mode") or "").strip()
    if explicit in {"작성", "검토", "퇴고", "요약", "리서치", "자문"}:
        return explicit
    keys = set(case.keys())
    if keys & {"원문", "초안", "검토_대상", "review_target", "draft"}:
        return "검토"
    if keys & {"퇴고_대상", "문체_대상"}:
        return "퇴고"
    if keys & {"질의", "쟁점", "question", "issue"}:
        return "자문"
    if keys & {"리서치_주제", "research_topic"}:
        return "리서치"
    if keys & {"요약_대상", "summary_target", "판결문"}:
        return "요약"
    return "작성"


def _simulate_general(case: dict[str, Any], cfg: Config) -> str:
    """범용 mock 시뮬레이터 — 모드별 골격 본문 생성."""
    mode = _infer_mode(case)
    title = case.get("사건명") or case.get("title") or case.get("문서_유형") or "법률 문서"
    party = case.get("의뢰인") or case.get("당사자") or case.get("신청인_성명") or "[당사자]"
    summary = case.get("사건_개요") or case.get("개요") or case.get("질의") or case.get("원문") or ""

    if mode == "작성":
        return f"""{title}

의 뢰 인: {party}
작 성 모 드: 작성 (범용)

제1. 사 건 의 개 요
   {summary or '[확인 필요] 사건 개요가 제공되지 않았습니다.'}

제2. 사 실 관 계
   가. 다툼 없는 사실
   {case.get('다툼없는_사실', '[확인 필요]')}
   나. 다툼 있는 사실
   {case.get('다툼있는_사실', '[확인 필요]')}

제3. 적 용 법 리
   본 사건에 적용되는 법령·판례는 사건 분야에 따라 별도로 검증 후 인용합니다.
   현 단계에서는 사용자 제공 정보 범위 내에서 골격만 제시합니다.

제4. 결    론
   사용자 제공 사실관계를 토대로 한 초안이며, 청구취지·결론은 담당 변호사가 확정합니다.
"""

    if mode == "검토":
        return f"""법 률 문 서 검 토 의 견

검 토 대 상: {title}
의 뢰 인: {party}
작 성 모 드: 검토

제1. 검 토 결 과 요 약
   사실관계 정합성, 법리 정확성, 논리 구조, 입증 충분성, 리스크 항목별로
   각각 평가하였으며 상세 결과는 아래와 같습니다.

제2. 항 목 별 평 가
   가. 사실관계 정합성: [확인 필요]
   나. 법리 정확성: [확인 필요]
   다. 논리 구조: [확인 필요]
   라. 입증 충분성: [확인 필요]
   마. 리스크: [확인 필요]

제3. 보 완 제 안
   (1) 사용자 제공 원문을 기준으로 한 구체 보완 사항은 도메인 분야 확정 후 제시합니다.

제4. 상 대 방 예 상 반 박
   본 의견서 작성 시점에서는 사용자 제공 사실관계만으로 반박을 추정합니다.
"""

    if mode == "퇴고":
        return f"""법 률 문 서 퇴 고 의 견

대 상 문 서: {title}
작 성 모 드: 퇴고

제1. 총    평
   톤·구조·강점에 대한 3줄 평가는 원문 입수 후 작성합니다.

제2. 체 크 포 인 트 평 가
   가. 한자어·일본어식 표현 순화: [확인 필요]
   나. 청구취지 단위·이율·기산일: [확인 필요]
   다. 주어·서술어 일치: [확인 필요]
   라. 수동태 과다: [확인 필요]
   마. 장문 분할: [확인 필요]
   바. 접속사 반복: [확인 필요]
   사. 판례 인용 형식: [확인 필요]
   아. 결론 문단: [확인 필요]

제3. 금 기 표 현 검 출
   "사료되는 바입니다", "당원으로서는", "~에 있어" 등 검출 결과는 원문 입수 후 표시.

제4. 지 적 별 수 정 제 안
   원문/수정안/사유는 원문 입수 후 작성. 법적 결론·청구취지는 변경하지 않습니다.
"""

    if mode == "요약":
        return f"""법 률 문 서 요 약

대 상 문 서: {title}
작 성 모 드: 요약

제1. 문 서 식 별
   {summary or '[확인 필요]'}

제2. 핵 심 사 실
   사용자 제공 본문에서 추출한 사실 목록은 본 골격 단계에서는 [확인 필요]로 표기합니다.

제3. 주 요 쟁 점 및 결 론
   쟁점 추출 후 작성.

제4. 인 용 법 령 및 판 례
   원문에서 인용된 법령·판례를 verify_citation 통과 후 나열합니다.

제5. 변 호 사 추 가 확 인 사 항
   원문 입수 후 작성.
"""

    if mode == "리서치":
        topic = case.get("리서치_주제") or case.get("research_topic") or summary or "[확인 필요]"
        return f"""법 률 리 서 치 결 과

리 서 치 주 제: {topic}
작 성 모 드: 리서치

제1. 검 색 쟁 점
   {topic}

제2. 관 련 법 령 및 조 문
   본 단계에서는 사용자 제공 정보만으로 골격을 제시하며,
   적용 법령은 get_law_article 호출 결과 및 verify_citation 통과 후 본문 인용합니다.

제3. 관 련 판 례
   search_precedent 호출 결과를 통해 사건번호·판시사항 형식으로 인용합니다.

제4. 학 설 및 해 석 론
   다수설·소수설 구분 후 작성.

제5. 실 무 상 유 의 점
   사용자 사건 적용 시 유의 사항 정리.
"""

    # 자문
    return f"""법 률 자 문 의 견

의 뢰 인: {party}
질    의: {summary or '[확인 필요]'}
작 성 모 드: 자문

제1. 사 실 관 계 정 리
   가. 다툼 없는 사실: {case.get('다툼없는_사실', '[확인 필요]')}
   나. 다툼 있는 사실: {case.get('다툼있는_사실', '[확인 필요]')}

제2. 법 적 쟁 점
   {case.get('쟁점', '[확인 필요]')}

제3. 쟁 점 별 적 용 법 리
   본 골격 단계에서는 적용 법령·판례를 도구로 검증한 뒤 본문에 인용합니다.

제4. 유 리 · 불 리 사 실
   가. 우리 측 유리 사실: [확인 필요]
   나. 우리 측 불리 사실: [확인 필요]

제5. 권 장 전 략
   가. 주위적: [확인 필요]
   나. 예비적: [확인 필요]

제6. 추 가 확 보 가 필 요 한 증 거
   [확인 필요]
"""


_SIMULATORS = {
    "unfair_dismissal": _simulate_unfair_dismissal,
    "contract_review": _simulate_contract_review,
    "criminal_opinion": _simulate_criminal_opinion,
    "rehab_creditor": _simulate_rehab_creditor,
    "general": _simulate_general,
}


# ---------- 진입점 ----------

def run_agent(
    agent_name: str | None,
    case: dict[str, Any],
    *,
    cfg: Config | None = None,
) -> dict[str, Any]:
    """에이전트 1회 실행. agent_name 미지정/`general` 시 범용 모드."""
    cfg = cfg or load_config()
    effective_name = agent_name or "general"

    if cfg.is_mock or not cfg.anthropic_api_key:
        # mock: 도메인 시뮬레이터 우선, 없으면 범용 시뮬레이터로 fallback
        sim = _SIMULATORS.get(effective_name, _simulate_general)
        body = sim(case, cfg)
        body = safe_postprocess(body, user_input=json.dumps(case, ensure_ascii=False))
        audit = audit_citations(body, oc=cfg.law_go_kr_oc, mock=True)
        tools_used = _MOCK_TOOLS_USED.get(effective_name, _MOCK_TOOLS_USED["general"])
        return {"text": body, "tools_used": tools_used, "audit": audit, "mode": "mock"}

    # real: anthropic SDK 사용
    from anthropic import Anthropic  # 지연 import

    client = Anthropic(api_key=cfg.anthropic_api_key)
    system_text = fill_variables(load_system_prompt(effective_name), case)
    user_doc = json.dumps(case, ensure_ascii=False, indent=2)

    # prompt cache: system 과 tools 를 ephemeral 캐시로 — 5분 TTL.
    # 동일 (system_text, tools) 가 반복되는 도구 루프 N회·연속 호출에서 90%+ 비용 절감.
    system_blocks = [
        {"type": "text", "text": system_text, "cache_control": {"type": "ephemeral"}}
    ]
    tools_cached = _attach_tools_cache_control(TOOLS)
    temperature = _TEMPERATURE_BY_MODE.get(_infer_mode(case), 0.2)

    messages: list[dict[str, Any]] = [
        {
            "role": "user",
            "content": (
                "<<<DOCUMENT>>>\n" + user_doc + "\n<<<END>>>\n\n"
                "위 사건 데이터로 산출물을 작성해주세요. "
                "필요한 법령·판례는 도구로 검증한 후 인용해주세요."
            ),
        }
    ]
    tools_used: list[str] = []

    for _ in range(8):  # 최대 8회 도구 루프
        resp = client.messages.create(
            model=cfg.anthropic_model,
            max_tokens=8000,
            system=system_blocks,
            tools=tools_cached,
            messages=messages,
            temperature=temperature,
        )
        if resp.stop_reason != "tool_use":
            text = "".join(getattr(b, "text", "") for b in resp.content)
            text = safe_postprocess(text, user_input=user_doc)
            audit = audit_citations(text, oc=cfg.law_go_kr_oc, mock=False)
            return {"text": text, "tools_used": tools_used, "audit": audit, "mode": "real"}

        # tool_use 처리
        tool_results = []
        assistant_blocks = [b.model_dump() if hasattr(b, "model_dump") else dict(b) for b in resp.content]
        for block in resp.content:
            if getattr(block, "type", "") == "tool_use":
                tools_used.append(block.name)
                result = dispatch(block.name, dict(block.input), oc=cfg.law_go_kr_oc, mock=False)
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })
        messages.append({"role": "assistant", "content": assistant_blocks})
        messages.append({"role": "user", "content": tool_results})

    raise RuntimeError("도구 호출 8회를 초과했습니다.")


_MOCK_TOOLS_USED = {
    "unfair_dismissal": [
        "get_law_article", "get_law_article", "get_law_article",
        "search_precedent", "verify_citation", "verify_citation", "verify_citation"
    ],
    "contract_review": ["get_law_article", "get_law_article"],
    "criminal_opinion": ["get_law_article"],
    "rehab_creditor": ["get_law_article"],
    "general": [],
}
