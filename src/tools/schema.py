"""Anthropic tool_use 스키마 정의.

각 tool은 (이름, 설명, 입력 스키마)로 구성됩니다.
실제 호출은 tool_router.dispatch() 에서 함수로 매핑됩니다.
"""
from __future__ import annotations

TOOLS = [
    {
        "name": "search_law",
        "description": (
            "한국 법령을 키워드 또는 법령명으로 검색합니다. "
            "약칭(예: '화관법')도 정식 명칭으로 자동 매핑됩니다. "
            "결과는 법령명·소관 부처·시행일·법령 ID 목록입니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "법령명 또는 키워드 (예: '근로기준법', '해고예고')"
                },
                "limit": {
                    "type": "integer",
                    "description": "최대 결과 수",
                    "default": 5
                }
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_law_article",
        "description": (
            "특정 법령의 조문 본문을 조회합니다. "
            "법령명과 조항 번호(예: '근로기준법' + '제26조')로 호출합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "law_name": {"type": "string"},
                "article_no": {
                    "type": "string",
                    "description": "예: '제23조', '제26조 제1항'"
                }
            },
            "required": ["law_name", "article_no"]
        }
    },
    {
        "name": "search_precedent",
        "description": (
            "판례 목록을 검색합니다. 키워드·법원·기간으로 필터링."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {"type": "string"},
                "court": {
                    "type": "string",
                    "description": "예: '대법원', '서울고등법원'. 생략 시 전체."
                },
                "year_from": {"type": "integer"},
                "year_to": {"type": "integer"},
                "limit": {"type": "integer", "default": 5}
            },
            "required": ["query"]
        }
    },
    {
        "name": "get_precedent_text",
        "description": "판례 본문을 사건번호로 조회합니다.",
        "input_schema": {
            "type": "object",
            "properties": {
                "case_no": {
                    "type": "string",
                    "description": "예: '2019다270163'"
                }
            },
            "required": ["case_no"]
        }
    },
    {
        "name": "verify_citation",
        "description": (
            "인용한 법령 조문 또는 판례 사건번호가 실제로 존재하는지 검증합니다. "
            "결과 본문에 인용하기 전, 환각 방지를 위해 반드시 호출하십시오. "
            "존재하지 않으면 'verified=false' 반환."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "kind": {
                    "type": "string",
                    "enum": ["law", "precedent"],
                    "description": "law=법령조문, precedent=판례"
                },
                "ref": {
                    "type": "string",
                    "description": (
                        "law: '근로기준법 제26조' / "
                        "precedent: '2019다270163' 또는 '대법원 2019. 5. 10. 선고 2019다270163'"
                    )
                }
            },
            "required": ["kind", "ref"]
        }
    },
    {
        "name": "recommend_ktx",
        "description": (
            "법원·관청 도착 시점을 받아 KTX 추천 시간표 3건을 반환합니다. "
            "실제 좌석 예매는 절대 자동화하지 않으며, 결과의 'reservation_url' 을 "
            "사용자에게 안내만 합니다."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "from_station": {"type": "string", "description": "예: '서울', '용산'"},
                "court_name": {
                    "type": "string",
                    "description": "예: '부산지방법원', '대전지방법원'"
                },
                "arrival_dt": {
                    "type": "string",
                    "description": "ISO 8601 (예: '2026-05-12T10:00')"
                }
            },
            "required": ["from_station", "court_name", "arrival_dt"]
        }
    }
]
