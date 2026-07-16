#!/usr/bin/env python3
"""Rebuild 精彩瞬间 — unique per card, Messi restored, Swiss/CR7 fixed, full audit."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageEnhance, ImageFilter

ROOT = Path("/Users/liuchao/worldcup-site/site")
OUT = ROOT / "media/moments"
ASSETS = Path("/Users/liuchao/.cursor/projects/Users-liuchao/assets")
OUT.mkdir(parents=True, exist_ok=True)

EMOJI = {
    "西班牙": "🇪🇸", "阿根廷": "🇦🇷", "法国": "🇫🇷", "英格兰": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "挪威": "🇳🇴",
    "巴西": "🇧🇷", "葡萄牙": "🇵🇹", "比利时": "🇧🇪", "摩洛哥": "🇲🇦", "德国": "🇩🇪",
    "荷兰": "🇳🇱", "日本": "🇯🇵", "墨西哥": "🇲🇽", "美国": "🇺🇸", "加拿大": "🇨🇦",
    "瑞士": "🇨🇭", "哥伦比亚": "🇨🇴", "埃及": "🇪🇬", "韩国": "🇰🇷", "瑞典": "🇸🇪",
    "克罗地亚": "🇭🇷", "奥地利": "🇦🇹", "澳大利亚": "🇦🇺", "塞内加尔": "🇸🇳",
    "科特迪瓦": "🇨🇮", "巴拉圭": "🇵🇾", "佛得角": "🇨🇻", "加纳": "🇬🇭", "刚果(金)": "🇨🇩",
    "南非": "🇿🇦", "厄瓜多尔": "🇪🇨", "波黑": "🇧🇦", "阿尔及利亚": "🇩🇿", "乌拉圭": "🇺🇾",
    "乌兹别克斯坦": "🇺🇿", "伊拉克": "🇮🇶", "伊朗": "🇮🇷", "卡塔尔": "🇶🇦", "土耳其": "🇹🇷",
    "巴拿马": "🇵🇦", "库拉索": "🇨🇼", "捷克": "🇨🇿", "新西兰": "🇳🇿", "沙特阿拉伯": "🇸🇦",
    "海地": "🇭🇹", "突尼斯": "🇹🇳", "约旦": "🇯🇴", "苏格兰": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
}

# (team, title, match, wide_asset, port_asset|None, letterbox)
# 阿根廷：梅西两张好图放最前（用户点名截图二）
# 号码按 FIFA 2026 官方大名单（格列兹曼未入选法国）
STAR_CARDS = [
    # Argentina — Messi first
    ("阿根廷", "梅西队长", "雨夜潘帕斯 · 10号", "cine-argentina-captain-wide.png", None, True),
    ("阿根廷", "雨中成团", "蓝白拥抱的一夜", "cine-argentina-huddle-wide.png", "argentina-02.png", True),
    ("阿根廷", "恩佐引擎", "中场核弹 · 24号", "star-argentina-enzo-24-wide.png", None, True),
    ("阿根廷", "蜘蛛侠", "锋线尖刀 · 9号", "star-argentina-alvarez-9-wide.png", None, True),
    # Spain — Yamal first
    ("西班牙", "亚马尔时刻", "半决赛之光 · 19号", "star-spain-yamal-19-wide.png", None, True),
    ("西班牙", "佩德里掌控", "中场节拍器 · 20号", "star-spain-pedri-20-wide.png", None, True),
    ("西班牙", "尼科边路", "红色闪电 · 17号", "star-spain-nico-17-wide.png", None, True),
    ("西班牙", "日落门神", "赛前独影 · 23号", "star-spain-gk-23-wide.png", None, True),
    # France — no Griezmann (not in 2026 squad)
    ("法国", "姆巴佩冲刺", "高卢锋线 · 10号", "star-france-mbappe-10-wide.png", None, True),
    ("法国", "登贝莱加速", "右边路疯狗 · 7号", "star-france-dembele-7-wide.png", None, True),
    ("法国", "奥利赛魔术", "新生代创意 · 11号", "star-france-olise-11-wide.png", None, True),
    ("法国", "图拉姆冲顶", "高卢9号", "star-france-thuram-9-wide.png", None, True),
    ("法国", "门线闪电", "扑救定格 · 16号", "star-france-maignan-16-netbehind-fromport-wide.png", "star-france-maignan-16-netbehind-port.png", True),
    # England
    ("英格兰", "贝林厄姆", "三狮核心 · 10号", "star-england-bellingham-10-wide.png", None, True),
    ("英格兰", "萨卡突破", "右边路尖刀 · 7号", "star-england-saka-7-wide.png", None, True),
    ("英格兰", "凯恩领军", "队长命令 · 9号", "star-england-kane-9-wide.png", None, True),
    # Norway / Brazil / Portugal
    ("挪威", "哈兰德压迫", "红衣神话 · 9号", "star-norway-haaland-9-wide.png", None, True),
    ("巴西", "维尼修斯", "桑巴前场 · 7号", "star-brazil-vini-7-wide.png", None, True),
    ("葡萄牙", "C罗远征", "五盾旗帜 · 7号", "star-portugal-cr7-7-wide.png", None, True),
    # Netherlands early among European powers
    ("荷兰", "橙衣落幕", "点球出局之夜", "star-netherlands-full-wide.png", None, True),
    # Morocco / Belgium / Germany / Swiss
    ("摩洛哥", "哈基米", "右侧引擎 · 2号", "star-morocco-hakimi-2-wide.png", None, True),
    ("比利时", "德布劳内", "红魔调度 · 7号", "star-belgium-kdb-7-wide.png", None, True),
    ("德国", "诺伊尔", "最后防线 · 1号", "star-germany-neuer-1-wide.png", None, True),
    ("瑞士", "点球之夜", "红十字庆祝", "star-switzerland-wide.png", "switzerland-01.png", False),
    # More named teams
    ("日本", "蓝武士", "出征前的秩序", "star-japan-wide.png", None, False),
    ("墨西哥", "烟绿球场", "阿兹特克热浪", "star-mexico-wide.png", None, False),
    ("美国", "条纹灯海", "东道主之夜", "star-usa-wide.png", None, False),
    ("加拿大", "北境余温", "枫叶军团", "star-canada-wide.png", None, False),
    ("哥伦比亚", "金色风暴", "南美热血", "star-colombia-wide.png", None, False),
    ("埃及", "萨拉赫", "法老之刃 · 10号", "star-egypt-salah-10-wide.png", None, True),
    ("韩国", "孙兴慜", "亚洲天王 · 7号", "star-korea-son-7-wide.png", None, True),
]


def letterbox_to(src: Image.Image, size, fill_blur=True):
    """Fit entire subject into frame — never crop limbs."""
    W, H = size
    img = src.convert("RGB")
    scale = min(W / img.width, H / img.height)
    nw, nh = max(1, int(img.width * scale)), max(1, int(img.height * scale))
    fg = img.resize((nw, nh), Image.Resampling.LANCZOS)

    if fill_blur:
        bg = img.resize((W, H), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))
        bg = ImageEnhance.Brightness(bg).enhance(0.35)
    else:
        bg = Image.new("RGB", (W, H), (8, 14, 22))
    canvas = bg.copy()
    canvas.paste(fg, ((W - nw) // 2, (H - nh) // 2))
    return ImageEnhance.Contrast(canvas).enhance(1.05)


def cover_to(src: Image.Image, size, bias_left=False):
    W, H = size
    img = src.convert("RGB")
    scale = max(W / img.width, H / img.height)
    nw, nh = int(img.width * scale + 0.5), int(img.height * scale + 0.5)
    img = img.resize((nw, nh), Image.Resampling.LANCZOS)
    if bias_left:
        left = max(0, int(nw * 0.22) - W // 2)
        left = min(left, nw - W)
    else:
        left = (nw - W) // 2
    top = (nh - H) // 2
    return img.crop((left, top, left + W, top + H))


def export_desk(src: Path, dst: Path, letterbox: bool):
    im = Image.open(src)
    out = letterbox_to(im, (1920, 1080)) if letterbox else cover_to(im, (1920, 1080))
    out = ImageEnhance.Sharpness(out).enhance(1.08)
    out.save(dst, "JPEG", quality=92, optimize=True, progressive=True)


def export_port(src: Path, dst: Path, letterbox: bool):
    im = Image.open(src)
    if letterbox:
        out = letterbox_to(im, (1080, 1920))
    else:
        # face-biased portrait from landscape
        out = cover_to(im, (1080, 1920), bias_left=True)
    out = ImageEnhance.Sharpness(out).enhance(1.1)
    out.save(dst, "JPEG", quality=92, optimize=True, progressive=True)


def tint_unique(base: Path, seed: str, dst_desk: Path, dst_port: Path):
    import colorsys
    im = Image.open(base).convert("RGB")
    W, H = 1920, 1080
    bg = cover_to(im, (W, H))
    h = (int(hashlib.md5(seed.encode()).hexdigest()[:6], 16) % 1000) / 1000.0
    rr, gg, bb = colorsys.hls_to_rgb(h, 0.32, 0.5)
    tone = Image.new("RGB", (W, H), (int(rr * 255), int(gg * 255), int(bb * 255)))
    mixed = Image.blend(ImageEnhance.Brightness(bg).enhance(0.68), tone, 0.32)
    mixed = ImageEnhance.Contrast(mixed).enhance(1.1)
    mixed.save(dst_desk, "JPEG", quality=90, optimize=True, progressive=True)
    export_port(dst_desk, dst_port, letterbox=True)


def main():
    data = json.loads((ROOT / "data.json").read_text())
    journeys = (data.get("highlights") or {}).get("journeys") or []
    heat = {j["team"]: j.get("heat", 0) for j in journeys}

    used_desk, used_port = set(), set()
    by_team = {}

    for team, title, match, wide_name, port_name, letterbox in STAR_CARDS:
        wide_src = ASSETS / wide_name
        if not wide_src.exists():
            print("MISSING", wide_name)
            continue
        key = hashlib.md5(f"v4|{team}|{title}|{wide_name}|{port_name}".encode()).hexdigest()[:10]
        desk_rel = f"media/moments/v4-{key}-desk.jpg"
        port_rel = f"media/moments/v4-{key}-port.jpg"
        export_desk(wide_src, ROOT / desk_rel, letterbox=letterbox)
        if port_name and (ASSETS / port_name).exists():
            # 独立竖版素材：按 9:16 完整入画（手机专用）
            export_port(ASSETS / port_name, ROOT / port_rel, letterbox=True)
        else:
            # 无独立竖版时：横图 letterbox 成 9:16，全身可见，对齐电脑端效果
            export_port(wide_src, ROOT / port_rel, letterbox=True)

        assert desk_rel not in used_desk
        assert port_rel not in used_port
        used_desk.add(desk_rel)
        used_port.add(port_rel)

        by_team.setdefault(team, []).append({
            "title": title,
            "match": match,
            "cover": port_rel,
            "coverDesktop": desk_rel,
            "wallpaper": True,
            "star": True,
        })
        print("OK", team, title, "letterbox" if letterbox else "cover")

    # Remaining teams: unique tinted football ambients from football bases only
    bases = [
        ASSETS / n for n in [
            "star-switzerland-wide.png",
            "star-netherlands-wide.png",
            "star-japan-wide.png",
            "star-france-gk-wide.png",
            "star-norway-haaland-wide.png",
        ] if (ASSETS / n).exists()
    ]
    remaining = [t for t in EMOJI if t not in by_team]
    for i, team in enumerate(sorted(remaining, key=lambda t: (-heat.get(t, 0), t))):
        base = bases[i % len(bases)]
        key = hashlib.md5(f"v4|amb|{team}".encode()).hexdigest()[:10]
        desk_rel = f"media/moments/v4amb-{key}-desk.jpg"
        port_rel = f"media/moments/v4amb-{key}-port.jpg"
        tint_unique(base, team + "football", ROOT / desk_rel, ROOT / port_rel)
        assert desk_rel not in used_desk
        used_desk.add(desk_rel)
        used_port.add(port_rel)
        by_team[team] = [{
            "title": f"{team}远征",
            "match": "世界杯印记",
            "cover": port_rel,
            "coverDesktop": desk_rel,
            "wallpaper": True,
        }]
        print("AMB", team)

    # Tab order: put major football powers with star cards near the front
    TAB_BOOST = {
        "西班牙": 9000, "阿根廷": 8900, "法国": 8800, "英格兰": 8700,
        "荷兰": 8600, "巴西": 8500, "葡萄牙": 8400, "德国": 8300,
        "挪威": 8200, "比利时": 8100, "摩洛哥": 8000, "瑞士": 7900,
        "日本": 7800, "墨西哥": 7700, "美国": 7600, "加拿大": 7500,
        "哥伦比亚": 7400, "埃及": 7300, "韩国": 7200,
    }
    moments = [{
        "team": team,
        "flag": EMOJI.get(team, ""),
        "heat": heat.get(team, 0),
        "photos": photos,
    } for team, photos in by_team.items()]
    moments.sort(key=lambda x: (
        -TAB_BOOST.get(x["team"], x["heat"]),
        -x["heat"],
        x["team"],
    ))

    desks = [p["coverDesktop"] for c in moments for p in c["photos"]]
    ports = [p["cover"] for c in moments for p in c["photos"]]
    assert len(desks) == len(set(desks))
    assert len(ports) == len(set(ports))

    data["highlights"]["momentsByCountry"] = moments
    data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    print("---")
    for t in ["阿根廷", "瑞士", "葡萄牙", "西班牙", "法国"]:
        print(t, [p["title"] for p in by_team[t]])
    print("photos", len(desks), "unique desks/ports ok")


if __name__ == "__main__":
    main()
