"""환경변수와 실행 모드 한 곳에서 관리."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _load_dotenv(path: Path) -> None:
    """경량 .env 로더 — 외부 의존성 없이."""
    if not path.exists():
        return
    for raw in path.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        k, _, v = line.partition("=")
        os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


_load_dotenv(Path(__file__).resolve().parent.parent / ".env")


@dataclass(frozen=True)
class Config:
    anthropic_api_key: str
    anthropic_model: str
    law_go_kr_oc: str
    mode: str  # "mock" | "real"

    @property
    def is_mock(self) -> bool:
        return self.mode == "mock"


def load_config(mode_override: str | None = None) -> Config:
    mode = mode_override or os.environ.get("AGENT_MODE", "mock")
    return Config(
        anthropic_api_key=os.environ.get("ANTHROPIC_API_KEY", ""),
        anthropic_model=os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-6"),
        law_go_kr_oc=os.environ.get("LAW_GO_KR_OC", ""),
        mode=mode,
    )
