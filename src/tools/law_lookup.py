# SPDX-License-Identifier: PolyForm-Noncommercial-1.0.0
# Copyright (c) 2026 kimlawtech
# 본 파일은 PolyForm Noncommercial 1.0.0 라이선스로 배포됩니다.
# 비상업 사용만 허용. 상업 사용 문의: kimlawtech@gmail.com
# 라이선스 전문: LICENSE-GUARDRAILS
"""법령 검색·조문 조회.

mock 모드: src/tools/mocks.py 의 인덱스에서 검색.
real 모드: 법제처 OPEN API (open.law.go.kr/DRF/lawSearch.do, lawService.do).
"""
from __future__ import annotations

import re
from typing import Any

from .mocks import LAW_INDEX, normalize_law_name


LAW_GO_KR_BASE = "http://www.law.go.kr/DRF"


def search_law(query: str, *, limit: int = 5, oc: str = "", mock: bool = True) -> dict[str, Any]:
    """법령 목록 검색."""
    canonical = normalize_law_name(query)

    if mock or not oc:
        hits = []
        for name, info in LAW_INDEX.items():
            if canonical in name or query in name:
                hits.append({
                    "law_name": info["law_name"],
                    "law_id": info["law_id"],
                    "ministry": info["ministry"],
                    "effective_date": info["effective_date"],
                })
        return {"query": query, "canonical": canonical, "results": hits[:limit], "source": "mock"}

    import httpx  # noqa: WPS433
    params = {"OC": oc, "target": "law", "type": "JSON", "query": canonical, "display": str(limit)}
    try:
        r = httpx.get(f"{LAW_GO_KR_BASE}/lawSearch.do", params=params, timeout=15.0)
        r.raise_for_status()
        data = r.json()
    except Exception as exc:
        return {"query": query, "canonical": canonical, "results": [], "source": "law.go.kr", "error": str(exc)}
    hits = []
    for item in (data.get("LawSearch", {}).get("law", []) or [])[:limit]:
        hits.append({
            "law_name": item.get("법령명한글"),
            "law_id": item.get("법령ID") or item.get("법령일련번호"),
            "ministry": item.get("소관부처명"),
            "effective_date": item.get("시행일자"),
        })
    return {"query": query, "canonical": canonical, "results": hits, "source": "law.go.kr"}


_ARTICLE_NO_RE = re.compile(r"제\s*(\d+)\s*조(?:\s*제\s*(\d+)\s*항)?")


def _parse_article_no(article_no: str) -> tuple[int | None, int | None]:
    """'제26조 제1항' → (26, 1), '제23조' → (23, None)."""
    m = _ARTICLE_NO_RE.search(article_no)
    if not m:
        return None, None
    return int(m.group(1)), int(m.group(2)) if m.group(2) else None


def _extract_article_text(law_json: dict[str, Any], target_no: int, target_para: int | None) -> str | None:
    """법제처 lawService.do JSON 응답에서 특정 조·항 본문 추출.

    응답 구조: {"법령": {"조문": {"조문단위": [{"조문번호": "26", "조문내용": "...",
                                             "항": [{"항번호": "1", "항내용": "..."}]}]}}}
    필드명은 시기·법령별 편차가 있어 안전하게 .get 으로 접근.
    """
    root = law_json.get("법령") or law_json
    jomun = root.get("조문") or {}
    units = jomun.get("조문단위") or jomun.get("조") or []
    if isinstance(units, dict):
        units = [units]
    for unit in units:
        try:
            unit_no = int(str(unit.get("조문번호") or unit.get("조번호") or "").strip() or 0)
        except ValueError:
            continue
        if unit_no != target_no:
            continue
        if target_para is None:
            text = unit.get("조문내용") or unit.get("내용") or ""
            return str(text).strip() or None
        paras = unit.get("항") or []
        if isinstance(paras, dict):
            paras = [paras]
        for para in paras:
            try:
                para_no = int(str(para.get("항번호") or "").strip() or 0)
            except ValueError:
                continue
            if para_no == target_para:
                text = para.get("항내용") or para.get("내용") or ""
                return str(text).strip() or None
    return None


def get_law_article(law_name: str, article_no: str, *, oc: str = "", mock: bool = True) -> dict[str, Any]:
    """특정 법령의 조문 본문 조회."""
    canonical = normalize_law_name(law_name)

    if mock or not oc:
        info = LAW_INDEX.get(canonical)
        if not info:
            return {"found": False, "law_name": canonical, "article_no": article_no, "source": "mock"}
        text = info["articles"].get(article_no)
        if not text:
            for k, v in info["articles"].items():
                if k.startswith(article_no):
                    text = v
                    article_no = k
                    break
        return {
            "found": text is not None,
            "law_name": canonical,
            "article_no": article_no,
            "text": text or "",
            "ministry": info["ministry"],
            "effective_date": info["effective_date"],
            "source": "mock",
        }

    import httpx  # noqa: WPS433
    try:
        # 1) 법령 메타 조회 → 법령일련번호(MST) 확보
        search = httpx.get(
            f"{LAW_GO_KR_BASE}/lawSearch.do",
            params={"OC": oc, "target": "law", "type": "JSON", "query": canonical, "display": "1"},
            timeout=15.0,
        )
        search.raise_for_status()
        s_data = search.json()
        items = (s_data.get("LawSearch", {}).get("law", []) or [])
        if not items:
            # 검색 실패 → mock fallback
            return get_law_article(law_name, article_no, oc="", mock=True)
        mst = items[0].get("법령일련번호") or items[0].get("법령ID")
        if not mst:
            return get_law_article(law_name, article_no, oc="", mock=True)

        # 2) 본문 조회
        r = httpx.get(
            f"{LAW_GO_KR_BASE}/lawService.do",
            params={"OC": oc, "target": "law", "type": "JSON", "MST": str(mst)},
            timeout=15.0,
        )
        r.raise_for_status()
        law_json = r.json()
    except Exception as exc:
        return {
            "found": False,
            "law_name": canonical,
            "article_no": article_no,
            "text": "",
            "source": "law.go.kr",
            "error": str(exc),
        }

    target_no, target_para = _parse_article_no(article_no)
    if target_no is None:
        return {"found": False, "law_name": canonical, "article_no": article_no, "text": "", "source": "law.go.kr"}

    text = _extract_article_text(law_json, target_no, target_para)
    if text is None and target_para is not None:
        # 항 매칭 실패 시 조 전체 본문으로 fallback
        text = _extract_article_text(law_json, target_no, None)
    return {
        "found": text is not None,
        "law_name": canonical,
        "article_no": article_no,
        "text": text or "",
        "source": "law.go.kr",
    }
