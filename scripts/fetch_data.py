"""
청약홈 API 데이터 수집 스크립트
매일 새벽 GitHub Actions에서 실행

확인된 엔드포인트 (2026-06-24 기준):
  - getAPTLttotPblancDetail    : 아파트 분양정보 (총 ~2800건)
  - getAPTLttotPblancMdl       : 타입별 분양가/세대수 (~14000건)
  - getRemndrLttotPblancDetail : 무순위/잔여세대 (~1600건)
  - getAPTLttotPblancCmpet     : 경쟁률 (~53000건)
  - getAPTSpsplyReqstStus      : 특별공급 신청현황 (~12000건)
  - getAptLttotPblancScore     : 당첨가점 (~28000건)
  - getAPTPrzwnerAreaStat      : 연령별/지역별 당첨자 통계
  - getAPTApsPrzwnerStat       : 지역별 당첨가점 통계

환경변수:
  - API_KEY : 공공데이터포털 서비스키
"""
import os
import json
import time
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

API_KEY   = os.environ.get("API_KEY", "")
BASE      = "https://api.odcloud.kr/api"
DATA_DIR  = Path(__file__).parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

DELAY     = 0.5   # 요청 간 딜레이 (초)
PER_PAGE  = 100   # 페이지당 건수


# ── 공통 ──────────────────────────────────────────

def fetch_all(endpoint: str, extra_params: dict | None = None) -> list:
    """전체 페이지 수집 — 실패 시 빈 리스트 반환"""
    url = f"{BASE}/{endpoint}"
    params = {"page": 1, "perPage": PER_PAGE, "serviceKey": API_KEY}
    if extra_params:
        params.update(extra_params)

    all_data: list = []
    while True:
        try:
            r = requests.get(url, params=params, timeout=15)
            r.raise_for_status()
            d = r.json()
        except Exception as e:
            print(f"  [오류] p{params['page']}: {e}")
            break

        items = d.get("data", [])
        all_data.extend(items)
        total = d.get("totalCount", 0)
        print(f"  p{params['page']}: {len(items)}건 수집 (누적 {len(all_data)}/{total})")

        if len(all_data) >= total or not items:
            break
        params["page"] += 1
        time.sleep(DELAY)

    return all_data


def save(filename: str, data: list):
    """기존 파일 보존 — 데이터 없으면 덮어쓰지 않음"""
    path = DATA_DIR / filename
    if not data:
        print(f"  [경고] 데이터 없음 — {filename} 유지")
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  OK {filename}: {len(data)}건 저장")


def save_dict(filename: str, data: dict):
    path = DATA_DIR / filename
    if not data:
        print(f"  [경고] 데이터 없음 — {filename} 유지")
        return
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"  OK {filename}: {len(data)}개 지역 저장")


# ── 수집 함수 ──────────────────────────────────────

def fetch_apt():
    print("\n[1] 아파트 분양정보")
    data = fetch_all("ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancDetail")
    save("apt.json", data)
    return data


def fetch_apt_type():
    print("\n[2] 타입별 분양가/세대수")
    data = fetch_all("ApplyhomeInfoDetailSvc/v1/getAPTLttotPblancMdl")
    save("apt_type.json", data)
    return data


def fetch_residual():
    print("\n[3] 무순위/잔여세대")
    data = fetch_all("ApplyhomeInfoDetailSvc/v1/getRemndrLttotPblancDetail")
    save("residual.json", data)
    return data


def fetch_competition():
    print("\n[4] 경쟁률")
    data = fetch_all("ApplyhomeInfoCmpetRtSvc/v1/getAPTLttotPblancCmpet")
    save("competition.json", data)
    return data


def fetch_spsply():
    print("\n[5] 특별공급 신청현황")
    data = fetch_all("ApplyhomeInfoCmpetRtSvc/v1/getAPTSpsplyReqstStus")
    save("spsply.json", data)
    return data


def fetch_score():
    print("\n[6] 당첨가점")
    data = fetch_all("ApplyhomeInfoCmpetRtSvc/v1/getAptLttotPblancScore")
    save("score.json", data)
    return data


def fetch_winner_stat():
    print("\n[7] 지역별 당첨가점 통계 (score.html용)")
    data = fetch_all("ApplyhomeStatSvc/v1/getAPTApsPrzwnerStat")
    save("winner_stat.json", data)
    return data


# ── 국토부 실거래가 ────────────────────────────────

def _addr_to_lawd_cd(addr):
    a = addr
    if '서울' in a:
        for g,c in [('강남구','11680'),('서초구','11650'),('송파구','11710'),('강동구','11740'),
                    ('마포구','11440'),('영등포구','11560'),('동작구','11590'),('관악구','11620'),
                    ('강서구','11500'),('양천구','11470'),('구로구','11530'),('금천구','11545'),
                    ('은평구','11380'),('서대문구','11410'),('종로구','11110'),('중구','11140'),
                    ('용산구','11170'),('성동구','11200'),('광진구','11215'),('동대문구','11230'),
                    ('중랑구','11260'),('성북구','11290'),('강북구','11305'),('도봉구','11320'),('노원구','11350')]:
            if g in a: return c
    if '부산' in a:
        for g,c in [('해운대구','26350'),('수영구','26500'),('사하구','26380'),('금정구','26410'),
                    ('강서구','26440'),('연제구','26470'),('동래구','26260'),('부산진구','26230'),
                    ('남구','26290'),('북구','26320'),('사상구','26530'),('기장군','26710'),
                    ('중구','26110'),('서구','26140'),('동구','26170'),('영도구','26200')]:
            if g in a: return c
    if '대구' in a:
        for g,c in [('수성구','27260'),('달서구','27290'),('달성군','27710'),('북구','27230'),
                    ('동구','27140'),('서구','27170'),('남구','27200'),('중구','27110')]:
            if g in a: return c
    if '인천' in a:
        for g,c in [('계양구','28245'),('남동구','28200'),('부평구','28237'),('연수구','28185'),
                    ('서구','28260'),('미추홀구','28177'),('강화군','28710'),('옹진군','28720'),
                    ('중구','28110'),('동구','28140')]:
            if g in a: return c
    if '광주' in a and '경기' not in a:
        for g,c in [('광산구','29200'),('서구','29140'),('북구','29170'),('남구','29155'),('동구','29110')]:
            if g in a: return c
    if '대전' in a:
        for g,c in [('유성구','30200'),('서구','30170'),('대덕구','30230'),('동구','30110'),('중구','30140')]:
            if g in a: return c
    if '울산' in a:
        for g,c in [('울주군','31710'),('남구','31140'),('북구','31200'),('동구','31170'),('중구','31110')]:
            if g in a: return c
    if '세종' in a: return '36110'
    if '경기' in a or '김포' in a:
        for g,c in [('장안구','41111'),('권선구','41113'),('팔달구','41115'),('영통구','41117'),
                    ('수정구','41131'),('중원구','41133'),('분당구','41135'),('만안구','41171'),
                    ('동안구','41173'),('상록구','41271'),('단원구','41273'),('덕양구','41281'),
                    ('일산동구','41285'),('일산서구','41287'),('처인구','41461'),('기흥구','41463'),('수지구','41465')]:
            if g in a: return c
        for s,c in [('수원시','41110'),('성남시','41130'),('의정부시','41150'),('안양시','41170'),
                    ('부천시','41190'),('광명시','41210'),('평택시','41220'),('동두천시','41250'),
                    ('안산시','41270'),('고양시','41280'),('과천시','41290'),('구리시','41310'),
                    ('남양주시','41360'),('오산시','41370'),('시흥시','41390'),('군포시','41410'),
                    ('의왕시','41430'),('하남시','41450'),('용인시','41460'),('파주시','41480'),
                    ('이천시','41500'),('안성시','41550'),('김포시','41570'),('화성시','41590'),
                    ('광주시','41610'),('양주시','41630'),('포천시','41650'),('여주시','41670'),
                    ('연천군','41800'),('가평군','41820'),('양평군','41830')]:
            if s in a: return c
    if '강원' in a:
        for s,c in [('춘천시','51110'),('원주시','51130'),('강릉시','51150'),('동해시','51170'),
                    ('태백시','51190'),('속초시','51210'),('삼척시','51230')]:
            if s in a: return c
    if '충북' in a or '충청북도' in a:
        for s,c in [('청주시','43110'),('충주시','43130'),('제천시','43150')]:
            if s in a: return c
    if '충남' in a or '충청남도' in a:
        for g,c in [('동남구','44131'),('서북구','44133')]:
            if g in a: return c
        for s,c in [('천안시','44130'),('공주시','44150'),('보령시','44180'),('아산시','44200'),
                    ('서산시','44210'),('논산시','44230'),('계룡시','44250'),('당진시','44270')]:
            if s in a: return c
    if '전북' in a or '전라북도' in a:
        for g,c in [('완산구','52111'),('덕진구','52113')]:
            if g in a: return c
        for s,c in [('전주시','52110'),('군산시','52130'),('익산시','52140'),('정읍시','52180'),
                    ('남원시','52190'),('김제시','52210')]:
            if s in a: return c
    if '전남' in a or '전라남도' in a:
        for s,c in [('목포시','46110'),('여수시','46130'),('순천시','46150'),('나주시','46170'),('광양시','46230')]:
            if s in a: return c
    if '경북' in a or '경상북도' in a:
        for s,c in [('포항시','47110'),('경주시','47130'),('김천시','47150'),('안동시','47170'),
                    ('구미시','47190'),('영주시','47210'),('영천시','47230'),('경산시','47290')]:
            if s in a: return c
    if '경남' in a or '경상남도' in a:
        for g,c in [('의창구','48121'),('성산구','48123'),('마산합포구','48125'),('마산회원구','48127'),('진해구','48129')]:
            if g in a: return c
        for s,c in [('창원시','48110'),('진주시','48170'),('통영시','48220'),('사천시','48240'),
                    ('김해시','48250'),('밀양시','48270'),('거제시','48310'),('양산시','48330'),('함안군','48720')]:
            if s in a: return c
    if '제주' in a:
        return '50130' if '서귀포' in a else '50110'
    return ''


def fetch_trade(apt_data: list) -> dict:
    """활성 단지 주소 기반으로 국토부 실거래가 수집 → {lawd_cd: [rows]}"""
    from datetime import date, datetime, timezone, timedelta
    import urllib.request, urllib.parse

    KST = timezone(timedelta(hours=9))
    today = datetime.now(KST).date()  # GitHub Actions 러너는 UTC라 date.today()는 KST 기준 하루 전이 됨
    months = []
    for i in range(3):
        y, m = today.year, today.month - i
        if m <= 0:
            y -= 1; m += 12
        months.append(f"{y}{m:02d}")

    TODAY_STR = str(today)
    active = [a for a in apt_data if (a.get('CNTRCT_CNCLS_ENDDE') or '') >= TODAY_STR]
    lawd_set = {_addr_to_lawd_cd(a.get('HSSPLY_ADRES', '')) for a in active} - {''}

    result: dict = {}
    base = ('https://apis.data.go.kr/1613000/RTMSDataSvcAptTrade/getRTMSDataSvcAptTrade')
    key_enc = urllib.parse.quote(API_KEY, safe='')

    for lawd_cd in sorted(lawd_set):
        rows = []
        for ym in months:
            url = (f"{base}?LAWD_CD={lawd_cd}&DEAL_YMD={ym}"
                   f"&numOfRows=100&pageNo=1&_type=json&serviceKey={key_enc}")
            try:
                with urllib.request.urlopen(url, timeout=8) as r:
                    data = json.loads(r.read())
                items = (data.get('response', {}).get('body', {})
                         .get('items', {}).get('item') or [])
                if not isinstance(items, list):
                    items = [items]
                rows.extend(items)
            except Exception as e:
                print(f"  [무시] {lawd_cd}/{ym}: {e}")
            time.sleep(0.3)
        result[lawd_cd] = rows
        print(f"  {lawd_cd}: {len(rows)}건")

    save_dict("trade.json", result)
    return result


# ── 메인 ──────────────────────────────────────────

def main():
    if not API_KEY:
        raise SystemExit("[오류] API_KEY 환경변수가 없습니다.")

    print("=" * 55)
    print("wooaaptpass.wooahouse.com 청약 데이터 수집 시작")
    print("=" * 55)

    apt_data = fetch_apt()
    fetch_apt_type()
    fetch_residual()
    fetch_competition()
    fetch_spsply()
    fetch_score()
    fetch_winner_stat()

    print("\n[8] 국토부 실거래가 (단지별 주변 데이터)")
    fetch_trade(apt_data or [])

    print("\n" + "=" * 55)
    print("데이터 수집 완료")
    print("=" * 55)


if __name__ == "__main__":
    main()
