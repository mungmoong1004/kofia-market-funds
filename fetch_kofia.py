"""금융투자협회 FreeSIS 증시자금/신용공여 통계 수집 → data/kofia.json"""
import json, urllib.request, datetime, os, time
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")

URL = "https://freesis.kofia.or.kr/meta/getMetaDataList.do"
START_YEAR = 2018

def fetch(obj, s, e_, unit="1"):
    body = {"dmSearch": {"tmpV40": unit, "tmpV41": "1", "tmpV1": "D",
                         "tmpV45": s, "tmpV46": e_, "OBJ_NM": obj}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    last = None
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as r:
                raw = r.read().decode("utf-8", "replace")
            return json.loads(raw)["ds1"] or []
        except Exception as e:  # 일시 오류는 재시도, 마지막엔 응답 앞부분을 보여 준다
            last = e
            print(f"[{obj} {s}~{e_}] 시도 {attempt+1} 실패: {e!r}; 응답 앞부분: {locals().get('raw', '')[:300]!r}")
            time.sleep(5)
    raise last

def collect(obj, unit):
    today = datetime.datetime.now(KST).date()
    rows = {}
    for y in range(START_YEAR, today.year + 1):
        for r in fetch(obj, f"{y}0101", f"{y}1231", unit):
            rows[r["TMPV1"]] = r
    return [rows[k] for k in sorted(rows)]

SPECS = {
    "fund":   ("STATSCU0100000060BO", "1000000", ["deposit", "derivDeposit", "rp", "unpaid", "forcedSale", "forcedRatio"]),
    "credit": ("STATSCU0100000070BO", "1000000", ["loanTotal", "loanKospi", "loanKosdaq", "shortTotal", "shortKospi", "shortKosdaq", "ipoLoan", "secLoan"]),
    "shares": ("STATSCU0100000080BO", "1", ["loanTotal", "loanKospi", "loanKosdaq", "shortTotal", "shortKospi", "shortKosdaq"]),
    # 주식 > 증시동향 > 유가증권시장 / 코스닥시장 (TMPV2 = 종가지수, 단위 설정과 무관)
    "kospi":  ("STATSCU0100000020BO", "1000000", ["close"]),
    "kosdaq": ("STATSCU0100000030BO", "1000000", ["close"]),
}
out = {"updated": datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M")}
# 금액은 백만원, 주수는 주 단위로 받는다 (원 단위로 받으면 큰 값이 #으로 가려지는 경우가 있음)
# 협회가 점검·방화벽 차단 등으로 응답하지 않으면 멈추지 않고 실패만 기록한다.
# (make_csv.py가 기존 CSV를 그대로 두고 네이버 종가만 보충한다)
try:
    for key, (obj, unit, cols) in SPECS.items():
        data = collect(obj, unit)
        out[key] = {"date": [r["TMPV1"] for r in data]}
        for i, c in enumerate(cols):
            out[key][c] = [r.get(f"TMPV{i+2}") for r in data]
        print(key, len(data), data[0]["TMPV1"], data[-1]["TMPV1"])
except Exception as e:
    print(f"금융투자협회 데이터 받기 실패 → 기존 자료 유지: {e!r}")
    out = {"updated": out["updated"], "failed": True}
os.makedirs("data", exist_ok=True)
with open("data/kofia.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
