# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 kimlawtech
# 본 파일은 PolyForm Noncommercial 1.0.0 라이선스로 배포됩니다.
# 비상업 사용만 허용. 상업 사용 문의: kimlawtech@gmail.com
# 라이선스 전문: LICENSE-GUARDRAILS
"""판례 목록·본문 조회."""
from __future__ import annotations

from typing import Any

from .mocks import PRECEDENTS


LAW_GO_KR_BASE = "http://www.law.go.kr/DRF"


def search_precedent(
    query: str,
    *,
    court: str | None = None,
    year_from: int | None = None,
    year_to: int | None = None,
    limit: int = 5,
    oc: str = "",
    mock: bool = True,
) -> dict[str, Any]:
    if mock or not oc:
        hits = []
        for case_no, info in PRECEDENTS.items():
            if query in info["case_name"] or query in info["summary"]:
                if court and court not in info["court"]:
                    continue
                year = int(info["decided_at"][:4])
                if year_from and year < year_from:
                    continue
                if year_to and year > year_to:
                    continue
                hits.append({
                    "case_no": info["case_no"],
                    "case_name": info["case_name"],
                    "court": info["court"],
                    "decided_at": info["decided_at"],
                    "summary": info["summary"][:80] + "...",
                })
        return {"query": query, "results": hits[:limit], "source": "mock"}

    params = {"OC": oc, "target": "prec", "type": "JSON", "query": query, "display": str(limit)}
    if court:
        params["curt"] = court
    if year_from:
        params["prncYdStart"] = f"{year_from}0101"
    if year_to:
        params["prncYdEnd"] = f"{year_to}1231"
    import httpx  # noqa: WPS433
    try:
        r = httpx.get(f"{LAW_GO_KR_BASE}/lawSearch.do", params=params, timeout=15.0)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        return {"query": query, "results": [], "source": "law.go.kr", "error": str(exc)}
    hits = []
    for item in (data.get("PrecSearch", {}).get("prec", []) or [])[:limit]:
        summary_raw = item.get("판시사항") or item.get("판결요지") or ""
        hits.append({
            "case_no": item.get("사건번호"),
            "case_name": item.get("사건명"),
            "court": item.get("법원명"),
            "decided_at": item.get("선고일자"),
            "summary": (summary_raw[:80] + "...") if summary_raw else "",
            "prec_id": item.get("판례일련번호") or item.get("ID"),
        })
    return {"query": query, "results": hits, "source": "law.go.kr"}


def _coalesce(d: dict[str, Any], *keys: str) -> str:
    for k in keys:
        v = d.get(k)
        if v:
            return str(v).strip()
    return ""


def get_precedent_text(case_no: str, *, oc: str = "", mock: bool = True) -> dict[str, Any]:
    if mock or not oc:
        info = PRECEDENTS.get(case_no.strip())
        if not info:
            return {"found": False, "case_no": case_no, "source": "mock"}
        return {
            "found": True,
            "case_no": info["case_no"],
            "case_name": info["case_name"],
            "court": info["court"],
            "decided_at": info["decided_at"],
            "summary": info["summary"],
            "applied_laws": info["applied_laws"],
            "source": "mock",
        }

    import httpx  # noqa: WPS433
    try:
        # 1) 사건번호로 먼저 검색 → 판례일련번호(ID) 확보
        search = httpx.get(
            f"{LAW_GO_KR_BASE}/lawSearch.do",
            params={"OC": oc, "target": "prec", "type": "JSON", "query": case_no, "display": "1"},
            timeout=15.0,
        )
        search.raise_for_status()
        s_data = search.json()
        items = (s_data.get("PrecSearch", {}).get("prec", []) or [])
        if not items:
            return {"found": False, "case_no": case_no, "source": "law.go.kr"}
        prec_id = items[0].get("판례일련번호") or items[0].get("ID") or case_no

        # 2) 본문 조회
        r = httpx.get(
            f"{LAW_GO_KR_BASE}/lawService.do",
            params={"OC": oc, "target": "prec", "type": "JSON", "ID": str(prec_id)},
            timeout=15.0,
        )
        r.raise_for_status()
        body = r.json()
    except Exception as exc:
        return {"found": False, "case_no": case_no, "source": "law.go.kr", "error": str(exc)}

    root = body.get("PrecService") or body.get("판례") or body
    if isinstance(root, list):
        root = root[0] if root else {}

    summary = _coalesce(root, "판시사항", "판결요지", "summary")
    applied = _coalesce(root, "참조조문", "applied_laws")
    return {
        "found": bool(summary or root),
        "case_no": _coalesce(root, "사건번호") or case_no,
        "case_name": _coalesce(root, "사건명"),
        "court": _coalesce(root, "법원명"),
        "decided_at": _coalesce(root, "선고일자"),
        "summary": summary,
        "applied_laws": [s.strip() for s in applied.split(",")] if applied else [],
        "source": "law.go.kr",
    }
