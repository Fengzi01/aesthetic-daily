#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations
import argparse, datetime as dt, hashlib, json, random
from pathlib import Path
try:
    from zoneinfo import ZoneInfo
except Exception:
    ZoneInfo = None

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "content.json"

STATIC_CASE_IMAGES = {"am":"assets/cases/f15-office-am.svg","pm":"assets/cases/f15-office-pm.svg"}

THEMES = [
    {"am_cn":"清晨金属冷白","am_en":"Clean Metal Morning","pm_cn":"金属感办公空间","pm_en":"Minimal Metal Office","principle":"干净不是空，而是每个元素都有理由。","case":"用冷灰、银白、黑色屏幕和少量桌面道具，建立干净、可靠、科技感的产品气质。","training":[("观察力训练","捕捉金属表面的细节、光泽与材质变化。"),("空间感训练","理解空间层次与留白，提升画面秩序感。"),("构图训练","学习简洁构图法则，平衡视觉引导。"),("色彩训练","掌握金属色与中性色营造高级感。")]},
    {"am_cn":"百叶光影与留白","am_en":"Blinds Light and Space","pm_cn":"冷灰百叶光影","pm_en":"Cool Gray Blinds Light","principle":"光影负责情绪，留白负责高级感。","case":"让百叶光影落在墙面和台面，产品只吃到边缘光，画面会更有秩序。","training":[("找光影","先找墙面的光影节奏，不急着摆产品。"),("控主体","产品位置要稳，不要被光影切得太乱。"),("留空白","右侧或上方保留干净区域。"),("压对比","暗部要有细节，不要变成死黑。")]},
    {"am_cn":"银白空间","am_en":"Silver White Space","pm_cn":"银白极简场景","pm_en":"Silver Minimal Scene","principle":"产品质感来自轮廓、阴影和比例。","case":"用银白、浅灰、黑色屏幕建立产品的工业设计感，避免暖色过多。","training":[("看轮廓","先判断产品外轮廓是否清楚。"),("看阴影","阴影要轻，但不能完全没有。"),("看比例","产品和桌面的比例决定画面是否稳定。"),("看颜色","冷灰和银白要干净，不要偏脏。")]}
]
RECS=[("光影之美","窗影切割空间","用窗影制造秩序，让画面从普通变得有结构。"),("色彩灵感","冷灰与金属","低饱和灰、银白、黑色屏幕，适合科技产品气质。"),("构图美学","主体偏移","主体不一定居中，右侧留白能让画面更像广告。"),("生活美学","一杯咖啡的尺度","小道具负责生活气息，但不能抢产品的主角位置。"),("电影瞬间","雾气与层次","氛围不是靠复杂元素，而是靠空气、距离和光的层次。"),("材质观察","金属边缘光","边缘光能让金属产品从背景里分离出来。"),("空间秩序","水平线稳定","产品图要先稳，再谈情绪。"),("建筑秩序","几何线条","高级感常来自稳定的几何关系，而不是复杂装饰。")]
REFS=[
    {"type":"半自动咖啡机","brand":"La Marzocco","name":"Linea Mini","tag":"金属 / 留白 / 家用专业感","reason":"适合参考银白机身、工业线条和干净台面的关系。","image":"assets/references/ref-01.svg","source":"La Marzocco Home","url":"https://home.lamarzoccousa.com/linea-mini/"},
    {"type":"半自动咖啡机","brand":"Breville","name":"Oracle Touch","tag":"屏幕 / 金属 / 自动化","reason":"适合参考黑色屏幕、金属正面和家用场景的结合。","image":"assets/references/ref-02.svg","source":"Breville","url":"https://www.breville.com/en-us/product/bes990"},
    {"type":"全自动咖啡机","brand":"JURA","name":"Z10","tag":"高级全自动 / 冷灰 / 屏幕界面","reason":"适合参考全自动机器的前脸比例、屏幕和黑银材质对比。","image":"assets/references/ref-03.svg","source":"JURA","url":"https://www.jura.com/"},
    {"type":"全自动咖啡机","brand":"De'Longhi","name":"Eletta Explore","tag":"家用全自动 / 白银配色","reason":"适合参考轻家用场景、饮品系统和清爽产品表达。","image":"assets/references/ref-04.svg","source":"De'Longhi","url":"https://www.delonghi.com/"},
    {"type":"商用全自动","brand":"Eversys","name":"Cameo","tag":"商用 / 黑银 / 稳定正面","reason":"适合参考商用咖啡机的专业感与吧台比例。","image":"assets/references/ref-05.svg","source":"Eversys","url":"https://www.eversys.com/"},
    {"type":"半自动咖啡机","brand":"Rocket","name":"Espresso Machine","tag":"不锈钢 / 高反光 / 轮廓","reason":"适合参考不锈钢高反光产品如何控制高光。","image":"assets/references/ref-06.svg","source":"Rocket Espresso","url":"https://rocket-espresso.com/"}
]
QUOTES=[("Clean is not empty. Clean is controlled.","干净不是空，而是被控制过。"),("Don't chase light. Understand light.","不要追逐光，先理解光。"),("Less information, stronger product.","信息越少，产品越强。"),("Space first. Product second.","先建立空间，再呈现产品。")]
CURATED=[{"title":"Photography","desc":"冷静、克制、薄雾般的色彩层次。","image":"assets/curated/sel-01.svg"},{"title":"Film Still","desc":"柔和人像与电影气氛，安静但有情绪。","image":"assets/curated/sel-02.svg"},{"title":"Interior Design","desc":"简洁室内与金属器物的空间关系。","image":"assets/curated/sel-03.svg"},{"title":"Product Design","desc":"产品轮廓、材质和阴影的平衡。","image":"assets/curated/sel-04.svg"},{"title":"Architecture","desc":"几何结构、秩序和高级感的来源。","image":"assets/curated/sel-05.svg"}]

def now_cn(): return dt.datetime.now(ZoneInfo("Asia/Shanghai")) if ZoneInfo else dt.datetime.utcnow()+dt.timedelta(hours=8)
def slot_of(s,now): return s if s in ("am","pm") else ("am" if now.hour<12 else "pm")
def pick(seed,arr): return arr[int(hashlib.md5(seed.encode()).hexdigest(),16)%len(arr)]
def week(d): return ["周一","周二","周三","周四","周五","周六","周日"][d.weekday()]
def load(): return json.loads(DATA.read_text(encoding="utf-8")) if DATA.exists() else {"days":[]}
def save(db): DATA.parent.mkdir(parents=True,exist_ok=True); DATA.write_text(json.dumps(db,ensure_ascii=False,indent=2),encoding="utf-8")
def slot_item(theme,slot):
    cn=theme["am_cn"] if slot=="am" else theme["pm_cn"]; en=theme["am_en"] if slot=="am" else theme["pm_en"]
    return {"themeCn":cn,"themeEn":en,"product":"F15","principle":theme["principle"],"trainingDesc":"今天只训练一个方向：干净、金属感、简洁场景。","training":[{"title":a,"text":b} for a,b in theme["training"]],"caseTitle":f"F15 白色版｜{cn}案例","caseText":theme["case"],"image":STATIC_CASE_IMAGES[slot]}
def update(db,now,slot):
    date=now.strftime("%Y-%m-%d"); theme=pick(date,THEMES); days=db.setdefault("days",[])
    day=next((d for d in days if d.get("date")==date),None)
    if not day:
        day={"date":date,"metaDate":f"{now:%Y / %m / %d} · {week(now)}","am":slot_item(theme,"am"),"pm":slot_item(theme,"pm")}
        days.insert(0,day)
    else:
        day["metaDate"]=f"{now:%Y / %m / %d} · {week(now)}"; day[slot]=slot_item(theme,slot)
    db["days"]=sorted(days,key=lambda x:x["date"],reverse=True)
    rng=random.Random(date+slot); chosen=rng.sample(RECS,5)
    db["recommendation"]={"update":f"{now:%m.%d} · {'07:30' if slot=='am' else '18:30'} 更新","items":[{"category":c,"title":t,"desc":d,"image":f"assets/recs/rec-{i+1:02d}.svg"} for i,(c,t,d) in enumerate(chosen)]}
    refs=rng.sample(REFS,4)
    db["productReferences"]={"update":f"{now:%m.%d} · Product Reference","items":refs}
    db["inspiration"]={"title":"雾中的几何","author":"Aesthetic OS","text1":"冷灰、留白、秩序。","text2":"画面越简单，越需要控制光、比例和边缘。","image":"assets/inspiration/inspiration-01.svg"}
    en,cn=pick(date+slot+"quote",QUOTES); db["quote"]={"en":en,"cn":cn}; db["selection"]=CURATED
def main():
    ap=argparse.ArgumentParser(); ap.add_argument("--slot",default="auto",choices=["auto","am","pm"]); args=ap.parse_args()
    now=now_cn(); slot=slot_of(args.slot,now); db=load(); update(db,now,slot); save(db); print(f"[OK] final reference update: {slot}")
if __name__=="__main__": main()
