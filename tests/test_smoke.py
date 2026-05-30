"""스모크 테스트 — import + mock 모드 1회 실행."""
from __future__ import annotations

import json
from pathlib import Path

import pytest


def test_imports():
    from src import config
    from src.tools import schema, mocks, law_lookup, precedent_search, citation_guard, ktx
    from src.agent import safety, tool_router, orchestrator
    from src.render import docx_render
    assert hasattr(orchestrator, "run_agent")
    assert hasattr(safety, "safe_postprocess")
    assert len(schema.TOOLS) >= 6


def test_mock_dismissal_runs():
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path("data/samples/dismissal_001.json").read_text(encoding="utf-8"))
    result = run_agent("unfair_dismissal", case, cfg=cfg)

    assert result["mode"] == "mock"
    assert "원직복직" in result["text"]
    assert "근로기준법 제26조" in result["text"]
    assert "본 출력은 AI 보조" in result["text"]  # 면책 자동 삽입
    assert len(result["tools_used"]) > 0


def test_mock_contract_runs():
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path("data/samples/contract_001.json").read_text(encoding="utf-8"))
    result = run_agent("contract_review", case, cfg=cfg)
    assert "HIGH" in result["text"]
    assert "민법 제390조" in result["text"]


@pytest.mark.parametrize("agent_name,sample", [
    ("unfair_dismissal",  "dismissal_001.json"),
    ("contract_review",   "contract_001.json"),
    ("criminal_opinion",  "criminal_001.json"),
    ("rehab_creditor",    "rehab_001.json"),
])
def test_all_agents_smoke(agent_name, sample):
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path(f"data/samples/{sample}").read_text(encoding="utf-8"))
    result = run_agent(agent_name, case, cfg=cfg)
    assert result["text"]
    assert "본 출력은 AI 보조" in result["text"]


def test_general_mode_runs():
    """범용 모드 — agent_name 미지정 시 general fallback."""
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path("data/samples/general_001.json").read_text(encoding="utf-8"))
    result = run_agent(None, case, cfg=cfg)

    assert result["mode"] == "mock"
    assert result["text"]
    assert "본 출력은 AI 보조" in result["text"]
    assert "임대차 보증금 반환 사실관계 정리" in result["text"]


def test_general_mode_explicit():
    """agent_name='general' 명시도 동일 동작."""
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = json.loads(Path("data/samples/general_001.json").read_text(encoding="utf-8"))
    result = run_agent("general", case, cfg=cfg)
    assert "본 출력은 AI 보조" in result["text"]


def test_general_mode_routes_by_keys():
    """case 키에 따라 모드가 라우팅된다 — '쟁점' 키 → 자문."""
    from src.config import load_config
    from src.agent.orchestrator import run_agent

    cfg = load_config(mode_override="mock")
    case = {
        "사건명": "임대차 자문",
        "의뢰인": "[성명]",
        "쟁점": "보증금 공제 가능 범위",
    }
    result = run_agent(None, case, cfg=cfg)
    assert "자문" in result["text"]
