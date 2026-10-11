#!/usr/bin/env python3
"""
update_aptq_regions.py - 우아아파트(wooaapt)의 실거래 허브(시군구·동) 목록을 scripts/aptq_regions.json 으로 내보낸다.
청약 상세/지역 페이지에서 "이 동네 아파트 실거래가" 링크를 실제로 존재하는 URL로만 만들기 위한 스냅샷이다.
사용: python scripts/update_aptq_regions.py [wooaapt 경로(기본 ../../wooaapt)]
(wooaapt 에서 python scripts/process_trades.py 를 돌려 _rawdata/trades_*.json 이 있어야 한다. 가끔(분기 1회 정도) 다시 실행하면 충분)
"""
import glob, json, sys
from collections import defaultdict
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
src = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(__file__).resolve().parent.parent.parent / "wooaapt"
out = Path(__file__).parent / "aptq_regions.json"

by_dong = defaultdict(int)
sigungu = set()
for f in glob.glob(str(src / "_rawdata" / "trades_*.json")):
    for t in json.loads(Path(f).read_text(encoding="utf-8")):
        sigungu.add(f"{t['doShort']}|{t['sigungu']}")
        by_dong[f"{t['doShort']}|{t['sigungu']}|{t['dong']}"] += 1
# 동 허브는 단지가 2곳 이상일 때만 생성된다(wooaapt MIN_COMPLEXES_DONG)
hubs = sorted(k for k, n in by_dong.items() if n >= 2)
out.write_text(json.dumps({"sigungu": sorted(sigungu), "hubs": hubs}, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
print(f"시군구 {len(sigungu)}개, 동 허브 {len(hubs)}개 → {out}")
