#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Aesthetic OS daily updater.
# It updates data/content.json, generates one Dr.Coffee product scene image,
# and keeps daily recommendations/inspirations available for the website.

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import random
import re
import sys
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None


ROOT = Path(__file__).resolve().parents[1]
DATA_PATH = ROOT / "data" / "content.json"
ASSET_CASES = ROOT / "assets" / "cases"
ASSET_RECS = ROOT / "assets" / "recs"
ASSET_INSP = ROOT / "assets" / "inspiration"
ASSET_CURATED = ROOT / "assets" / "curated"

TEXT_MODEL = os.getenv("OPENAI_TEXT_MODEL") or "gpt-4.1-mini"
IMAGE_MODEL = os.getenv("OPENAI_IMAGE_MODEL") or "gpt-image-2"


THEMES = [
    {
        "key": "metal_clean",
        "theme_cn_am": "清晨金属冷白",
        "theme_en_am": "Clean Metal Morning",
        "theme_cn_pm": "金属感办公空间",
        "theme_en_pm": "Minimal Metal Office",
        "principle": "干净不是空，而是每个元素都有理由。",
        "prompt_style": "DJI-inspired, clean metal, white gray, minimal, precise product photography",
    },
    {
        "key": "shadow_blinds",
        "theme_cn_am": "百叶光影与留白",
        "theme_en_am": "Blinds Light and Space",
        "theme_cn_pm": "冷灰百叶光影",
        "theme_en_pm": "Cool Gray Blinds Light",
        "principle": "光影负责情绪，留白负责高级感。",
        "prompt_style": "soft blinds shadow, cool gray office, restrained composition, clean commercial photography",
    },
    {
        "key": "quiet_office",
        "theme_cn_am": "安静办公室",
        "theme_en_am": "Quiet Office",
        "theme_cn_pm": "克制的商务空间",
        "theme_en_pm": "Restrained Business Space",
        "principle": "让产品自然存在，而不是强行展示。",
        "prompt_style": "quiet modern office, clean desk, subtle metal reflections, high-end B2B product scene",
    },
    {
        "key": "glass_reflection",
        "theme_cn_am": "玻璃反光与轮廓",
        "theme_en_am": "Glass Reflection",
        "theme_cn_pm": "玻璃、金属与暗部",
        "theme_en_pm": "Glass Metal Shadow",
        "principle": "反光不是问题，失控的反光才是问题。",
        "prompt_style": "glass reflections, metal texture, dark gray details, minimal product photography",
    },
    {
        "key": "silver_space",
        "theme_cn_am": "银白空间",
        "theme_en_am": "Silver White Space",
        "theme_cn_pm": "银白极简场景",
        "theme_en_pm": "Silver Minimal Scene",
        "principle": "产品质感来自轮廓、阴影和比例。",
        "prompt_style": "silver white palette, minimal tech product scene, clean shadow, premium industrial design",
    },
]

RECOMMENDATION_SEEDS = [
    ("光影之美", "窗影切割空间", "用窗影制造秩序，让画面从普通变得有结构。"),
    ("色彩灵感", "冷灰与金属", "低饱和灰、银白、黑色屏幕，适合科技产品气质。"),
    ("构图美学", "主体偏移", "主体不一定居中，右侧留白能让画面更像广告。"),
    ("生活美学", "一杯咖啡的尺度", "小道具负责生活气息，但不能抢产品的主角位置。"),
    ("电影瞬间", "雾气与层次", "氛围不是靠复杂元素，而是靠空气、距离和光的层次。"),
    ("材质观察", "金属边缘光", "边缘光能让金属产品从背景里分离出来。"),
    ("空间秩序", "水平线稳定", "产品图要先稳，再谈情绪。"),
    ("产品摄影", "屏幕与黑色面板", "黑色区域要有细节，不能变成一块死黑。"),
]

CURATED = [
    {"title": "Photography", "desc": "冷静、克制、薄雾般的色彩层次。", "image": "assets/curated/sel-01.svg"},
    {"title": "Film Still", "desc": "柔和人像与电影气氛，安静但有情绪。", "image": "assets/curated/sel-02.svg"},
    {"title": "Interior Design", "desc": "简洁室内与金属器物的空间关系。", "image": "assets/curated/sel-03.svg"},
    {"title": "Product Design", "desc": "产品轮廓、材质和阴影的平衡。", "image": "assets/curated/sel-04.svg"},
    {"title": "Architecture", "desc": "几何结构、秩序和高级感的来源。", "image": "assets/curated/sel-05.svg"},
]


def now_china() -> dt.datetime:
    if ZoneInfo:
        return dt.datetime.now(ZoneInfo("Asia/Shanghai"))
    return dt.datetime.utcnow() + dt.timedelta(hours=8)


def decide_slot(slot: str, now: dt.datetime) -> str:
    if slot in ("am", "pm"):
        return slot
    return "am" if now.hour < 12 else "pm"


def ensure_dirs() -> None:
    for p in [DATA_PATH.parent, ASSET_CASES, ASSET_RECS, ASSET_INSP, ASSET_CURATED]:
        p.mkdir(parents=True, exist_ok=True)


def load_db() -> Dict[str, Any]:
    if DATA_PATH.exists():
        return json.loads(DATA_PATH.read_text(encoding="utf-8"))
    return {
        "recommendation": {"update": "", "items": []},
        "inspiration": {},
        "quote": {},
        "selection": CURATED,
        "days": [],
    }


def save_db(db: Dict[str, Any]) -> None:
    DATA_PATH.write_text(json.dumps(db, ensure_ascii=False, indent=2), encoding="utf-8")


def pick_theme(date: str) -> Dict[str, str]:
    idx = int(hashlib.md5(date.encode("utf-8")).hexdigest(), 16) % len(THEMES)
    return THEMES[idx]


def chinese_weekday(d: dt.datetime) -> str:
    names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
    return names[d.weekday()]


def make_svg(path: Path, title: str, subtitle: str, palette: str = "light", kind: str = "case") -> None:
    if palette == "dark":
        bg1, bg2, table, text = "#e9ecef", "#bfc5ca", "#22262b", "#ffffff"
    elif palette == "warm":
        bg1, bg2, table, text = "#efede8", "#d4cdc2", "#3a3a3a", "#ffffff"
    else:
        bg1, bg2, table, text = "#f5f6f7", "#dfe3e7", "#d3d7dc", "#111319"

    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="1600" height="900" viewBox="0 0 1600 900">
<defs>
<linearGradient id="bg" x1="0" x2="1"><stop offset="0" stop-color="{bg1}"/><stop offset="1" stop-color="{bg2}"/></linearGradient>
<linearGradient id="metal" x1="0" x2="1"><stop offset="0" stop-color="#f8f9fa"/><stop offset=".5" stop-color="#cfd5dc"/><stop offset="1" stop-color="#ffffff"/></linearGradient>
<filter id="sd"><feDropShadow dx="0" dy="22" stdDeviation="24" flood-color="#000" flood-opacity=".20"/></filter>
</defs>
<rect width="1600" height="900" fill="url(#bg)"/>
<rect x="0" y="622" width="1600" height="278" fill="{table}" opacity=".92"/>
<polygon points="1030,0 1130,0 850,900 760,900" fill="#fff" opacity=".26"/>
<polygon points="1180,0 1270,0 990,900 910,900" fill="#fff" opacity=".18"/>
<polygon points="1330,0 1400,0 1140,900 1080,900" fill="#fff" opacity=".13"/>
<g filter="url(#sd)">
<rect x="620" y="242" width="360" height="378" rx="38" fill="url(#metal)"/>
<rect x="684" y="298" width="214" height="162" rx="22" fill="#121418"/>
<rect x="724" y="332" width="132" height="94" rx="14" fill="#2a2927"/>
<circle cx="790" cy="379" r="28" fill="#b9a176"/>
<rect x="712" y="502" width="154" height="66" rx="15" fill="#1c1d20"/>
<rect x="746" y="526" width="86" height="20" rx="10" fill="#bca37d"/>
<rect x="598" y="302" width="50" height="286" rx="18" fill="#111317"/>
<rect x="705" y="606" width="184" height="18" rx="9" fill="#e6e9ed"/>
</g>
<g opacity=".9">
<rect x="1070" y="605" width="88" height="70" rx="16" fill="#f2f3f4"/>
<path d="M1154 620 C1198 620 1200 662 1152 662" stroke="#f2f3f4" stroke-width="14" fill="none"/>
<rect x="1190" y="578" width="132" height="84" rx="16" fill="#d8dde2" opacity=".72"/>
<circle cx="1240" cy="550" r="29" fill="#697966"/>
<rect x="1235" y="574" width="9" height="65" fill="#5c5e51"/>
</g>
<text x="72" y="114" font-family="Arial, sans-serif" font-size="24" fill="{text}" opacity=".82">{subtitle}</text>
<text x="72" y="188" font-family="Arial, sans-serif" font-size="78" font-weight="700" fill="{text}">{title}</text>
<text x="1360" y="844" text-anchor="end" font-family="Arial, sans-serif" font-size="30" fill="{text}" opacity=".82">Dr.Coffee F15</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def make_rec_svg(path: Path, label: str, i: int) -> None:
    colors = [
        ("#f4f6f8", "#ced4da", "#23262b"),
        ("#eceff1", "#b8c0c8", "#3b424b"),
        ("#f6f6f4", "#dcd9d2", "#222222"),
        ("#eef2f5", "#aeb9c2", "#4c5660"),
        ("#f7f8f9", "#d9dee3", "#151719"),
    ]
    c1, c2, dark = colors[i % len(colors)]
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="620" viewBox="0 0 800 620">
<defs><linearGradient id="g" x1="0" x2="1"><stop offset="0" stop-color="{c1}"/><stop offset="1" stop-color="{c2}"/></linearGradient></defs>
<rect width="800" height="620" fill="url(#g)"/>
<rect x="90" y="390" width="620" height="96" rx="18" fill="{dark}" opacity=".10"/>
<polygon points="90,120 710,120 560,390 210,390" fill="#fff" opacity=".42"/>
<rect x="{190 + i*18}" y="220" width="220" height="150" rx="24" fill="#ffffff" opacity=".82"/>
<rect x="{220 + i*18}" y="250" width="160" height="82" rx="18" fill="{dark}" opacity=".72"/>
<circle cx="{300 + i*18}" cy="292" r="26" fill="#b7a37e"/>
<text x="60" y="548" font-family="Arial" font-size="32" font-weight="700" fill="{dark}" opacity=".72">{label}</text>
</svg>"""
    path.write_text(svg, encoding="utf-8")


def ensure_curated_assets() -> None:
    for idx, item in enumerate(CURATED, 1):
        p = ROOT / item["image"]
        if p.exists():
            continue
        make_rec_svg(p, item["title"], idx)


def generate_with_openai_image(prompt: str, out_path: Path) -> bool:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return False

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        result = client.images.generate(
            model=IMAGE_MODEL,
            prompt=prompt,
            size="1536x1024",
        )
        data0 = result.data[0]
        b64 = getattr(data0, "b64_json", None)
        if b64:
            out_path.write_bytes(base64.b64decode(b64))
            return True

        url = getattr(data0, "url", None)
        if url:
            urllib.request.urlretrieve(url, out_path)
            return True

        return False
    except Exception as exc:
        print(f"[WARN] OpenAI image generation failed: {exc}", file=sys.stderr)
        return False


def generate_with_openai_text(date: str, slot: str, theme: Dict[str, str]) -> Dict[str, Any] | None:
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
        client = OpenAI(api_key=api_key)
        system = "你是一个审美训练内容策划助手。只输出 JSON，不要解释。"
        user = f"""
为 Aesthetic OS 生成 {date} {'晨间' if slot == 'am' else '晚间'} 内容。
要求：
- 风格：大疆感、金属、干净、简单、冷灰白、商业产品摄影。
- 产品：Dr.Coffee F15 全自动咖啡机。
- 同时保留非工作类每日推荐，不要只围绕咖啡机。
- 输出 JSON，字段：
  theme_cn, theme_en, principle, training_desc,
  training: [{{title,text}} x4],
  recommendations: [{{category,title,desc}} x5],
  inspiration: {{title,author,text1,text2}},
  quote: {{en,cn}}
今日主题参考：{theme['prompt_style']}
"""
        resp = client.chat.completions.create(
            model=TEXT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        raw = resp.choices[0].message.content
        return json.loads(raw)
    except Exception as exc:
        print(f"[WARN] OpenAI text generation failed: {exc}", file=sys.stderr)
        return None


def fallback_content(date: str, slot: str, theme: Dict[str, str]) -> Dict[str, Any]:
    rng = random.Random(date + slot)
    recs = rng.sample(RECOMMENDATION_SEEDS, 5)
    return {
        "theme_cn": theme["theme_cn_am"] if slot == "am" else theme["theme_cn_pm"],
        "theme_en": theme["theme_en_am"] if slot == "am" else theme["theme_en_pm"],
        "principle": theme["principle"],
        "training_desc": "今天只训练一个方向：干净、金属感、简洁场景。",
        "training": [
            {"title": "观察光线", "text": "先看光从哪里来，再决定产品放在哪里。"},
            {"title": "理解空间", "text": "只保留必要元素，让画面干净。"},
            {"title": "拍摄思路", "text": "主体不必填满画面，留白是高级感的一部分。"},
            {"title": "色彩情绪", "text": "用浅灰、银白、黑色屏幕建立克制的科技感。"},
        ],
        "recommendations": [
            {"category": c, "title": t, "desc": d}
            for c, t, d in recs
        ],
        "inspiration": {
            "title": "雾中的几何",
            "author": "Aesthetic OS",
            "text1": "冷灰、留白、秩序。",
            "text2": "画面越简单，越需要控制光、比例和边缘。",
        },
        "quote": {
            "en": "Clean is not empty. Clean is controlled.",
            "cn": "干净不是空，而是被控制过。",
        },
    }


def build_image_prompt(slot: str, content: Dict[str, Any], theme: Dict[str, str]) -> str:
    time_desc = "morning soft cool daylight" if slot == "am" else "evening directional soft light"
    return f"""
Create a realistic commercial product photography scene for a Dr.Coffee F15 automatic coffee machine.
Visual style: DJI-inspired, clean, minimalist, metallic, precise, premium technology product photography.
Scene: modern office coffee corner, white-gray background, clean desk, metal and glass materials, subtle reflections.
Lighting: {time_desc}, controlled shadows, clean highlights, no warm yellow cast.
Composition: 16:9 landscape, product slightly off center, generous negative space, high-end B2B advertising.
Product: a compact white/silver automatic coffee machine with black screen panel, boxy industrial design, realistic proportions.
Strict rules: no text, no logos, no watermark, no people, no extra machine, no distorted screen, no messy props.
Theme: {content.get('theme_en', '')}; principle: {content.get('principle', '')}; reference style: {theme['prompt_style']}.
""".strip()


def make_empty_slot(date: str, slot: str) -> Dict[str, Any]:
    theme = pick_theme(date)
    content = fallback_content(date, slot, theme)
    image_path = f"assets/cases/{date}-{slot}-fallback.svg"
    make_svg(ROOT / image_path, content["theme_en"], content["principle"], "light")
    return {
        "themeCn": content["theme_cn"],
        "themeEn": content["theme_en"],
        "product": "F15",
        "principle": content["principle"],
        "trainingDesc": content["training_desc"],
        "training": content["training"],
        "caseTitle": f"F15 白色版｜{content['theme_cn']}案例",
        "caseText": "自动占位内容。下一次对应时段运行后会替换。",
        "image": image_path,
    }


def update_db(db: Dict[str, Any], date: str, now: dt.datetime, slot: str, content: Dict[str, Any], image_path: str) -> None:
    meta_date = f"{now:%Y / %m / %d} · {chinese_weekday(now)}"

    item = {
        "themeCn": content["theme_cn"],
        "themeEn": content["theme_en"],
        "product": "F15",
        "principle": content["principle"],
        "trainingDesc": content["training_desc"],
        "training": content["training"],
        "caseTitle": f"F15 白色版｜{content['theme_cn']}案例",
        "caseText": "冷灰背景、银白机身、简洁道具与受控光影，传递干净、克制、可靠的商业产品气质。",
        "image": image_path,
    }

    days: List[Dict[str, Any]] = db.setdefault("days", [])
    day = next((d for d in days if d.get("date") == date), None)
    if not day:
        day = {
            "date": date,
            "metaDate": meta_date,
            "am": item if slot == "am" else make_empty_slot(date, "am"),
            "pm": item if slot == "pm" else make_empty_slot(date, "pm"),
        }
        days.insert(0, day)
    else:
        day["metaDate"] = meta_date
        day[slot] = item

    db["days"] = sorted(days, key=lambda x: x["date"], reverse=True)

    rec_items = []
    for i, r in enumerate(content["recommendations"], 1):
        rec_path = f"assets/recs/{date}-{slot}-{i:02d}.svg"
        make_rec_svg(ROOT / rec_path, r.get("category", "推荐"), i)
        rec_items.append({
            "category": r.get("category", "推荐"),
            "title": r.get("title", "审美观察"),
            "desc": r.get("desc", "观察光、空间、构图和色彩。"),
            "image": rec_path,
        })
    db["recommendation"] = {
        "update": f"{now:%m.%d} · {'07:30' if slot == 'am' else '18:30'} 更新",
        "items": rec_items,
    }

    insp_path = f"assets/inspiration/{date}-{slot}.svg"
    make_svg(ROOT / insp_path, content["inspiration"]["title"], content["inspiration"]["text1"], "light", "inspiration")
    db["inspiration"] = {
        "title": content["inspiration"].get("title", "今日灵感"),
        "author": content["inspiration"].get("author", "Aesthetic OS"),
        "text1": content["inspiration"].get("text1", ""),
        "text2": content["inspiration"].get("text2", ""),
        "image": insp_path,
    }

    db["quote"] = content.get("quote", {})
    db["selection"] = CURATED
    ensure_curated_assets()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--slot", default="auto", choices=["auto", "am", "pm"])
    args = parser.parse_args()

    ensure_dirs()
    now = now_china()
    date = now.strftime("%Y-%m-%d")
    slot = decide_slot(args.slot, now)
    theme = pick_theme(date)

    db = load_db()

    ai_content = generate_with_openai_text(date, slot, theme)
    content = ai_content or fallback_content(date, slot, theme)

    image_ext = "png" if os.getenv("OPENAI_API_KEY") else "svg"
    image_rel = f"assets/cases/{date}-{slot}.{image_ext}"
    image_abs = ROOT / image_rel

    prompt = build_image_prompt(slot, content, theme)
    ok = generate_with_openai_image(prompt, image_abs)

    if not ok:
        image_rel = f"assets/cases/{date}-{slot}.svg"
        image_abs = ROOT / image_rel
        make_svg(
            image_abs,
            content.get("theme_en", "Aesthetic OS"),
            content.get("principle", "Clean is controlled."),
            "dark" if slot == "pm" else "light",
        )

    update_db(db, date, now, slot, content, image_rel)
    save_db(db)

    print(f"[OK] Updated {date} {slot}. Image: {image_rel}")


if __name__ == "__main__":
    main()
