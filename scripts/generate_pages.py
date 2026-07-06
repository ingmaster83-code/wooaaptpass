"""
JSON → HTML 자동 생성
대상: 계약 종료일 >= 오늘인 단지 (약 47건)
"""
import os
import json
import re
import unicodedata
from datetime import date, datetime, timezone, timedelta
from pathlib import Path
from collections import defaultdict
from jinja2 import Environment, FileSystemLoader

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
DOCS_DIR = BASE_DIR / "docs"
TMPL_DIR = Path(__file__).parent / "templates"

KAKAO_KEY = os.environ.get("KAKAO_MAP_KEY", "")
API_KEY   = os.environ.get("API_KEY", "")
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).date()  # GitHub Actions 러너는 UTC라 date.today()는 KST 기준 하루 전이 됨
TODAY_STR = str(TODAY)
WEEKDAYS = ["월", "화", "수", "목", "금", "토", "일"]
REGIONS = ["서울","경기","인천","부산","대구","광주","대전","울산","세종","강원","충북","충남","전북","전남","경북","경남","제주"]

# ── 국토부 실거래가 LAWD_CD 매핑 ──────────────────────
def addr_to_lawd_cd(addr):
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


# ── 유틸 ──────────────────────────────────────────

def load_json(fname):
    p = DATA_DIR / fname
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []


def slugify(text):
    text = unicodedata.normalize("NFC", str(text))
    return re.sub(r"[^\w가-힣]", "", text)


def parse_date(s):
    if not s:
        return None
    try:
        return date.fromisoformat(str(s).replace(".", "-").replace("/", "-")[:10])
    except Exception:
        return None


def fmt_date(s):
    """'2026-06-30' → '2026. 06. 30 (월)'"""
    d = parse_date(s)
    if not d:
        return "-"
    return f"{d.year}. {d.month:02d}. {d.day:02d} ({WEEKDAYS[d.weekday()]})"


def fmt_ym(s):
    """'203009' → '2030년 9월'"""
    s = str(s or "")
    return f"{s[:4]}년 {int(s[4:6])}월" if len(s) >= 6 else "-"


def fmt_price(amount):
    """143770 → '14억 3,770만'"""
    try:
        v = int(str(amount).replace(",", ""))
    except Exception:
        return "-"
    uk, man = v // 10000, v % 10000
    if uk and man:
        return f"{uk}억 {man:,}만"
    if uk:
        return f"{uk}억"
    if man:
        return f"{man:,}만"
    return str(v)


def fmt_price_range(lo, hi):
    if not lo and not hi:
        return "-"
    if lo == hi or not lo:
        return fmt_price(hi or lo)
    return f"{fmt_price(lo)} ~ {fmt_price(hi)}"


def calc_dday(end_str, start_str=None):
    end = parse_date(end_str)
    start = parse_date(start_str)
    if not end:
        return {"days": None, "label": "마감", "cls": "gray", "live": False}
    diff = (end - TODAY).days
    if start and start <= TODAY <= end:
        return {"days": 0, "label": "청약중", "cls": "green", "live": True}
    if diff < 0:
        return {"days": diff, "label": "마감", "cls": "gray", "live": False}
    label = "D-Day" if diff == 0 else f"D-{diff}"
    cls = "green" if diff == 0 else ("red" if diff <= 3 else ("orange" if diff <= 30 else "blue"))
    return {"days": diff, "label": label, "cls": cls, "live": False}


def parse_ht(ht):
    """'059.9200A' → {area_int, type_code, display}"""
    m = re.match(r"(\d+)\.\d+\s*([A-Z]?)", str(ht).strip())
    if not m:
        return {"area_int": 0, "type_code": "", "display": str(ht)}
    ai = int(m.group(1))
    tc = m.group(2).strip()
    return {"area_int": ai, "type_code": tc, "display": f"{ai}㎡" + (f" {tc}" if tc else "")}


def group_types(types):
    """타입 리스트 → 면적별 그룹"""
    groups = defaultdict(list)
    for t in types:
        p = parse_ht(t.get("HOUSE_TY", ""))
        groups[p["area_int"]].append({**t, "_p": p})

    result = []
    for ai in sorted(groups):
        g = groups[ai]
        prices = [int(t.get("LTTOT_TOP_AMOUNT") or 0) for t in g]
        valid = [p for p in prices if p > 0]
        suply_ar = g[0].get("SUPLY_AR", "")
        try:
            suply_ar_fmt = f"{float(suply_ar):.2f}㎡"
        except Exception:
            suply_ar_fmt = "-"
        codes = [t["_p"]["type_code"] for t in g if t["_p"]["type_code"]]
        result.append({
            "area_int": ai,
            "types": g,
            "type_codes": "·".join(codes),
            "suply_ar": suply_ar_fmt,
            "min_price": min(valid) if valid else 0,
            "max_price": max(valid) if valid else 0,
            "price_range": fmt_price_range(min(valid) if valid else 0, max(valid) if valid else 0),
            "total_suply":  sum(int(t.get("SUPLY_HSHLDCO") or 0) for t in g),
            "total_spsply": sum(int(t.get("SPSPLY_HSHLDCO") or 0) for t in g),
        })
    return result


def spsply_totals(types):
    """특별공급 유형별 합계"""
    keys = ["NWWDS_HSHLDCO", "LFE_FRST_HSHLDCO", "MNYCH_HSHLDCO",
            "OLD_PARNTS_SUPORT_HSHLDCO", "INSTT_RECOMEND_HSHLDCO",
            "YGMN_HSHLDCO", "SPSPLY_HSHLDCO", "SUPLY_HSHLDCO"]
    return {k: sum(int(t.get(k) or 0) for t in types) for k in keys}


_HOUSE_TYPE_MAP = {
    "APT": "아파트", "OPST": "오피스텔", "TWHSE": "타운하우스",
    "DDDLDGE": "도시형생활주택", "HOUSE": "단독주택",
}
def house_type_name(item):
    raw = item.get("HOUSE_SECD_NM") or ""
    return _HOUSE_TYPE_MAP.get(raw, raw or "아파트")

def region_of(item):
    return item.get("SUBSCRPT_AREA_CODE_NM") or "기타"


# ── 필터링 ────────────────────────────────────────

def filter_active(apt_list):
    """계약 종료일 >= 오늘"""
    active = [x for x in apt_list if (x.get("CNTRCT_CNCLS_ENDDE") or "") >= TODAY_STR]
    for item in active:
        item["_dday"] = calc_dday(
            item.get("GNRL_RNK1_CRSPAREA_RCPTDE") or item.get("RCEPT_ENDDE"),
            item.get("RCEPT_BGNDE"),
        )
    def _sort(item):
        dd = item["_dday"]
        if dd["live"]:                            # 청약 접수 중
            return (0, dd["days"])
        if dd["days"] is not None and dd["days"] >= 0:  # 청약 예정
            return (1, dd["days"])
        return (2, -(dd["days"] or 0))            # 마감 (계약 중) — 최근 마감 순
    active.sort(key=_sort)
    return active


def filter_residual(res_list):
    """무순위: 일반 접수 종료일 기준"""
    active = [x for x in res_list
              if (x.get("SUBSCRPT_RCEPT_ENDDE") or x.get("GNRL_RCEPT_ENDDE") or "") >= TODAY_STR]
    for item in active:
        item["_dday"] = calc_dday(
            item.get("SUBSCRPT_RCEPT_ENDDE") or item.get("GNRL_RCEPT_ENDDE"),
            item.get("SUBSCRPT_RCEPT_BGNDE") or item.get("GNRL_RCEPT_BGNDE"),
        )
    active.sort(key=lambda x: (x["_dday"]["days"] if x["_dday"]["days"] is not None else 9999))
    return active


# ── Jinja2 ────────────────────────────────────────

env = Environment(loader=FileSystemLoader(str(TMPL_DIR)), autoescape=True)
env.globals.update({
    "kakao_key": KAKAO_KEY,
    "today_str": TODAY.strftime("%Y년 %m월 %d일"),
    "year": TODAY.year,
})
env.filters.update({
    "slugify":          slugify,
    "fmt_date":         fmt_date,
    "fmt_ym":           fmt_ym,
    "fmt_price":        fmt_price,
    "region_of":        region_of,
    "house_type_name":  house_type_name,
})


def render(tmpl, out_path, **ctx):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(env.get_template(tmpl).render(**ctx), encoding="utf-8")
    print(f"  {out_path.relative_to(BASE_DIR)}")


# ── 생성 함수 ──────────────────────────────────────

def gen_detail_pages(active, type_map, trade_map=None):
    if trade_map is None:
        trade_map = {}
    print("\n[1] 단지별 상세 페이지")
    for item in active:
        hid  = item.get("HOUSE_MANAGE_NO")
        name = item.get("HOUSE_NM", "")
        if not name:
            continue
        types   = type_map.get(hid, [])
        grouped = group_types(types)
        totals  = spsply_totals(types)
        all_prices = [int(t.get("LTTOT_TOP_AMOUNT") or 0) for t in types if t.get("LTTOT_TOP_AMOUNT")]
        # 1순위 해당지역 기준 D-Day (히어로·사이드바용)
        dday_rank1 = calc_dday(item.get("GNRL_RNK1_CRSPAREA_RCPTDE"))
        # 청약 접수 시작 기준 D-Day (특별공급)
        dday_spsply = calc_dday(item.get("SPSPLY_RCEPT_BGNDE"))
        # 분양가 합계 세대수 계산
        total_suply_sum = sum(int(t.get("SUPLY_HSHLDCO") or 0) for t in types)
        render("detail.html",
               DOCS_DIR / "apt" / f"{slugify(name)}.html",
               item=item,
               slug=slugify(name),
               grouped_types=grouped,
               sp_totals=totals,
               total_suply_sum=total_suply_sum,
               min_price=fmt_price(min(all_prices)) if all_prices else "-",
               max_price=fmt_price(max(all_prices)) if all_prices else "-",
               dday=dday_rank1,
               dday_spsply=dday_spsply,
               is_speclt=item.get("SPECLT_RDN_EARTH_AT") == "Y",
               is_redev=item.get("IMPRMN_BSNS_AT") == "Y",
               fmt_date=fmt_date,
               fmt_ym=fmt_ym,
               lawd_cd=addr_to_lawd_cd(item.get("HSSPLY_ADRES", "")),
               trade_rows=trade_map.get(addr_to_lawd_cd(item.get("HSSPLY_ADRES", "")), []),
        )
    print(f"  완료: {len(active)}개")


def gen_index(active):
    print("\n[2] 메인 페이지")
    top6 = active[:6]

    cal_events = {}
    for item in active:
        for field, etype in [
            ("SPSPLY_RCEPT_BGNDE",        "blue"),
            ("GNRL_RNK1_CRSPAREA_RCPTDE", "green"),
            ("PRZWNER_PRESNATN_DE",        "orange"),
        ]:
            d = parse_date(item.get(field))
            if d and d.year == TODAY.year and d.month == TODAY.month:
                cal_events.setdefault(d.day, []).append(etype)

    region_counts = defaultdict(int)
    for item in active:
        region_counts[region_of(item)] += 1

    render("index.html", DOCS_DIR / "index.html",
           top6=top6,
           total_active=len(active),
           cal_events=json.dumps(cal_events),
           region_counts=dict(region_counts),
           fmt_date=fmt_date,
           fmt_ym=fmt_ym,
           slugify=slugify,
    )


def gen_list(active, residual_active):
    print("\n[3] 목록 페이지")
    render("list.html", DOCS_DIR / "list.html",
           items=active,
           residual=residual_active,
           fmt_date=fmt_date,
           slugify=slugify,
    )


def gen_regions(active):
    print("\n[4] 지역별 페이지")
    region_map = defaultdict(list)
    for item in active:
        region_map[region_of(item)].append(item)
    for region in REGIONS + ["기타"]:
        render("region.html",
               DOCS_DIR / "지역" / f"{region}.html",
               region=region,
               items=region_map.get(region, []),
               fmt_date=fmt_date,
               slugify=slugify,
        )


def gen_residual(residual_active):
    print("\n[5] 무순위 페이지")
    render("residual.html", DOCS_DIR / "residual.html",
           items=residual_active,
           fmt_date=fmt_date,
           slugify=slugify,
    )


def gen_calendar(active):
    print("\n[5] 캘린더 페이지")
    # 달력 이벤트: date → [{name, slug, type}]
    cal_events = {}
    for item in active:
        name = item.get("HOUSE_NM", "")
        slug_v = slugify(name)
        for field, etype in [
            ("SPSPLY_RCEPT_BGNDE",        "blue"),
            ("GNRL_RNK1_CRSPAREA_RCPTDE", "green"),
            ("PRZWNER_PRESNATN_DE",        "orange"),
            ("CNTRCT_CNCLS_BGNDE",        "red"),
        ]:
            d = parse_date(item.get(field))
            if d:
                key = d.isoformat()
                cal_events.setdefault(key, []).append({"name": name, "slug": slug_v, "type": etype})
    render("calendar.html", DOCS_DIR / "calendar.html",
           items=active,
           cal_events=json.dumps(cal_events),
    )


def gen_score(winner_stat):
    print("\n[6] 당첨가점 페이지")
    # 최신 12개월치, 점수 있는 것만
    rows = [r for r in winner_stat
            if r.get("LWET_SCORE") not in [None, "-", ""] and r.get("STAT_DE")]
    # STAT_DE 내림차순
    rows.sort(key=lambda r: r.get("STAT_DE", ""), reverse=True)
    render("score.html", DOCS_DIR / "score.html", stat_rows=rows[:300])


def gen_sitemap(active, residual_active):
    print("\n[6] sitemap.xml")
    base = "https://wooaaptpass.wooahouse.com"
    today_iso = TODAY.isoformat()
    urls = [
        (f"{base}/",              "1.0"),
        (f"{base}/list.html",     "0.9"),
        (f"{base}/calendar.html", "0.8"),
        (f"{base}/residual.html", "0.9"),
        (f"{base}/score.html",    "0.8"),
    ]
    for r in REGIONS:
        urls.append((f"{base}/지역/{r}.html", "0.8"))
    for item in active:
        n = item.get("HOUSE_NM", "")
        if n:
            urls.append((f"{base}/apt/{slugify(n)}.html", "0.9"))

    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, pri in urls:
        lines.append(f'  <url><loc>{loc}</loc><lastmod>{today_iso}</lastmod>'
                     f'<changefreq>daily</changefreq><priority>{pri}</priority></url>')
    lines.append("</urlset>")
    (DOCS_DIR / "sitemap.xml").write_text("\n".join(lines), encoding="utf-8")
    print(f"  {len(urls)}개 URL 등록")


# ── 메인 ──────────────────────────────────────────

def main():
    print("=" * 55)
    print("wooaaptpass.wooahouse.com 페이지 생성 시작")
    print("=" * 55)

    apt          = load_json("apt.json")
    apt_type     = load_json("apt_type.json")
    residual     = load_json("residual.json")
    winner_stat  = load_json("winner_stat.json")

    print(f"로드: apt {len(apt)}, type {len(apt_type)}, residual {len(residual)}, stat {len(winner_stat)}")

    active   = filter_active(apt)
    res_act  = filter_residual(residual)
    print(f"활성: 아파트 {len(active)}건, 무순위 {len(res_act)}건")

    type_map = defaultdict(list)
    for t in apt_type:
        type_map[t.get("HOUSE_MANAGE_NO")].append(t)

    raw_trade = load_json("trade.json")
    trade_map = raw_trade if isinstance(raw_trade, dict) else {}

    gen_detail_pages(active, type_map, trade_map)
    gen_index(active)
    gen_list(active, res_act)
    gen_regions(active)
    gen_residual(res_act)
    gen_calendar(active)
    gen_score(winner_stat)
    gen_sitemap(active, res_act)

    print("\n" + "=" * 55)
    print("완료")
    print("=" * 55)


if __name__ == "__main__":
    main()
