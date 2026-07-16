#!/usr/bin/env python3
"""Export new star assets + refresh 球星风采 catalog (likeness refresh + hot adds)."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path("/Users/liuchao/worldcup-site/site")
ASSETS = Path("/Users/liuchao/.cursor/projects/Users-liuchao/assets")
OUT = ROOT / "media/moments"
OUT.mkdir(parents=True, exist_ok=True)

# name, flag, team, number, rank, title, match, wide, port|None, kind
CARDS = [
    ("梅西", "🇦🇷", "阿根廷", "10", 100, "梅西队长", "雨夜潘帕斯 · 10号", "cine-argentina-captain-wide.png", None, "star"),
    ("梅西", "🇦🇷", "阿根廷", "10", 98, "雨中成团", "蓝白拥抱的一夜", "cine-argentina-huddle-wide.png", "argentina-02.png", "scene"),
    ("亚马尔", "🇪🇸", "西班牙", "19", 99, "亚马尔时刻", "半决赛之光 · 19号", "star-spain-yamal-19-v4-wide.png", None, "star"),
    ("姆巴佩", "🇫🇷", "法国", "10", 97, "姆巴佩冲刺", "高卢锋线 · 10号", "star-france-mbappe-10-wide.png", None, "star"),
    ("C罗", "🇵🇹", "葡萄牙", "7", 95, "C罗远征", "五盾旗帜 · 7号", "star-portugal-cr7-7-wide.png", None, "star"),
    ("哈兰德", "🇳🇴", "挪威", "9", 93, "哈兰德压迫", "红衣神话 · 9号", "star-norway-haaland-9-wide.png", None, "star"),
    ("恩佐", "🇦🇷", "阿根廷", "24", 92, "恩佐引擎", "中场核弹 · 24号", "star-argentina-enzo-24-wide.png", None, "star"),
    ("阿尔瓦雷斯", "🇦🇷", "阿根廷", "9", 91, "蜘蛛侠", "锋线尖刀 · 9号", "star-argentina-alvarez-9-wide.png", None, "star"),
    ("劳塔罗", "🇦🇷", "阿根廷", "22", 90, "劳塔罗绝杀", "决赛班底 · 22号", "star-argentina-lautaro-22-wide.png", None, "star"),
    ("登贝莱", "🇫🇷", "法国", "7", 89, "登贝莱加速", "右边路疯狗 · 7号", "star-france-dembele-7-wide.png", None, "star"),
    ("奥利赛", "🇫🇷", "法国", "11", 88, "奥利赛魔术", "新生代创意 · 11号", "star-france-olise-11-wide.png", None, "star"),
    ("佩德里", "🇪🇸", "西班牙", "20", 87, "佩德里掌控", "中场节拍器 · 20号", "star-spain-pedri-20-v2-wide.png", None, "star"),
    ("维尼修斯", "🇧🇷", "巴西", "7", 86, "维尼修斯", "桑巴前场 · 7号", "star-brazil-vini-7-wide.png", None, "star"),
    ("加克波", "🇳🇱", "荷兰", "11", 85, "加克波冲刺", "橙衣利刃 · 11号", "star-netherlands-gakpo-11-v2-wide.png", None, "star"),
    ("范戴克", "🇳🇱", "荷兰", "4", 84, "范戴克统领", "橙衣铁闸 · 4号", "star-netherlands-vvd-4-wide.png", None, "star"),
    ("尼科·威廉姆斯", "🇪🇸", "西班牙", "17", 83, "尼科边路", "红色闪电 · 17号", "star-spain-nico-17-wide.png", None, "star"),
    ("贝林厄姆", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "英格兰", "10", 82, "贝林厄姆", "三狮核心 · 10号", "star-england-bellingham-10-wide.png", None, "star"),
    ("凯恩", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "英格兰", "9", 81, "凯恩领军", "队长命令 · 9号", "star-england-kane-9-wide.png", None, "star"),
    ("萨卡", "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "英格兰", "7", 80, "萨卡突破", "右边路尖刀 · 7号", "star-england-saka-7-wide.png", None, "star"),
    ("萨拉赫", "🇪🇬", "埃及", "10", 79, "萨拉赫", "法老之刃 · 10号", "star-egypt-salah-10-wide.png", None, "star"),
    ("穆西亚拉", "🇩🇪", "德国", "10", 78, "穆西亚拉", "战车核心 · 10号", "star-germany-musiala-10-wide.png", None, "star"),
    ("德布劳内", "🇧🇪", "比利时", "7", 77, "德布劳内", "红魔调度 · 7号", "star-belgium-kdb-7-wide.png", None, "star"),
    ("孙兴慜", "🇰🇷", "韩国", "7", 76, "孙兴慜", "亚洲天王 · 7号", "star-korea-son-7-wide.png", None, "star"),
    ("迈尼昂", "🇫🇷", "法国", "16", 75, "门线闪电", "扑救定格 · 16号", "star-france-maignan-16-fullgoal-wide.png", None, "star"),
    ("沃齐尼亚", "🇨🇻", "佛得角", "1", 94, "零封西班牙", "神扑封神 · 1号", "star-capeverde-vozinha-1-wide.png", None, "scene"),
    ("扎卡", "🇨🇭", "瑞士", "10", 72, "点球之夜", "红十字 · 10号", "star-switzerland-xhaka-10-wide.png", None, "star"),
    ("图拉姆", "🇫🇷", "法国", "9", 70, "图拉姆冲顶", "高卢9号", "star-france-thuram-9-wide.png", None, "star"),
    ("诺伊尔", "🇩🇪", "德国", "1", 68, "诺伊尔", "最后防线 · 1号", "star-germany-neuer-1-wide.png", None, "star"),
    ("哈基米", "🇲🇦", "摩洛哥", "2", 66, "哈基米", "右侧引擎 · 2号", "star-morocco-hakimi-2-wide.png", None, "star"),
]


def letterbox_to(src: Image.Image, size):
    W, H = size
    img = src.convert("RGB")
    scale = min(W / img.width, H / img.height)
    nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    fg = img.resize((nw, nh), Image.Resampling.LANCZOS)
    bg = img.resize((W, H), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))
    bg = ImageEnhance.Brightness(bg).enhance(0.35)
    canvas = bg.copy()
    canvas.paste(fg, ((W - nw) // 2, (H - nh) // 2))
    return ImageEnhance.Contrast(ImageEnhance.Sharpness(canvas).enhance(1.08)).enhance(1.05)


def export_pair(wide_name, port_name, key):
    wide = ASSETS / wide_name
    if not wide.exists():
        raise FileNotFoundError(wide_name)
    desk_rel = f"media/moments/v5-{key}-desk.jpg"
    port_rel = f"media/moments/v5-{key}-port.jpg"
    letterbox_to(Image.open(wide), (1920, 1080)).save(ROOT / desk_rel, "JPEG", quality=92, optimize=True, progressive=True)
    src = ASSETS / port_name if port_name and (ASSETS / port_name).exists() else wide
    letterbox_to(Image.open(src), (1080, 1920)).save(ROOT / port_rel, "JPEG", quality=92, optimize=True, progressive=True)
    return desk_rel, port_rel


def main():
    data = json.loads((ROOT / "data.json").read_text())
    groups = {}
    for name, flag, team, number, rank, title, match, wide, port, kind in CARDS:
        key = hashlib.md5(f"v5|{name}|{title}|{wide}".encode()).hexdigest()[:10]
        try:
            desk, port_rel = export_pair(wide, port, key)
        except FileNotFoundError as e:
            print("MISSING", e)
            continue
        entry = groups.setdefault(name, {
            "id": name,
            "name": name,
            "flag": flag,
            "team": team,
            "number": number,
            "rank": rank,
            "photos": [],
        })
        if rank > entry.get("rank", 0):
            entry["rank"] = rank
            entry["flag"] = flag
            entry["team"] = team
            entry["number"] = number
        entry["photos"].append({
            "title": title,
            "match": match,
            "cover": port_rel,
            "coverDesktop": desk,
            "wallpaper": True,
            "star": kind == "star",
            "scene": kind == "scene",
            "player": name,
            "team": team,
            "number": number,
        })
        print("OK", name, title)

    stars = sorted(groups.values(), key=lambda x: (-x["rank"], x["name"]))
    for s in stars:
        s.pop("rank", None)

    hl = data.setdefault("highlights", {})
    hl["stars"] = stars
    hl["momentsByCountry"] = []
    data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("--- stars", len(stars), "photos", sum(len(s["photos"]) for s in stars))
    for s in stars:
        print(s["flag"], s["name"], [p["title"] for p in s["photos"]])


if __name__ == "__main__":
    main()
