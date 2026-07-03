#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import argparse, json, datetime as dt
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "content.json"

def now_cn():
    return dt.datetime.now(ZoneInfo("Asia/Shanghai")) if ZoneInfo else dt.datetime.utcnow() + dt.timedelta(hours=8)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", default="auto", choices=["auto","am","pm"])
    args = ap.parse_args()
    db = json.loads(DATA.read_text(encoding="utf-8"))
    slot = args.slot if args.slot in ("am","pm") else ("am" if now_cn().hour < 12 else "pm")
    db.setdefault("recommendation", {})["update"] = f"{now_cn():%m.%d} · {'07:30' if slot=='am' else '18:30'} 更新"
    db.setdefault("productReferences", {})["update"] = f"{now_cn():%m.%d} · Product Reference"
    DATA.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[OK] clean v6 update: {slot}")

if __name__ == "__main__":
    main()
