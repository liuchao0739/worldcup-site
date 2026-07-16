#!/usr/bin/env python3
"""Rebuild highlights: poster wallpapers, stage reel covers, unique 48-team journeys."""
import json
import urllib.request
import urllib.parse
import time
import re
import io
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageDraw, ImageFilter, ImageEnhance, ImageFont

UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
)
ROOT = Path("/Users/liuchao/worldcup-site/site")
MEDIA_M = ROOT / "media/moments"
MEDIA_J = ROOT / "media/journeys"
MEDIA_R = ROOT / "media/reels"
for p in (MEDIA_M, MEDIA_J, MEDIA_R):
    p.mkdir(parents=True, exist_ok=True)

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

NAME_MAP = {
    "Czechia ❌": "捷克", "Czechia": "捷克",
    "Senegal": "塞内加尔", "Senegal 🟡": "塞内加尔",
    "South Korea": "韩国", "South Korea 🟡": "韩国",
}

POP = {
    "阿根廷": 90, "西班牙": 88, "法国": 86, "英格兰": 84, "巴西": 82,
    "葡萄牙": 70, "德国": 68, "荷兰": 66, "挪威": 72, "比利时": 55,
    "墨西哥": 60, "美国": 58, "日本": 52, "摩洛哥": 50, "瑞士": 40,
    "克罗地亚": 38, "乌拉圭": 36, "哥伦比亚": 34, "加拿大": 32, "韩国": 30,
    "埃及": 28, "塞内加尔": 26, "奥地利": 22, "瑞典": 20, "澳大利亚": 18,
    "科特迪瓦": 16, "加纳": 14, "巴拉圭": 12, "佛得角": 15, "刚果(金)": 10,
}

TEAM_COLORS = {
    "西班牙": ((200, 16, 46), (250, 190, 0)),
    "阿根廷": ((116, 172, 223), (255, 255, 255)),
    "法国": ((0, 35, 149), (237, 41, 57)),
    "英格兰": ((34, 52, 140), (200, 16, 46)),
    "挪威": ((186, 12, 47), (0, 32, 91)),
    "巴西": ((0, 156, 59), (255, 223, 0)),
    "比利时": ((0, 0, 0), (250, 190, 0)),
    "摩洛哥": ((193, 39, 45), (0, 98, 51)),
    "瑞士": ((255, 0, 0), (255, 255, 255)),
    "葡萄牙": ((0, 102, 0), (255, 0, 0)),
    "德国": ((0, 0, 0), (255, 206, 0)),
    "荷兰": ((255, 102, 0), (255, 255, 255)),
    "日本": ((188, 0, 45), (255, 255, 255)),
    "墨西哥": ((0, 104, 71), (206, 17, 38)),
    "美国": ((60, 59, 110), (178, 34, 52)),
    "加拿大": ((255, 0, 0), (255, 255, 255)),
    "埃及": ((206, 17, 38), (0, 0, 0)),
    "韩国": ((0, 71, 160), (205, 46, 58)),
}

STAGE_SCORE = {"决赛": 600, "半决赛": 500, "8强": 400, "16强": 300, "32强": 200, "小组赛": 100}

# Curated unique BVs — must remain unique across all teams
JOURNEY_BV = {
    "西班牙": "BV1ooNh6AEBN",
    "阿根廷": "BV119Nz6TEb6",
    "英格兰": "BV1QyNz6VEAx",
    "法国": "BV1bkN56BEBx",
    "挪威": "BV1RBT96hEY1",
    "巴西": "BV1WRTS6NENr",
    "比利时": "BV1eDNp6NEGC",
    "摩洛哥": "BV1mXNE67Eqx",
    "瑞士": "BV1LZNM6NEUv",
    "葡萄牙": "BV19DjS6uE8V",
    "墨西哥": "BV1kdTS6YEub",
    "美国": "BV1wHMx6YEWY",
    "日本": "BV1ZrK96vEoY",
    "德国": "BV1NrTe6ZE1q",
    "荷兰": "BV18gKf6AEXu",
    "哥伦比亚": "BV1ibMv6UEwE",
    "加拿大": "BV1rBj664Ezy",
    "埃及": "BV18nMe6KEHv",
    "巴拉圭": "BV1pmMM6QE2t",
    "瑞典": "BV138Te6KEPp",
    "科特迪瓦": "BV1VJEP6DEyR",
    "刚果(金)": "BV116Tp6fECG",
    "奥地利": "BV1GeTK6fEXV",
    "克罗地亚": "BV1E4T76PEhj",
    "塞内加尔": "BV1BLj56jEqC",
    "波黑": "BV1sR746wEDZ",
    "佛得角": "BV1EyMF6QEsB",
    "加纳": "BV1mKL26UEiE",
    "阿尔及利亚": "BV1wVTL6NEvr",
    "澳大利亚": "BV1tiTo68EQJ",
    "南非": "BV1z8Kf6EEBz",  # placeholder reused? NO - use unique
    "厄瓜多尔": "BV1H77i6EExN",
    "韩国": "BV1MUje6xEZD",
    "卡塔尔": "BV1kCjv6mEAg",
    "伊朗": "BV16G4y1t7zi",
    "伊拉克": "BV1yPjj6aEC4",
    "乌拉圭": "BV1WG4y1z76Y",
    "土耳其": "BV1nqKgz8EA2",
    "苏格兰": "BV1eJNK6HEwK",
    "新西兰": "BV19Y4y1s7sq",
    "突尼斯": "BV1u6jt6qEWL",
    "约旦": "BV12uTM69EBH",
    "乌兹别克斯坦": "BV1cCjd6uEq3",
    "海地": "BV1gs7t6rEyr",
    "巴拿马": "BV1XKjs6AEPS",
    "库拉索": "BV1KYJM6HE83",
    "捷克": "BV1DJ9VBsEfj",
    "沙特阿拉伯": "BV1rh7g6CEWE",
}

# Fix Africa South Africa collision if any - use dedicated
JOURNEY_BV["南非"] = "BV1wGNc6QEEp"

# Extra high-quality covers for poster moments (team -> list of (title, match, bv))
MOMENT_EXTRA = {
    "西班牙": [
        ("亚马尔锁定决赛", "半决赛 · vs 法国", "BV147Na6UEdV"),
        ("波罗封印法国", "半决赛 · vs 法国", "BV11rNh6VEFK"),
        ("梅里诺绝杀比利时", "8强 · vs 比利时", "BV1eDNp6NEGC"),
        ("晋级决赛夜", "半决赛复盘", "BV1ooNh6AEBN"),
        ("斗牛士统治力", "半决赛精华", "BV1hPNz6rEjf"),
        ("西班牙4-0沙特", "小组赛高光", "BV1rh7g6CEWE"),
    ],
    "阿根廷": [
        ("逆转英格兰晋级决赛", "半决赛 · vs 英格兰", "BV119Nz6TEb6"),
        ("梅西传奇夜", "16强 · vs 埃及", "BV1f7Mh66Eaf"),
        ("阿尔瓦雷斯世界波", "8强 · vs 瑞士", "BV1LZNM6NEUv"),
        ("绝杀埃及解说", "16强名场面", "BV18nMe6KEHv"),
        ("蓝白风暴", "淘汰赛高光", "BV121MY6FEuE"),
    ],
    "英格兰": [
        ("半决赛止步阿根廷", "半决赛 · vs 阿根廷", "BV1KQNz6zEhc"),
        ("贝林厄姆双响", "8强 · vs 挪威", "BV1pBNK6uEZB"),
        ("三狮逆转挪威", "8强精华", "BV1VdNK6oEZJ"),
        ("英格兰3-2墨西哥", "16强惊魂", "BV1kdTS6YEub"),
        ("贝林厄姆封神", "16强复盘", "BV15vTQ6dEgQ"),
    ],
    "法国": [
        ("姆巴佩破门", "8强 · vs 摩洛哥", "BV1mXNE67EG6"),
        ("高卢雄鸡挺进四强", "8强精华", "BV1bkN56BEBx"),
        ("法国淘汰瑞典", "32强碾压", "BV138Te6KEPp"),
        ("半决赛落幕", "半决赛 · vs 西班牙", "BV11rNh6VEFK"),
    ],
    "挪威": [
        ("哈兰德双响", "16强 · vs 巴西", "BV1E6TU6REv6"),
        ("哈兰德暴力美学", "世界杯征程", "BV1RBT96hEY1"),
        ("爆冷掀翻巴西", "16强冷门", "BV1WRTS6NENr"),
        ("止步英格兰", "8强加时", "BV1VdNK6oEZJ"),
    ],
    "巴西": [
        ("五星悲歌", "16强止步挪威", "BV1WRTS6NENr"),
        ("内马尔点射", "淘汰赛瞬间", "BV1ZrK96vEoY"),
        ("桑巴落幕", "世界杯征程", "BV1E6TU6REv6"),
    ],
    "葡萄牙": [
        ("C罗双响", "小组赛 · vs 乌兹别克斯坦", "BV19DjS6uE8V"),
        ("连续六届进球", "葡萄牙征程", "BV1cCjd6uEq3"),
        ("加时绝杀克罗地亚", "淘汰赛", "BV1E4T76PEhj"),
    ],
    "比利时": [
        ("红魔绝杀塞内加尔", "32强", "BV1g1T66JENm"),
        ("比利时大战美国", "16强", "BV1wHMx6YEWY"),
        ("止步西班牙", "8强", "BV1eDNp6NEGC"),
    ],
    "摩洛哥": [
        ("点杀荷兰", "32强血战", "BV18gKf6AEXu"),
        ("摩洛哥止步法国", "8强复盘", "BV1mXNE67Eqx"),
        ("非洲雄狮", "淘汰赛征程", "BV1ELTw6xE7B"),
    ],
    "德国": [
        ("德国点球史", "战车落幕", "BV1NrTe6ZE1q"),
        ("诺伊尔谢幕", "淘汰赛", "BV1T8Kd6QEJF"),
        ("德国7-1库拉索", "小组赛", "BV1KYJM6HE83"),
    ],
    "荷兰": [
        ("荷兰点球出局", "vs 摩洛哥", "BV18gKf6AEXu"),
        ("橙衣落幕", "淘汰赛", "BV1ELTw6xE7B"),
    ],
    "日本": [
        ("蓝武士止步巴西", "32强", "BV1ZrK96vEoY"),
        ("日本4-0突尼斯", "小组赛", "BV1u6jt6qEWL"),
    ],
    "墨西哥": [
        ("墨西哥惜败英格兰", "16强", "BV1kdTS6YEub"),
        ("阿兹特克怒吼", "淘汰赛", "BV1vGTD6QEiV"),
    ],
    "美国": [
        ("美国止步比利时", "16强", "BV1wHMx6YEWY"),
    ],
    "瑞士": [
        ("瑞士点杀哥伦比亚", "16强", "BV1ibMv6UEwE"),
        ("十字军止步阿根廷", "8强", "BV1LZNM6NEUv"),
    ],
    "加拿大": [
        ("加拿大6-0卡塔尔", "小组赛", "BV1rBj664Ezy"),
        ("枫叶风暴", "淘汰赛", "BV1kCjv6mEAg"),
    ],
    "韩国": [
        ("韩国1-0墨西哥？", "小组瞬间", "BV1MUje6xEZD"),
        ("太极虎出局", "vs 南非", "BV1z8Kf6EEBz"),
    ],
    "埃及": [
        ("法老遗憾落幕", "16强 vs 阿根廷", "BV18nMe6KEHv"),
        ("埃及点杀澳大利亚", "32强", "BV1tiTo68EQJ"),
    ],
}

CUSTOM_PATH = {
    "西班牙": "小组头名 → 淘汰奥/葡/比 → 半决赛击败法国 → 决赛",
    "阿根廷": "小组全胜 → 加时过佛得角/埃及 → 加时过瑞士 → 半决赛逆转英格兰 → 决赛",
    "英格兰": "小组出线 → 过墨西哥 → 加时逆转挪威 → 半决赛止步阿根廷",
    "法国": "小组强势 → 过瑞典/巴拉圭/摩洛哥 → 半决赛止步西班牙",
    "挪威": "小组出线 → 过科特迪瓦/巴西 → 加时止步英格兰",
    "巴西": "小组出线 → 32强过日本 → 16强止步挪威",
    "比利时": "小组出线 → 过塞内加尔/美国 → 8强止步西班牙",
    "摩洛哥": "小组出线 → 点杀荷兰、过加拿大 → 8强止步法国",
    "瑞士": "小组出线 → 过阿尔及利亚、点杀哥伦比亚 → 8强止步阿根廷",
}

PATH_HINT = {
    "决赛": "已晋级决赛",
    "半决赛": "闯入半决赛",
    "8强": "止步四分之一决赛",
    "16强": "止步十六强",
    "32强": "止步三十二强",
    "小组赛": "小组赛出局",
}

REELS = {
    "r32": [("32强精华 · 英格兰 3-2 墨西哥", "BV1BNTD64EYL"), ("法国淘汰瑞典", "BV138Te6KEPp")],
    "r16": [("16强精华 · 挪威爆冷巴西", "BV1WRTS6NENr"), ("阿根廷绝杀埃及", "BV18nMe6KEHv")],
    "qf": [("8强精华 · 英格兰逆转挪威", "BV1VdNK6oEZJ"), ("西班牙绝杀比利时", "BV1eDNp6NEGC")],
    "sf": [
        ("半决赛精华 · 西班牙淘汰法国", "BV11rNh6VEFK"),
        ("半决赛精华 · 阿根廷逆转英格兰", "BV119Nz6TEb6"),
    ],
    "final": [],
}


def clean(n: str) -> str:
    n = n.strip()
    if n in NAME_MAP:
        return NAME_MAP[n]
    n = n.replace(" 🟡", "").replace(" ❌", "").strip()
    return NAME_MAP.get(n, n)


def slug(s: str) -> str:
    h = hashlib.md5(s.encode()).hexdigest()[:8]
    base = re.sub(r"[^\w\u4e00-\u9fff]+", "-", s).strip("-")[:24]
    return f"{base}-{h}" if base else h


def http_json(url: str):
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"}
    )
    with urllib.request.urlopen(req, timeout=25) as r:
        return json.load(r)


def view(bv: str):
    d = http_json(f"https://api.bilibili.com/x/web-interface/view?bvid={bv}")["data"]
    return d["title"], d["pic"].replace("http://", "https://")


def fetch_bytes(url: str) -> bytes:
    req = urllib.request.Request(
        url, headers={"User-Agent": UA, "Referer": "https://www.bilibili.com/"}
    )
    return urllib.request.urlopen(req, timeout=30).read()


def load_font(size: int):
    for path in (
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/Hiragino Sans GB.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/Library/Fonts/Arial Unicode.ttf",
    ):
        try:
            return ImageFont.truetype(path, size, index=0)
        except Exception:
            continue
    return ImageFont.load_default()


def make_poster(src: Image.Image, team: str, title: str, match: str, out: Path):
    """Compose phone-wallpaper poster 1080x1920."""
    W, H = 1080, 1920
    c1, c2 = TEAM_COLORS.get(team, ((20, 40, 30), (180, 160, 60)))
    img = src.convert("RGB")

    # blurred full-bleed background
    bg = ImageEnhance.Brightness(img.resize((W, H), Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(28))).enhance(0.55)
    canvas = Image.new("RGB", (W, H), c1)
    canvas.paste(bg, (0, 0))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    od = ImageDraw.Draw(overlay)
    for y in range(H):
        a = int(40 + 140 * (y / H))
        od.line([(0, y), (W, y)], fill=(c1[0], c1[1], c1[2], a))
    canvas = Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")

    # hero photo with portrait crop
    target_h = 1280
    target_w = 900
    ratio = target_w / target_h
    iw, ih = img.size
    if iw / ih > ratio:
        nw = int(ih * ratio)
        left = (iw - nw) // 2
        hero = img.crop((left, 0, left + nw, ih))
    else:
        nh = int(iw / ratio)
        top = max(0, (ih - nh) // 5)
        hero = img.crop((0, top, iw, min(ih, top + nh)))
    hero = hero.resize((target_w, target_h), Image.Resampling.LANCZOS)
    # soft vignette frame
    hx = (W - target_w) // 2
    hy = 180
    canvas.paste(hero, (hx, hy))

    draw = ImageDraw.Draw(canvas)
    # accent bars
    draw.rectangle([0, 0, W, 14], fill=c2)
    draw.rectangle([0, H - 14, W, H], fill=c2)
    draw.rectangle([hx - 6, hy - 6, hx + target_w + 6, hy + target_h + 6], outline=c2, width=4)

    font_team = load_font(64)
    font_title = load_font(42)
    font_match = load_font(28)
    font_footer = load_font(22)

    flag = EMOJI.get(team, "")
    draw.text((72, 48), f"{flag} {team}", font=font_team, fill=(255, 255, 255))
    # title block under hero
    ty = hy + target_h + 36
    draw.text((72, ty), title[:18], font=font_title, fill=(245, 245, 240))
    draw.text((72, ty + 64), match[:28], font=font_match, fill=c2)
    draw.text((72, H - 80), "WORLD CUP 2026 · WALLPAPER", font=font_footer, fill=(200, 200, 200))

    out.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(out, "JPEG", quality=93, optimize=True)
    return out


def save_cover(url: str, path: Path, size=(1280, 720)):
    data = fetch_bytes(url)
    im = Image.open(io.BytesIO(data)).convert("RGB")
    im = im.resize(size, Image.Resampling.LANCZOS)
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path, "JPEG", quality=92, optimize=True)
    return im


def assert_unique_journeys():
    seen = {}
    for team, bv in JOURNEY_BV.items():
        if bv in seen:
            raise SystemExit(f"Duplicate BV {bv}: {seen[bv]} vs {team}")
        seen[bv] = team
    print(f"journey unique ok: {len(seen)}")


def main():
    assert_unique_journeys()
    with open(ROOT / "data.json") as f:
        data = json.load(f)

    farthest = {}
    for g in data["groups"]:
        for t in g["teams"]:
            farthest[clean(t["name"])] = "小组赛"

    for m in data["matches"]:
        g = m.get("g")
        if g in STAGE_SCORE:
            for side in ("a", "b"):
                team = clean(m[side])
                cur = farthest.get(team, "小组赛")
                if STAGE_SCORE[g] > STAGE_SCORE.get(cur, 100):
                    farthest[team] = g

    ko = data.get("knockout") or {}
    # 半决赛胜者晋级决赛（格子含比分、不含 vs）
    left_sf = str(ko.get("leftSF", ""))
    right_sf = str(ko.get("rightSF", ""))
    if "西班牙" in left_sf and "vs" not in left_sf:
        farthest["西班牙"] = "决赛"
    if "法国" in left_sf and "vs" not in left_sf and "西班牙" not in left_sf.split("vs")[0]:
        # leftSF 形如「🇪🇸 西班牙 2-0」→ 西班牙晋级
        pass
    if "阿根廷" in right_sf and "vs" not in right_sf:
        farthest["阿根廷"] = "决赛"
        farthest["英格兰"] = "半决赛"
    elif "英格兰" in right_sf and "vs" not in right_sf:
        farthest["英格兰"] = "决赛"
        farthest["阿根廷"] = "半决赛"
    elif "vs" in right_sf:
        for t in ("英格兰", "阿根廷"):
            if t in right_sf:
                farthest[t] = "半决赛"

    teams = sorted({clean(t["name"]) for g in data["groups"] for t in g["teams"]})

    def heat(team: str) -> int:
        return STAGE_SCORE.get(farthest.get(team, "小组赛"), 100) * 10 + POP.get(team, 5)

    ranked = sorted(teams, key=lambda t: (-heat(t), t))

    # --- moments / posters ---
    moments_by_country = []
    used_poster_src = set()
    for team in ranked:
        items = MOMENT_EXTRA.get(team, [])
        # also include journey bv as an extra poster source
        jbv = JOURNEY_BV.get(team)
        if jbv and not any(x[2] == jbv for x in items):
            items = items + [(f"{team} · 征程海报", farthest.get(team, "世界杯"), jbv)]
        photos = []
        for i, (title, match, bv) in enumerate(items):
            key = f"{team}-{bv}"
            if key in used_poster_src:
                continue
            try:
                _, pic = view(bv)
                raw = Image.open(io.BytesIO(fetch_bytes(pic))).convert("RGB")
                rel = f"media/moments/{slug(team)}-{i + 1}.jpg"
                make_poster(raw, team, title, match, ROOT / rel)
                photos.append({"title": title, "match": match, "cover": rel, "wallpaper": True})
                used_poster_src.add(key)
                print("poster", team, title)
                time.sleep(0.1)
            except Exception as e:
                print("poster fail", team, bv, e)
        if photos:
            moments_by_country.append(
                {"team": team, "flag": EMOJI.get(team, ""), "heat": heat(team), "photos": photos}
            )
    moments_by_country.sort(key=lambda x: -x["heat"])

    # --- journeys ---
    journeys = []
    for team in ranked:
        st = farthest.get(team, "小组赛")
        entry = {
            "team": team,
            "flag": EMOJI.get(team, ""),
            "status": st,
            "path": CUSTOM_PATH.get(team, PATH_HINT.get(st, st)),
            "heat": heat(team),
            "searchUrl": "https://search.bilibili.com/all?keyword="
            + urllib.parse.quote(f"{team} 世界杯2026"),
            "title": f"{team} · 世界杯征程",
        }
        bv = JOURNEY_BV.get(team)
        if bv:
            try:
                title, pic = view(bv)
                rel = f"media/journeys/{slug(team)}.jpg"
                save_cover(pic, ROOT / rel)
                entry["bilibiliId"] = bv
                entry["cover"] = rel
                entry["title"] = title[:48]
                print("journey", team, bv)
                time.sleep(0.1)
            except Exception as e:
                print("journey fail", team, e)
        journeys.append(entry)

    # --- stage reels with covers ---
    stages = []
    for sid, title in [
        ("r32", "32强"),
        ("r16", "16强"),
        ("qf", "8强"),
        ("sf", "半决赛"),
        ("final", "决赛"),
    ]:
        reels = []
        for i, (rtitle, bv) in enumerate(REELS.get(sid) or []):
            try:
                _, pic = view(bv)
                rel = f"media/reels/{sid}-{i + 1}.jpg"
                save_cover(pic, ROOT / rel)
                reels.append({"title": rtitle, "bilibiliId": bv, "cover": rel})
                print("reel", sid, rtitle)
                time.sleep(0.1)
            except Exception as e:
                print("reel fail", sid, bv, e)
                reels.append({"title": rtitle, "bilibiliId": bv})
        stages.append({"id": sid, "title": title, "reels": reels})

    # Preserve cinematic wallpapers / 球星风采 (v3/v4/clean/star) — never overwrite
    preserved_moments = (data.get("highlights") or {}).get("momentsByCountry")
    preserved_stars = (data.get("highlights") or {}).get("stars")
    if preserved_moments and any(
        (p.get("cover") or "").startswith(("media/moments/clean-", "media/moments/v3-", "media/moments/v4-", "media/moments/cine-"))
        or p.get("star")
        for c in preserved_moments
        for p in (c.get("photos") or [])
    ):
        moments_by_country = preserved_moments
        print("preserved star/cinematic moments", len(moments_by_country))

    data["highlights"] = {
        "momentsByCountry": moments_by_country,
        "stages": stages,
        "journeys": journeys,
    }
    if preserved_stars:
        data["highlights"]["stars"] = preserved_stars
        print("preserved stars gallery", len(preserved_stars))
    data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    with open(ROOT / "data.json", "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        f.write("\n")

    print("---")
    print("poster countries", len(moments_by_country), "photos", sum(len(c["photos"]) for c in moments_by_country))
    print("journeys", len(journeys), "withVideo", sum(1 for j in journeys if j.get("bilibiliId")))
    bvs = [j["bilibiliId"] for j in journeys if j.get("bilibiliId")]
    print("unique BVs", len(bvs), "set", len(set(bvs)))
    print("stages", [(s["id"], len(s["reels"])) for s in stages])
    print("updated", data["updatedAt"])


if __name__ == "__main__":
    main()
