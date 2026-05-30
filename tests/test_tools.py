"""tools/ 단위 테스트 — 캐시, 법령 파서, temperature 매핑."""
from __future__ import annotations


def test_verify_citation_cache_hit():
    from src.tools.citation_guard import clear_verify_cache, verify_citation

    clear_verify_cache()
    first = verify_citation("law", "근로기준법 제26조", mock=True)
    assert first.get("cache") != "hit"
    assert first["verified"] is True

    second = verify_citation("law", "근로기준법 제26조", mock=True)
    assert second.get("cache") == "hit"
    assert second["verified"] == first["verified"]


def test_verify_citation_cache_separates_keys():
    from src.tools.citation_guard import clear_verify_cache, verify_citation

    clear_verify_cache()
    verify_citation("law", "근로기준법 제26조", mock=True)
    other = verify_citation("law", "근로기준법 제27조", mock=True)
    # 다른 ref → cache miss
    assert other.get("cache") != "hit"


def test_parse_article_no_simple():
    from src.tools.law_lookup import _parse_article_no

    assert _parse_article_no("제26조") == (26, None)
    assert _parse_article_no("제23조 제1항") == (23, 1)
    assert _parse_article_no("쓰레기") == (None, None)


def test_extract_article_text_jomun_unit():
    """법제처 JSON 가상 응답에서 조·항 본문 추출."""
    from src.tools.law_lookup import _extract_article_text

    law_json = {
        "법령": {
            "조문": {
                "조문단위": [
                    {
                        "조문번호": "26",
                        "조문내용": "사용자는 30일 전에 예고하여야 한다.",
                        "항": [
                            {"항번호": "1", "항내용": "예고 의무 적용 범위는 ..."},
                        ],
                    },
                ],
            },
        },
    }
    assert "30일 전에 예고" in _extract_article_text(law_json, 26, None)
    assert "예고 의무 적용 범위" in _extract_article_text(law_json, 26, 1)
    assert _extract_article_text(law_json, 99, None) is None


def test_extract_article_text_dict_unit():
    """조문단위가 단일 dict 인 응답도 처리."""
    from src.tools.law_lookup import _extract_article_text

    law_json = {
        "법령": {
            "조문": {
                "조문단위": {
                    "조문번호": "390",
                    "조문내용": "채무불이행 본문",
                },
            },
        },
    }
    assert _extract_article_text(law_json, 390, None) == "채무불이행 본문"


def test_temperature_mode_mapping():
    from src.agent.orchestrator import _TEMPERATURE_BY_MODE

    assert _TEMPERATURE_BY_MODE["요약"] == 0.0
    assert _TEMPERATURE_BY_MODE["리서치"] == 0.0
    assert _TEMPERATURE_BY_MODE["자문"] >= _TEMPERATURE_BY_MODE["작성"]


def test_attach_tools_cache_control():
    from src.agent.orchestrator import _attach_tools_cache_control

    tools = [{"name": "a"}, {"name": "b"}]
    out = _attach_tools_cache_control(tools)
    # 원본 불변
    assert "cache_control" not in tools[-1]
    # 마지막 항목에만 마커
    assert out[-1]["cache_control"] == {"type": "ephemeral"}
    assert "cache_control" not in out[0]


def test_attach_tools_cache_control_empty():
    from src.agent.orchestrator import _attach_tools_cache_control

    assert _attach_tools_cache_control([]) == []
