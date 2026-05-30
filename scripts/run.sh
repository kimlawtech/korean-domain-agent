#!/usr/bin/env bash
# 빠른 실행 헬퍼 — 4개 도메인을 한 번에 mock 실행하고 결과 docx 4개 출력.
set -e

cd "$(dirname "$0")/.."

mkdir -p out

for pair in \
  "unfair_dismissal:dismissal_001" \
  "contract_review:contract_001" \
  "criminal_opinion:criminal_001" \
  "rehab_creditor:rehab_001"
do
  agent="${pair%%:*}"
  case_name="${pair##*:}"
  echo ""
  echo "==> ${agent} / ${case_name}"
  python -m src.cli run \
    --agent "${agent}" \
    --input "data/samples/${case_name}.json" \
    --out "out/${case_name}.docx" \
    --mode mock
done
echo ""
echo "완료. out/ 폴더 확인."
