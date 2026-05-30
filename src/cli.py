"""명령행 진입점.

사용:
    # 도메인 미지정 → 범용(general) 모드
    python -m src.cli run --input data/samples/dismissal_001.json \\
        --out out/dismissal_001.docx --mode mock

    # 도메인 특화
    python -m src.cli run --agent unfair_dismissal \\
        --input data/samples/dismissal_001.json \\
        --out out/dismissal_001.docx --mode mock

    python -m src.cli list-agents
    python -m src.cli verify-citation --kind law --ref "근로기준법 제26조"
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .agent.orchestrator import run_agent
from .config import load_config
from .render.docx_render import save
from .tools.citation_guard import verify_citation


AGENTS = ["general", "unfair_dismissal", "contract_review", "criminal_opinion", "rehab_creditor"]


def cmd_run(args: argparse.Namespace) -> int:
    cfg = load_config(mode_override=args.mode)
    case = json.loads(Path(args.input).read_text(encoding="utf-8"))
    agent_name = args.agent or "general"
    print(f"[mode={cfg.mode}] agent={agent_name} input={args.input}")

    result = run_agent(agent_name, case, cfg=cfg)
    out_path = save(result["text"], args.out)
    print(f"\n사용 도구: {', '.join(result['tools_used']) or '(없음)'}")
    audit = result.get("audit") or {}
    if audit:
        print(
            f"인용 검증: 총 {audit.get('total', 0)} 건, "
            f"검증 통과 {audit.get('verified', 0)} 건, "
            f"의심 {len(audit.get('suspicious_refs', []))} 건"
        )
        if audit.get("suspicious_refs"):
            print("  의심 인용: " + ", ".join(audit["suspicious_refs"]))
    print(f"\n결과 파일: {out_path}")
    return 0


def cmd_list_agents(_: argparse.Namespace) -> int:
    for name in AGENTS:
        print(name)
    return 0


def cmd_verify_citation(args: argparse.Namespace) -> int:
    cfg = load_config()
    result = verify_citation(args.kind, args.ref, oc=cfg.law_go_kr_oc, mock=cfg.is_mock)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result.get("verified") else 2


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="legal-agent", description="Korean Legal Agent CLI")
    sub = p.add_subparsers(dest="command", required=True)

    p_run = sub.add_parser("run", help="에이전트 1회 실행")
    p_run.add_argument("--agent", required=False, choices=AGENTS, default="general")
    p_run.add_argument("--input", required=True, help="입력 JSON 경로")
    p_run.add_argument("--out", required=True, help="출력 Word 경로")
    p_run.add_argument("--mode", choices=["mock", "real"], default=None)
    p_run.set_defaults(func=cmd_run)

    p_list = sub.add_parser("list-agents", help="사용 가능한 에이전트 목록")
    p_list.set_defaults(func=cmd_list_agents)

    p_vc = sub.add_parser("verify-citation", help="인용 검증")
    p_vc.add_argument("--kind", required=True, choices=["law", "precedent"])
    p_vc.add_argument("--ref", required=True)
    p_vc.set_defaults(func=cmd_verify_citation)

    return p


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    return int(args.func(args) or 0)


if __name__ == "__main__":
    sys.exit(main())
