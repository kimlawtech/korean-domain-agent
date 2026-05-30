"""tool_use 응답을 받아 실제 함수로 디스패치."""
from __future__ import annotations

from typing import Any

from ..tools.law_lookup import get_law_article, search_law
from ..tools.precedent_search import get_precedent_text, search_precedent
from ..tools.citation_guard import verify_citation
from ..tools.ktx import recommend_ktx


def dispatch(name: str, input_: dict[str, Any], *, oc: str = "", mock: bool = True) -> dict[str, Any]:
    """tool_name → 함수 매핑."""
    try:
        if name == "search_law":
            return search_law(
                query=input_["query"],
                limit=int(input_.get("limit", 5)),
                oc=oc,
                mock=mock,
            )
        if name == "get_law_article":
            return get_law_article(
                law_name=input_["law_name"],
                article_no=input_["article_no"],
                oc=oc,
                mock=mock,
            )
        if name == "search_precedent":
            return search_precedent(
                query=input_["query"],
                court=input_.get("court"),
                year_from=input_.get("year_from"),
                year_to=input_.get("year_to"),
                limit=int(input_.get("limit", 5)),
                oc=oc,
                mock=mock,
            )
        if name == "get_precedent_text":
            return get_precedent_text(
                case_no=input_["case_no"],
                oc=oc,
                mock=mock,
            )
        if name == "verify_citation":
            return verify_citation(
                kind=input_["kind"],
                ref=input_["ref"],
                oc=oc,
                mock=mock,
            )
        if name == "recommend_ktx":
            return recommend_ktx(
                from_station=input_["from_station"],
                court_name=input_["court_name"],
                arrival_dt=input_["arrival_dt"],
                mock=mock,
            )
        return {"error": f"지원하지 않는 도구: {name}"}
    except Exception as exc:  # pylint: disable=broad-except
        return {"error": f"{type(exc).__name__}: {exc}"}
