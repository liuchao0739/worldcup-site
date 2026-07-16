#!/usr/bin/env python3
"""Build native desktop cinematic 16:9 images (not center-crops) + wire data."""
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone
from PIL import Image, ImageEnhance, ImageFilter, ImageDraw

ROOT = Path("/Users/liuchao/worldcup-site/site")
OUT = ROOT / "media/moments"
ASSETS = Path("/Users/liuchao/.cursor/projects/Users-liuchao/assets")
OUT.mkdir(parents=True, exist_ok=True)

# Dedicated native landscape cinematics -> assign to titles
CINE_MAP = {
    ("西班牙", "亚马尔之夜"): "cine-spain-yamal-wide.png",
    ("西班牙", "佩德里掌控"): "cine-spain-pedri-wide.png",
    ("西班牙", "尼科·威廉姆斯"): "cine-spain-nico-wide.png",
    ("西班牙", "通道尽头"): "cine-spain-tunnel-wide.png",
    ("西班牙", "赤色宣言"): "cine-spain-yamal-wide.png",
    ("西班牙", "雨夜破晓"): "cine-spain-pedri-wide.png",
    ("西班牙", "日暮门神"): "cine-spain-tunnel-wide.png",
    ("西班牙", "相拥成碑"): "cine-spain-nico-wide.png",
    ("西班牙", "红黄雾境"): "cine-spain-tunnel-wide.png",
    ("阿根廷", "雨中成团"): "cine-argentina-huddle-wide.png",
    ("阿根廷", "天青礼花"): "cine-argentina-huddle-wide.png",
    ("阿根廷", "梅西队长"): "cine-argentina-captain-wide.png",
    ("阿根廷", "蓝白条纹"): "cine-argentina-captain-wide.png",
    ("阿根廷", "臂章遗落"): "cine-argentina-captain-wide.png",
    ("阿根廷", "条纹呼吸"): "cine-argentina-huddle-wide.png",
    ("阿根廷", "恩佐·费尔南德斯"): "cine-argentina-huddle-wide.png",
    ("法国", "疾风蓝影"): "cine-france-sprint-wide.png",
    ("法国", "姆巴佩冲刺"): "cine-france-sprint-wide.png",
    ("法国", "门线闪电"): "cine-france-sprint-wide.png",
    ("法国", "赛前露珠"): "cine-france-sprint-wide.png",
    ("法国", "格列兹曼回望"): "cine-france-sprint-wide.png",
    ("英格兰", "白衣仰光"): "cine-england-raise-wide.png",
    ("英格兰", "隧道心跳"): "cine-england-raise-wide.png",
    ("英格兰", "贝林厄姆"): "cine-england-raise-wide.png",
    ("英格兰", "萨卡突破"): "cine-england-raise-wide.png",
    ("英格兰", "凯恩领军"): "cine-england-raise-wide.png",
    ("挪威", "峡湾怒吼"): "cine-norway-myth-wide.png",
    ("挪威", "红影神话"): "cine-norway-myth-wide.png",
    ("挪威", "哈兰德压迫"): "cine-norway-myth-wide.png",
    ("巴西", "金黄落幕"): "cine-brazil-kneel-wide.png",
    ("巴西", "维尼修斯"): "cine-brazil-kneel-wide.png",
    ("巴西", "内马尔旧影"): "cine-brazil-kneel-wide.png",
    ("葡萄牙", "红衣升空"): "cine-portugal-leap-wide.png",
    ("葡萄牙", "C罗远征"): "cine-portugal-leap-wide.png",
    ("葡萄牙", "B费调度"): "cine-portugal-leap-wide.png",
    ("摩洛哥", "北非狂想"): "cine-morocco-wide.png",
    ("摩洛哥", "哈基米"): "cine-morocco-wide.png",
}


def export_cine(src: Path, dst: Path):
    im = Image.open(src).convert("RGB")
    W, H = 1920, 1080
    scale = max(W / im.width, H / im.height)
    nw, nh = int(im.width * scale + 0.5), int(im.height * scale + 0.5)
    im = im.resize((nw, nh), Image.Resampling.LANCZOS)
    left, top = (nw - W) // 2, (nh - H) // 2
    im = im.crop((left, top, left + W, top + H))
    im = ImageEnhance.Contrast(im).enhance(1.06)
    im = ImageEnhance.Color(im).enhance(1.04)
    dst.parent.mkdir(parents=True, exist_ok=True)
    im.save(dst, "JPEG", quality=92, optimize=True, progressive=True)


def make_desktop_poster(src: Path, dst: Path):
    """Different desktop image: blurred 16:9 ambience + full uncropped portrait panel."""
    src_im = Image.open(src).convert("RGB")
    W, H = 1920, 1080

    # background: cover-fill + heavy blur + darken
    bg = src_im.copy()
    scale = max(W / bg.width, H / bg.height)
    nw, nh = int(bg.width * scale + 0.5), int(bg.height * scale + 0.5)
    bg = bg.resize((nw, nh), Image.Resampling.LANCZOS)
    bg = bg.crop(((nw - W) // 2, (nh - H) // 2, (nw - W) // 2 + W, (nh - H) // 2 + H))
    bg = bg.filter(ImageFilter.GaussianBlur(36))
    bg = ImageEnhance.Brightness(bg).enhance(0.42)
    bg = ImageEnhance.Color(bg).enhance(0.85)

    # foreground portrait: fit full height, keep full head-to-toe / full face
    panel_h = int(H * 0.92)
    panel_w = int(src_im.width * (panel_h / src_im.height))
    # limit width so it feels cinematic panel (~38% of frame)
    max_w = int(W * 0.42)
    if panel_w > max_w:
        panel_w = max_w
        panel_h = int(src_im.height * (panel_w / src_im.width))
    fg = src_im.resize((panel_w, panel_h), Image.Resampling.LANCZOS)
    fg = ImageEnhance.Contrast(fg).enhance(1.08)
    fg = ImageEnhance.Sharpness(fg).enhance(1.12)

    canvas = bg.copy()
    # slight left offset for storytelling
    x = int(W * 0.10)
    y = (H - panel_h) // 2
    # soft shadow plate
    shadow = Image.new("RGBA", (panel_w + 40, panel_h + 40), (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([0, 0, panel_w + 39, panel_h + 39], radius=18, fill=(0, 0, 0, 120))
    shadow = shadow.filter(ImageFilter.GaussianBlur(18))
    canvas_rgba = canvas.convert("RGBA")
    canvas_rgba.alpha_composite(shadow, (x - 12, y - 8))
    canvas_rgba.paste(fg, (x, y))
    # thin gold edge
    edge = ImageDraw.Draw(canvas_rgba)
    edge.rectangle([x - 2, y - 2, x + panel_w + 1, y + panel_h + 1], outline=(212, 175, 55, 160), width=2)
    out = canvas_rgba.convert("RGB")
    out.save(dst, "JPEG", quality=92, optimize=True, progressive=True)


def main():
    data = json.loads((ROOT / "data.json").read_text())
    moments = data["highlights"]["momentsByCountry"]

    # export dedicated cine files once
    cine_files = {}
    for asset in set(CINE_MAP.values()):
        src = ASSETS / asset
        if not src.exists():
            print("missing cine", asset)
            continue
        key = hashlib.md5(asset.encode()).hexdigest()[:10]
        dst = OUT / f"cine-desk-{key}.jpg"
        if not dst.exists() or dst.stat().st_size < 20000:
            export_cine(src, dst)
        cine_files[asset] = f"media/moments/{dst.name}"
        print("cine", asset, "->", dst.name)

    updated = 0
    for country in moments:
        team = country["team"]
        for photo in country.get("photos") or []:
            title = photo.get("title") or ""
            cover = photo.get("cover") or ""
            cover_path = ROOT / cover

            # Prefer dedicated cinematic landscape when mapped
            mapped = CINE_MAP.get((team, title))
            if mapped and mapped in cine_files:
                photo["coverDesktop"] = cine_files[mapped]
                # drop bad center-crop wide
                photo.pop("coverWide", None)
                updated += 1
                continue

            # Otherwise build a different desktop poster (blur ambience + full portrait panel)
            if cover and cover_path.exists():
                key = hashlib.md5((team + title + cover).encode()).hexdigest()[:10]
                desk_name = f"desk-poster-{key}.jpg"
                desk_path = OUT / desk_name
                if not desk_path.exists() or desk_path.stat().st_size < 20000:
                    try:
                        make_desktop_poster(cover_path, desk_path)
                        print("poster", team, title)
                    except Exception as e:
                        print("poster fail", team, title, e)
                        continue
                photo["coverDesktop"] = f"media/moments/{desk_name}"
                photo.pop("coverWide", None)
                updated += 1
            else:
                photo.pop("coverWide", None)

    data["highlights"]["momentsByCountry"] = moments
    data["updatedAt"] = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
    (ROOT / "data.json").write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n")
    print("updated photos", updated)
    # stats
    n = sum(1 for c in moments for p in c["photos"] if p.get("coverDesktop"))
    print("with coverDesktop", n)


if __name__ == "__main__":
    main()
