"""골든셋 회귀 테스트.

각 도메인의 가상 사건을 실행한 결과에 expected/ 의 키워드가 모두 포함되는지.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

CASES = [
    ("unfair_dismissal",  "dismissal_001"),
    ("contract_review",   "contract_001"),
    ("criminal_opinion",  "criminal_001"),
    ("rehab_creditor",    "rehab_001"),
]


def _expected_keywords(name: str) -> list[str]:
    raw = Path(f"data/expected/{name}.md").read_text(encoding="utf-8").splitlines()
    return [ln.strip() for ln in raw if ln.strip() and not ln.strip().startswith("#")]


@pytest.mark.parametrize("agent_name,case_name", CASES)
def test_regression(agent_name, case_name):
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path(f"data/samples/{case_name}.json").read_text(encoding="utf-8"))
    result = run_agent(agent_name, case, cfg=cfg)
    text = result["text"]

    missing = [kw for kw in _expected_keywords(case_name) if kw not in text]
    assert not missing, f"빠진 키워드 ({agent_name}): {missing}"


def test_citation_audit_no_suspicious():
    """모의 응답에서 인용된 법령/판례는 모두 mock DB에 존재해야 한다."""
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path("data/samples/dismissal_001.json").read_text(encoding="utf-8"))
    result = run_agent("unfair_dismissal", case, cfg=cfg)
    audit = result["audit"]
    # 의심 인용 0건 — 모의 응답은 검증된 출처만 사용해야 함
    assert audit["total"] >= 1, "본문에서 인용을 추출하지 못함"
    assert audit["verified"] == audit["total"], (
        f"검증 실패 인용 발견: {audit['suspicious_refs']}"
    )
