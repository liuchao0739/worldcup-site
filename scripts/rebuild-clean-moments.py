#!/usr/bin/env python3
"""Rebuild 精彩瞬间 using clean cinematic wallpapers (no text baked in)."""
import json
import colorsys
import shutil
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageEnhance, ImageFilter, ImageOps

ROOT = Path("/Users/liuchao/worldcup-site/site")
ASSETS = Path("/Users/liuchao/.cursor/projects/Users-liuchao/assets")
OUT = ROOT / "media/moments"
OUT.mkdir(parents=True, exist_ok=True)

# (asset_filename, team, title, story)
CATALOG = [
    # Spain
    ("spain-01.png", "西班牙", "赤色宣言", "半决赛夜 · 亚马尔时刻"),
    ("spain-02.png", "西班牙", "雨夜破晓", "半决赛 · 绝杀法国前夜"),
    ("spain-03.png", "西班牙", "通道尽头", "通往决赛的隧道光"),
    ("spain-04.png", "西班牙", "日暮门神", "赛前独影"),
    ("spain-05.png", "西班牙", "相拥成碑", "晋级决赛的拥抱"),
    ("spain-06.png", "西班牙", "红黄雾境", "空场中的斗牛士疆域"),
    # Argentina
    ("argentina-01.png", "阿根廷", "天青礼花", "四强夜的潘帕斯天空"),
    ("argentina-02.png", "阿根廷", "雨中成团", "淘汰赛生死之后"),
    ("argentina-03.png", "阿根廷", "臂章遗落", "一场漫长征程的痕迹"),
    ("argentina-04.png", "阿根廷", "条纹呼吸", "浅蓝白的静默力量"),
    # France
    ("france-01.png", "法国", "疾风蓝影", "八强夜的冲刺"),
    ("france-02.png", "法国", "门线闪电", "扑救定格"),
    ("france-03.png", "法国", "赛前露珠", "蓝色球靴上的等待"),
    # England
    ("england-01.png", "英格兰", "白衣仰光", "逆转之夜"),
    ("england-02.png", "英格兰", "隧道心跳", "半决赛开赛前"),
    # Norway
    ("norway-01.png", "挪威", "峡湾怒吼", "掀翻巴西的那一刻"),
    ("norway-02.png", "挪威", "红影神话", "哈兰德式的压迫感"),
    # Brazil
    ("brazil-01.png", "巴西", "金黄落幕", "十六强夜的沉默"),
    # Portugal
    ("portugal-01.png", "葡萄牙", "红衣升空", "连续进球的庆典"),
    # Morocco
    ("morocco-01.png", "摩洛哥", "北非狂想", "点杀荷兰后的喧嚣"),
    # Belgium
    ("belgium-01.png", "比利时", "离场背影", "八强征途走到尽头"),
    # Switzerland
    ("switzerland-01.png", "瑞士", "冷静时刻", "点球大战后的静"),
    # Germany
    ("germany-01.png", "德国", "冷光黑白", "战车熄火之夜"),
    # Netherlands
    ("netherlands-01.png", "荷兰", "橙色迷雾", "点球出局的荷兰夜"),
    # Japan
    ("japan-01.png", "日本", "更衣室之蓝", "出征前的秩序"),
    # Mexico
    ("mexico-01.png", "墨西哥", "烟绿球场", "阿兹特克的热浪"),
    # USA
    ("usa-01.png", "美国", "条纹灯海", "东道主的主场夜"),
    # Canada
    ("canada-01.png", "加拿大", "北境余温", "枫叶军团的冷场故事"),
]

# Remaining teams: tint ambient wallpapers from base atmosphere frames
BASE_FOR_TINT = "spain-06.png"
TEAM_TONES = {
    "哥伦比亚": (0.08, 0.85, 0.55),   # yellow-ish
    "埃及": (0.0, 0.8, 0.35),
    "韩国": (0.0, 0.75, 0.4),
    "瑞典": (0.12, 0.9, 0.55),
    "奥地利": (0.0, 0.7, 0.45),
    "克罗地亚": (0.98, 0.65, 0.5),
    "澳大利亚": (0.12, 0.8, 0.4),
    "塞内加尔": (0.12, 0.85, 0.45),
    "科特迪瓦": (0.08, 0.8, 0.5),
    "巴拉圭": (0.0, 0.7, 0.4),
    "佛得角": (0.55, 0.6, 0.45),
    "加纳": (0.12, 0.85, 0.45),
    "刚果(金)": (0.15, 0.7, 0.35),
    "南非": (0.12, 0.7, 0.4),
    "厄瓜多尔": (0.14, 0.85, 0.45),
    "波黑": (0.6, 0.5, 0.35),
    "阿尔及利亚": (0.33, 0.6, 0.35),
    "乌拉圭": (0.55, 0.35, 0.45),
    "乌兹别克斯坦": (0.55, 0.55, 0.4),
    "伊拉克": (0.0, 0.6, 0.3),
    "伊朗": (0.33, 0.55, 0.35),
    "卡塔尔": (0.92, 0.55, 0.45),
    "土耳其": (0.0, 0.75, 0.4),
    "巴拿马": (0.0, 0.65, 0.4),
    "库拉索": (0.58, 0.7, 0.4),
    "捷克": (0.0, 0.7, 0.4),
    "新西兰": (0.0, 0.0, 0.2),
    "沙特阿拉伯": (0.33, 0.7, 0.35),
    "海地": (0.58, 0.7, 0.4),
    "突尼斯": (0.0, 0.7, 0.4),
    "约旦": (0.0, 0.55, 0.3),
    "苏格兰": (0.6, 0.45, 0.35),
}

STORY_FALLBACK = {
    "哥伦比亚": ("金色余烬", "止步十六强的夜"),
    "埃及": ("法老落幕", "对决潘帕斯之后"),
    "韩国": ("太极冷光", "小组赛的寂静"),
    "瑞典": ("北欧寒焰", "面对高卢的夜"),
    "奥地利": ("阿尔卑斯回声", "惊险出线记忆"),
    "克罗地亚": ("方格寂静", "末路与骄傲"),
    "澳大利亚": ("袋鼠远征", "点球之夜"),
    "塞内加尔": ("雄狮回望", "三十二强战场"),
    "科特迪瓦": ("象牙咆哮", "淘汰赛瞬时"),
    "巴拉圭": ("南美硬骨头", "肉搏后的尘埃"),
    "佛得角": ("岛国逆风", "逼退强敌的夜"),
    "加纳": ("黑星微光", "小组赛旅程"),
    "刚果(金)": ("刚果脉搏", "远征落幕"),
    "南非": ("彩虹尽头", "世界杯短章"),
    "厄瓜多尔": ("赤道风暴", "出征印记"),
    "波黑": ("巴尔干雨", "小组赛故事"),
    "阿尔及利亚": ("沙漠回声", "出线边缘"),
    "乌拉圭": ("天蓝旧梦", "南美传奇余温"),
    "乌兹别克斯坦": ("丝路远征", "五球失利之夜"),
    "伊拉克": ("两河余烬", "揭幕热身的痛"),
    "伊朗": ("波斯静夜", "小组赛落幕"),
    "卡塔尔": ("从前东道主", "六球之夜"),
    "土耳其": ("新月征途", "重回舞台"),
    "巴拿马": ("地峡之风", "小组赛旅途"),
    "库拉索": ("一球成名", "巨人之侧的勇气"),
    "捷克": ("波希米亚夜", "重返舞台"),
    "新西兰": ("南岛冷光", "大洋洲远征"),
    "沙特阿拉伯": ("绿海落潮", "面对斗牛士"),
    "海地": ("加勒比浪", "世界波瞬间"),
    "突尼斯": ("迦太基静", "四球之夜"),
    "约旦": ("沙漠灯火", "小组赛记忆"),
    "苏格兰": ("格子军团", "出征短章"),
}

EMOJI = {
    "墨西哥": "🇲🇽", "法国": "🇫🇷", "挪威": "🇳🇴", "英格兰": "🏴󠁧󠁢󠁥󠁮󠁧󠁿", "摩洛哥": "🇲🇦",
    "巴西": "🇧🇷", "西班牙": "🇪🇸", "葡萄牙": "🇵🇹", "美国": "🇺🇸", "比利时": "🇧🇪",
    "阿根廷": "🇦🇷", "埃及": "🇪🇬", "瑞士": "🇨🇭", "哥伦比亚": "🇨🇴", "加拿大": "🇨🇦",
    "巴拉圭": "🇵🇾", "荷兰": "🇳🇱", "日本": "🇯🇵", "德国": "🇩🇪", "瑞典": "🇸🇪",
    "科特迪瓦": "🇨🇮", "刚果(金)": "🇨🇩", "奥地利": "🇦🇹", "克罗地亚": "🇭🇷",
    "塞内加尔": "🇸🇳", "波黑": "🇧🇦", "佛得角": "🇨🇻", "加纳": "🇬🇭", "阿尔及利亚": "🇩🇿",
    "澳大利亚": "🇦🇺", "南非": "🇿🇦", "厄瓜多尔": "🇪🇨", "韩国": "🇰🇷", "卡塔尔": "🇶🇦",
    "伊朗": "🇮🇷", "伊拉克": "🇮🇶", "乌拉圭": "🇺🇾", "土耳其": "🇹🇷", "苏格兰": "🏴󠁧󠁢󠁳󠁣󠁴󠁿",
    "新西兰": "🇳🇿", "突尼斯": "🇹🇳", "约旦": "🇯🇴", "乌兹别克斯坦": "🇺🇿", "海地": "🇭🇹",
    "巴拿马": "🇵🇦", "库拉索": "🇨🇼", "捷克": "🇨🇿", "沙特阿拉伯": "🇸🇦",
}


def to_wallpaper(src: Path, dst: Path, size=(1080, 1920)):
    """Export clean wallpaper JPEG — NO text overlays."""
    im = Image.open(src).convert("RGB")
    # Cover-fit to 9:16
    tw, th = size
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    im = im.crop((left, top, left + tw, top + th))
    # subtle polish only
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.05)
    im = ImageEnhance.Sharpness(im).enhance(1.1)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=92, optimize=True, progressive=True)
    return dst


def tint_atmosphere(base: Path, hue: float, sat: float, lit: float, dst: Path):
    """Fast team-mood wallpaper from a clean pitch atmosphere (no text)."""
    im = Image.open(base).convert("RGB")
    tw, th = 1080, 1920
    scale = max(tw / im.width, th / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left = (nw - tw) // 2
    top = (nh - th) // 2
    im = im.crop((left, top, left + tw, top + th))

    rr, gg, bb = colorsys.hls_to_rgb(hue, lit * 0.45, sat)
    tone = Image.new("RGB", (tw, th), (int(rr * 255), int(gg * 255), int(bb * 255)))
    base_dim = ImageEnhance.Brightness(im).enhance(0.72)
    mixed = Image.blend(base_dim, tone, 0.38)
    mixed = ImageEnhance.Contrast(mixed).enhance(1.12)
    mixed = ImageEnhance.Color(mixed).enhance(1.15)

    # soft top/bottom vignette without text
    mask = Image.new("L", (tw, th), 0)
    band = Image.new("L", (tw, th // 5), 140)
    mask.paste(band, (0, 0))
    mask.paste(band, (0, th - th // 5))
    mask = mask.filter(ImageFilter.GaussianBlur(48))
    dark = Image.new("RGB", (tw, th), (0, 0, 0))
    mixed = Image.composite(Image.blend(mixed, dark, 0.4), mixed, mask)
    mixed.save(dst, "JPEG", quality=91, optimize=True, progressive=True)


def heat_of(team: str, farthest: dict, pop: dict) -> int:
    stage = {"决赛": 600, "半决赛": 500, "8强": 400, "16强": 300, "32强": 200, "小组赛": 100}
    return stage.get(farthest.get(team, "小组赛"), 100) * 10 + pop.get(team, 5)


def main():
    data = json.loads((ROOT / "data.json").read_text())
    # Clear old moment jpegs that looked like bilibili posters (keep dirs)
    for p in OUT.glob("*.jpg"):
        # keep only new clean-* later; delete old Chinese-named bilibili composites
        p.unlink()

    by_team = {}
    for asset, team, title, story in CATALOG:
        src = ASSETS / asset
        if not src.exists():
            print("missing", asset)
            continue
        fname = f"clean-{asset.replace('.png', '')}.jpg"
        dst = OUT / fname
        to_wallpaper(src, dst)
        by_team.setdefault(team, []).append(
            {"title": title, "match": story, "cover": f"media/moments/{fname}", "wallpaper": True}
        )
        print("ok", team, title, dst.stat().st_size)

    base = ASSETS / BASE_FOR_TINT
    if not base.exists():
        raise SystemExit("missing base tint asset")
    for team, (h, s, l) in TEAM_TONES.items():
        title, story = STORY_FALLBACK[team]
        fname = f"clean-mood-{abs(hash(team)) % 10**8}.jpg"
        dst = OUT / fname
        tint_atmosphere(base, h, s, l, dst)
        by_team.setdefault(team, []).append(
            {"title": title, "match": story, "cover": f"media/moments/{fname}", "wallpaper": True}
        )
        print("mood", team, title)

    # farthest/pop for sorting — reuse journeys order if present
    journeys = (data.get("highlights") or {}).get("journeys") or []
    heat_map = {j["team"]: j.get("heat", 0) for j in journeys}

    moments = []
    for team, photos in by_team.items():
        moments.append(
            {
                "team": team,
                "flag": EMOJI.get(team, ""),
                "heat": heat_map.get(team, 0),
                "photos": photos,
            }
        )
    moments.sort(key=lambda x: (-x["heat"], x["team"]))

    # keep stages + journeys
    hl = data.get("highlights") or {}
    hl["momentsByCountry"] = moments
    data["highlights"] = hl
    data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")

    print("---")
    print("countries", len(moments), "photos", sum(len(m["photos"]) for m in moments))
    print("top", [(m["team"], len(m["photos"])) for m in moments[:10]])


if __name__ == "__main__":
    main()
