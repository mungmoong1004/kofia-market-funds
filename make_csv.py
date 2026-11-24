"""data/kofia.json → 대시보드용 CSV (원자료 금액 백만원→억원, 주수 주→천주, 지수는 그대로)"""
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
kp = dict(zip(d["kospi"]["date"], d["kospi"]["close"]))
kq = dict(zip(d["kosdaq"]["date"], d["kosdaq"]["close"]))
with open("docs/data/index.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["date", "kospi", "kosdaq"])
    for dt in sorted(set(kp) | set(kq)):
        w.writerow([iso(dt), kp.get(dt, ""), kq.get(dt, "")])

# 세 통계에 모두 있는 마지막 날짜 = 대시보드 기준일
common = set(d["fund"]["date"]) & set(d["credit"]["date"]) & set(d["shares"]["date"])
with open("docs/data/updated.txt", "w") as f:
    f.write(f"{d['updated']} KST · 최신 거래일 {iso(max(common))}\n")
