#!/bin/zsh
# 금융투자협회 데이터를 다시 받아 CSV를 만들고, 마지막으로 업로드한 날짜와 비교한다.
set -e
cd "$(dirname "$0")"
python3 fetch_kofia.py
python3 make_csv.py
LATEST=$(tail -1 docs/data/fund.csv | cut -d, -f1)
LAST=$(cat data/last_uploaded.txt 2>/dev/null || echo none)
echo "LATEST=$LATEST"
echo "LAST_UPLOADED=$LAST"
if [[ "$LATEST" == "$LAST" ]]; then echo "NEW_DATA=no"; else echo "NEW_DATA=yes"; fi
