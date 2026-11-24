"""금융투자협회 FreeSIS 증시자금/신용공여 통계 수집 → data/kofia.json"""
import json, urllib.request, datetime, os
from zoneinfo import ZoneInfo
KST = ZoneInfo("Asia/Seoul")

URL = "https://freesis.kofia.or.kr/meta/getMetaDataList.do"
START_YEAR = 2018

def fetch(obj, s, e):
    body = {"dmSearch": {"tmpV40": "1", "tmpV41": "1", "tmpV1": "D",
                         "tmpV45": s, "tmpV46": e, "OBJ_NM": obj}}
    req = urllib.request.Request(URL, json.dumps(body).encode(),
                                 {"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["ds1"] or []

def collect(obj):
    today = datetime.datetime.now(KST).date()
    rows = {}
    for y in range(START_YEAR, today.year + 1):
        for r in fetch(obj, f"{y}0101", f"{y}1231"):
            rows[r["TMPV1"]] = r
    return [rows[k] for k in sorted(rows)]

SPECS = {
    "fund":   ("STATSCU0100000060BO", ["deposit", "derivDeposit", "rp", "unpaid", "forcedSale", "forcedRatio"]),
    "credit": ("STATSCU0100000070BO", ["loanTotal", "loanKospi", "loanKosdaq", "shortTotal", "shortKospi", "shortKosdaq", "ipoLoan", "secLoan"]),
    "shares": ("STATSCU0100000080BO", ["loanTotal", "loanKospi", "loanKosdaq", "shortTotal", "shortKospi", "shortKosdaq"]),
}
out = {"updated": datetime.datetime.now(KST).strftime("%Y-%m-%d %H:%M")}
for key, (obj, cols) in SPECS.items():
    data = collect(obj)
    out[key] = {"date": [r["TMPV1"] for r in data]}
    for i, c in enumerate(cols):
        out[key][c] = [r.get(f"TMPV{i+2}") for r in data]
    print(key, len(data), data[0]["TMPV1"], data[-1]["TMPV1"])
os.makedirs("data", exist_ok=True)
with open("data/kofia.json", "w") as f:
    json.dump(out, f, ensure_ascii=False, separators=(",", ":"))
