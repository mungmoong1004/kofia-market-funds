"""data/kofia.json → 대시보드용 CSV (원자료 금액 백만원→억원, 주수 주→천주, 지수는 그대로, 협회에 아직 없는 최근 지수는 네이버 종가로 보충)"""
import json, csv
d = json.load(open("data/kofia.json"))
def iso(s): return f"{s[:4]}-{s[4:6]}-{s[6:]}"
def num(v, div, nd):
    if v is None: return ""
    x = round(v / div, nd)
    return int(x) if nd == 0 else x
specs = {
  "fund":   (["deposit","derivDeposit","rp","unpaid","forcedSale"], 100, 0, ["deposit","deriv_deposit","rp","unpaid","forced_sale"]),
  "credit": (["loanTotal","loanKospi","loanKosdaq","shortTotal","shortKospi","shortKosdaq","ipoLoan","secLoan"], 100, 0,
             ["loan_total","loan_kospi","loan_kosdaq","short_total","short_kospi","short_kosdaq","ipo_loan","sec_loan"]),
  "shares": (["loanTotal","loanKospi","loanKosdaq","shortTotal","shortKospi","shortKosdaq"], 1000, 0,
             ["loan_total","loan_kospi","loan_kosdaq","short_total","short_kospi","short_kosdaq"]),
}
failed = d.get("failed", False)
if not failed:
  for key,(src,div,nd,names) in specs.items():
    s = d[key]
    with open(f"docs/data/{key}.csv","w",newline="") as f:
        w = csv.writer(f)
        extra = ["forced_ratio"] if key=="fund" else []
        w.writerow(["date"]+names+extra)
        for i,dt in enumerate(s["date"]):
            row=[iso(dt)]+[num(s[c][i],div,nd) for c in src]
            if key=="fund": row.append(s["forcedRatio"][i])
            w.writerow(row)

# 코스피·코스닥 종가지수
if not failed:
    kp = dict(zip(d["kospi"]["date"], d["kospi"]["close"]))
    kq = dict(zip(d["kosdaq"]["date"], d["kosdaq"]["close"]))
else:  # 협회 실패: 기존 index.csv의 협회 값만 살리고 네이버 값은 새로 받는다
    kp, kq = {}, {}
    for r in csv.DictReader(open("docs/data/index.csv")):
        if r.get("src", "kofia") != "kofia": continue
        dt = r["date"].replace("-", "")
        if r["kospi"]: kp[dt] = r["kospi"]
        if r["kosdaq"]: kq[dt] = r["kosdaq"]

# 협회 지수는 다음 영업일에 올라오므로, 협회에 아직 없는 최근 종가는 네이버 금융에서 채운다.
# 장중 가격이 섞이지 않도록 오늘 자료는 장 마감(15:30) 뒤 15:40부터만 쓴다.
def naver_closes(code):
    import urllib.request, datetime
    from zoneinfo import ZoneInfo
    now = datetime.datetime.now(ZoneInfo("Asia/Seoul"))
    url = f"https://m.stock.naver.com/api/index/{code}/price?pageSize=10&page=1"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as r:
        rows = json.load(r)
    out = {}
    for row in rows:
        day = row["localTradedAt"][:10]
        if day == now.strftime("%Y-%m-%d") and (now.hour, now.minute) < (15, 40):
            continue
        out[day.replace("-", "")] = float(row["closePrice"].replace(",", ""))
    return out

naver_days = set()
for code, series in (("KOSPI", kp), ("KOSDAQ", kq)):
    last = max(series) if series else ""
    try:
        added = {dt: v for dt, v in naver_closes(code).items() if dt > last}
        series.update(added)
        naver_days |= set(added)
        print(f"{code}: 협회 마지막 {last}, 네이버로 추가 {sorted(added) or '없음'}")
    except Exception as e:
        print(f"{code}: 네이버 종가 받기 실패, 협회 자료만 사용 ({e!r})")
with open("docs/data/index.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "kospi", "kosdaq", "src"])  # src: kofia(금융투자협회) / naver(협회 미발표 당일 종가)
    for dt in sorted(set(kp) | set(kq)):
        w.writerow([iso(dt), kp.get(dt, ""), kq.get(dt, ""), "naver" if dt in naver_days else "kofia"])

# 세 통계에 모두 있는 마지막 날짜 = 대시보드 기준일
if not failed:
    common = set(d["fund"]["date"]) & set(d["credit"]["date"]) & set(d["shares"]["date"])
    line = f"{d['updated']} KST · 최신 거래일 {iso(max(common))}"
else:  # 기준일은 기존 값 유지, 협회 지연 표시
    prev = open("docs/data/updated.txt").read().strip()
    base = prev.split(" · 최신 거래일 ")[1].split(" · ")[0] if " · 최신 거래일 " in prev else "—"
    line = f"{d['updated']} KST · 최신 거래일 {base} · 협회 자료 지연(점검·차단), 지수만 네이버로 갱신"
with open("docs/data/updated.txt", "w") as f:
    f.write(line + "\n")
