"""KTX 시간표 추천.

mock 모드: mocks.KTX_SCHEDULES_FAKE 에서 후보 추출.
real 모드: Anthropic Computer Use 또는 letskorail.com 직접 스크레이핑.
실제 결제는 절대 자동화하지 않습니다.
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any

from .mocks import COURT_MAP, KTX_SCHEDULES_FAKE


def _to_dt(date_str: str, hhmm: str) -> datetime:
    """'2026-05-12' + '06:32' → datetime"""
    return datetime.fromisoformat(f"{date_str}T{hhmm}:00")


def recommend_ktx(
    from_station: str,
    court_name: str,
    arrival_dt: str,
    *,
    mock: bool = True,
) -> dict[str, Any]:
    info = COURT_MAP.get(court_name)
    if not info:
        return {
            "error": f"알 수 없는 법원: {court_name}. court_map.json 에 추가하세요.",
            "supported_courts": list(COURT_MAP.keys()),
        }
    nearest = info["nearest_station"]
    travel = info["avg_min_to_court"]
    buffer_min = 30

    arr_dt = datetime.fromisoformat(arrival_dt)
    rec_arrival = arr_dt - timedelta(minutes=travel + buffer_min)

    if mock:
        key = f"{from_station}_{nearest}"
        candidates = KTX_SCHEDULES_FAKE.get(key, [])
        date_str = arr_dt.strftime("%Y-%m-%d")
        # 권장 도착 시각 이전 도착 후보만, 도착 시각 내림차순
        scored = []
        for c in candidates:
            dt_arrive = _to_dt(date_str, c["arrive"])
            if dt_arrive <= rec_arrival:
                gap_min = int((rec_arrival - dt_arrive).total_seconds() // 60)
                scored.append((gap_min, c))
        scored.sort(key=lambda x: x[0])  # 가장 작은 gap 먼저 = 가장 늦게 도착(가장 효율)

        picks: list[dict[str, Any]] = []
        labels = ["추천", "대안", "여유"]
        for label, (gap, c) in zip(labels, scored[:3]):
            picks.append({
                "label": label,
                "train": c["train"],
                "depart": f"{date_str} {c['depart']}",
                "arrive": f"{date_str} {c['arrive']}",
                "class": c["class"],
                "avail": c["avail"],
                "gap_to_rec_arrival_min": gap,
                "reservation_url": (
                    f"https://www.letskorail.com/ebizprd/EbizPrdTicketDetail.do"
                    f"?txtGoStart={from_station}&txtGoEnd={nearest}&txtGoDate={date_str.replace('-', '')}"
                ),
            })

        return {
            "court_name": court_name,
            "nearest_station": nearest,
            "from_station": from_station,
            "recommended_arrival_at_station": rec_arrival.isoformat(),
            "rationale": (
                f"{court_name}까지 평균 이동 {travel}분 + 여유 {buffer_min}분을 합산한 "
                f"권장 KTX 도착 시각은 {rec_arrival.strftime('%H:%M')} 이전입니다."
            ),
            "candidates": picks,
            "note": "결제는 사용자가 직접. 결제 자동 클릭 절대 금지.",
            "source": "mock",
        }

    # real: Computer Use 호출 자리 — 실제 구현은 별도. 여기선 안내만.
    return {
        "court_name": court_name,
        "nearest_station": nearest,
        "recommended_arrival_at_station": rec_arrival.isoformat(),
        "candidates": [],
        "note": (
            "real 모드에서는 Anthropic Computer Use 또는 Playwright로 letskorail.com 을 조작합니다. "
            "본 키트에서는 모의 데이터로 흐름만 시연합니다."
        ),
        "source": "real_stub",
    }
