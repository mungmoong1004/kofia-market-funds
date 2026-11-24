# 증시자금·신용공여 동향

금융투자협회 종합통계포털(FreeSIS)의 일간 통계로 만든 대시보드입니다.

- 주식 > 증시자금 > 증시자금추이
- 주식 > 신용공여현황 > 신용공여 잔고 추이, 신용거래 체결주수 추이

`docs/`가 GitHub Pages로 배포되고, `.github/workflows/update-data.yml`이 평일 08시·18시(KST)에 데이터를 갱신합니다.

로컬에서 갱신: `python3 fetch_kofia.py && python3 make_csv.py`
