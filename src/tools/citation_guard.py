# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 kimlawtech
# 본 파일은 PolyForm Noncommercial 1.0.0 라이선스로 배포됩니다.
# 비상업 사용만 허용. 상업 사용 문의: kimlawtech@gmail.com
# 라이선스 전문: LICENSE-GUARDRAILS
"""인용 환각 방지 가드.

LLM이 만들어 낼 수 있는 가짜 법령 번호·판례 번호를 잡아냅니다.
korean-law-mcp 의 citation hallucination guard 패턴을 따릅니다.
"""
from __future__ import annotations

import json
import re
from typing import Any

from .law_lookup import get_law_article
from .precedent_search import get_precedent_text


# (kind, ref, oc, mock) → 결과 JSON. 동일 인용 재조회 차단.
_VERIFY_CACHE: dict[tuple[str, str, str, bool], str] = {}


def clear_verify_cache() -> None:
    """테스트·세션 분리 시 호출."""
    _VERIFY_CACHE.clear()


def _cache_get(kind: str, ref: str, oc: str, mock: bool) -> dict[str, Any] | None:
    raw = _VERIFY_CACHE.get((kind, ref, oc, mock))
    if raw is None:
        return None
    return json.loads(raw)


def _cache_set(kind: str, ref: str, oc: str, mock: bool, value: dict[str, Any]) -> None:
    _VERIFY_CACHE[(kind, ref, oc, mock)] = json.dumps(value, ensure_ascii=False)


# 법령 인용: "근로기준법 제26조" 또는 "근로기준법 제26조 제1항"
LAW_REF_RE = re.compile(r"^(.+?)\s+(제\d+조(?:\s*제\d+항)?)$")
# 판례 사건번호: "2019다270163" 형태
CASE_NO_RE = re.compile(r"^\d{2,4}[가-힣]{1,3}\d+$")


def verify_citation(kind: str, ref: str, *, oc: str = "", mock: bool = True) -> dict[str, Any]:
    """
    kind = "law" : ref = "근로기준법 제26조"
    kind = "precedent" : ref = "2019다270163" 또는 "대법원 2019. 5. 10. 선고 2019다270163"
    """
    ref = ref.strip()
    cached = _cache_get(kind, ref, oc, mock)
    if cached is not None:
        return {**cached, "cache": "hit"}

    if kind == "law":
        m = LAW_REF_RE.match(ref)
        if not m:
            out = {"verified": False, "ref": ref, "reason": "법령 인용 형식 아님 (예: '근로기준법 제26조')"}
            _cache_set(kind, ref, oc, mock, out)
            return out
        law_name, article_no = m.group(1).strip(), m.group(2).strip()
        result = get_law_article(law_name, article_no, oc=oc, mock=mock)
        out = {
            "verified": bool(result.get("found")),
            "ref": ref,
            "law_name": result.get("law_name"),
            "article_no": result.get("article_no"),
            "snippet": (result.get("text") or "")[:120],
            "source": result.get("source"),
        }
        _cache_set(kind, ref, oc, mock, out)
        return out

    if kind == "precedent":
        # "대법원 2019. 5. 10. 선고 2019다270163" 에서 사건번호 추출
        m = re.search(r"\d{2,4}[가-힣]{1,3}\d+", ref)
        case_no = m.group(0) if m else ref
        if not CASE_NO_RE.match(case_no):
            out = {"verified": False, "ref": ref, "reason": "사건번호 형식 아님"}
            _cache_set(kind, ref, oc, mock, out)
            return out
        result = get_precedent_text(case_no, oc=oc, mock=mock)
        out = {
            "verified": bool(result.get("found")),
            "ref": ref,
            "case_no": result.get("case_no"),
            "case_name": result.get("case_name"),
            "court": result.get("court"),
            "decided_at": result.get("decided_at"),
            "summary": (result.get("summary") or "")[:120],
            "source": result.get("source"),
        }
        _cache_set(kind, ref, oc, mock, out)
        return out

    out = {"verified": False, "ref": ref, "reason": f"지원하지 않는 kind: {kind}"}
    _cache_set(kind, ref, oc, mock, out)
    return out


# 출력 본문에서 인용 의심 부분 추출
LAW_INLINE_RE = re.compile(r"([가-힣]{1,}법(?:률)?(?:\s*및\s*[가-힣]+에\s*관한\s*법률)?)\s*(제\d+조(?:\s*제\d+항)?)")
CASE_INLINE_RE = re.compile(r"(\d{2,4}[가-힣]{1,3}\d+)")


def extract_citations(text: str) -> list[tuple[str, str]]:
    """본문에서 (kind, ref) 쌍을 모두 추출."""
    out: list[tuple[str, str]] = []
    for m in LAW_INLINE_RE.finditer(text):
        out.append(("law", f"{m.group(1)} {m.group(2)}"))
    for m in CASE_INLINE_RE.finditer(text):
        out.append(("precedent", m.group(1)))
    # 중복 제거
    seen = set()
    uniq: list[tuple[str, str]] = []
    for kind, ref in out:
        key = (kind, ref)
        if key in seen:
            continue
        seen.add(key)
        uniq.append((kind, ref))
    return uniq


def audit_citations(text: str, *, oc: str = "", mock: bool = True) -> dict[str, Any]:
    """본문 전체를 훑어 인용 검증 결과를 요약."""
    pairs = extract_citations(text)
    results = [verify_citation(k, r, oc=oc, mock=mock) for k, r in pairs]
    suspicious = [r for r in results if not r["verified"]]
    return {
        "total": len(results),
        "verified": sum(1 for r in results if r["verified"]),
        "suspicious_refs": [r["ref"] for r in suspicious],
        "details": results,
    }
