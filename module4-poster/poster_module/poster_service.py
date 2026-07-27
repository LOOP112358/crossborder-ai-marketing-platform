from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
from typing import Optional
import re
import uuid

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
POSTER_DIR = STATIC_DIR / "posters"
POSTER_DIR.mkdir(parents=True, exist_ok=True)


FONT_MAP = {
    "msyh": "C:/Windows/Fonts/msyh.ttc",
    "simhei": "C:/Windows/Fonts/simhei.ttf",
    "simsun": "C:/Windows/Fonts/simsun.ttc",
    "kaiti": "C:/Windows/Fonts/simkai.ttf",
    "arial": "C:/Windows/Fonts/arial.ttf",
    "impact": "C:/Windows/Fonts/impact.ttf",
}


def load_font(size: int, font_name: str = "msyh"):
    font_path = FONT_MAP.get(font_name)

    if font_path and Path(font_path).exists():
        return ImageFont.truetype(font_path, size)

    fallback_paths = [
        "C:/Windows/Fonts/msyh.ttc",
        "C:/Windows/Fonts/simhei.ttf",
        "C:/Windows/Fonts/arial.ttf",
    ]

    for path in fallback_paths:
        if Path(path).exists():
            return ImageFont.truetype(path, size)

    return ImageFont.load_default()


def url_to_path(url: str) -> Path:
    """把 /static/... URL 解析为本地文件路径（兼容仓库根 static 与 ABO 挂载）。"""
    raw = (url or "").strip()
    if not raw:
        return Path("")

    as_path = Path(raw)
    if as_path.is_file():
        return as_path

    # /static/abo-images/... → ABO 本地图片目录
    if raw.startswith("/static/abo-images/"):
        rel = raw[len("/static/abo-images/") :].lstrip("/").replace("\\", "/")
        candidates = []
        try:
            from app.modules.chat.services.config import ABO_IMAGES_DIR

            candidates.append(ABO_IMAGES_DIR / rel)
        except Exception:
            pass
        candidates.append(Path(r"C:\Users\lishu\Downloads\abo-images-small") / rel)
        for cand in candidates:
            if cand.is_file():
                return cand
        return candidates[0] if candidates else Path(rel)

    if raw.startswith("/static/"):
        relative = raw[len("/static/") :].lstrip("/").replace("\\", "/")
        # 仓库根 static（上传接口写这里）优先
        repo_static = BASE_DIR.parent.parent / "static"
        candidates = [
            STATIC_DIR / relative,
            repo_static / relative,
            BASE_DIR / "static" / relative,
            BASE_DIR.parent / "static" / relative,
        ]
        # 去重保序
        seen = set()
        uniq = []
        for c in candidates:
            key = str(c.resolve()) if c.parent.exists() else str(c)
            if key not in seen:
                seen.add(key)
                uniq.append(c)
        for cand in uniq:
            if cand.is_file():
                return cand
        return STATIC_DIR / relative

    return as_path



def draw_text_with_art_style(
    draw,
    text: str,
    x: int,
    y: int,
    font,
    fill: str,
    art_style: str = "stroke_shadow",
    stroke_enabled: bool = True,
    stroke_color: str = "#FFFFFF",
    stroke_width: int = 2,
    shadow_enabled: bool = True
):
    if not text:
        return

    art_style = art_style or "normal"

    use_stroke = False
    use_shadow = False

    if art_style == "normal":
        use_stroke = False
        use_shadow = False

    elif art_style == "stroke":
        use_stroke = True
        use_shadow = False

    elif art_style == "shadow":
        use_stroke = False
        use_shadow = True

    elif art_style == "stroke_shadow":
        use_stroke = True
        use_shadow = True

    elif art_style == "glow":
        use_stroke = True
        use_shadow = True

    elif art_style == "strong":
        use_stroke = True
        use_shadow = False

    if not stroke_enabled:
        use_stroke = False

    if not shadow_enabled:
        use_shadow = False

    if use_shadow:
        draw.text(
            (x + 4, y + 4),
            text,
            fill=(0, 0, 0, 120),
            font=font
        )

    if art_style == "glow":
        for offset in [8, 5, 3]:
            draw.text(
                (x, y),
                text,
                fill=fill,
                font=font,
                stroke_width=offset,
                stroke_fill=stroke_color
            )

    if art_style == "strong":
        offsets = [
            (0, 0), (1, 0), (0, 1), (1, 1),
            (-1, 0), (0, -1)
        ]

        for dx, dy in offsets:
            draw.text(
                (x + dx, y + dy),
                text,
                fill=fill,
                font=font,
                stroke_width=stroke_width if use_stroke else 0,
                stroke_fill=stroke_color
            )

        return

    draw.text(
        (x, y),
        text,
        fill=fill,
        font=font,
        stroke_width=stroke_width if use_stroke else 0,
        stroke_fill=stroke_color
    )


def draw_cta_button(
    draw,
    text: str,
    x: int,
    y: int,
    font,
    text_color: str,
    button_color: str,
    art_style: str = "normal"
):
    if not text:
        return

    text_bbox = draw.textbbox((0, 0), text, font=font)
    text_w = text_bbox[2] - text_bbox[0]
    text_h = text_bbox[3] - text_bbox[1]

    padding_x = 34
    padding_y = 18

    button_w = text_w + padding_x * 2
    button_h = text_h + padding_y * 2

    if art_style in ["shadow", "stroke_shadow", "glow"]:
        draw.rounded_rectangle(
            (x + 5, y + 5, x + button_w + 5, y + button_h + 5),
            radius=26,
            fill=(0, 0, 0, 90)
        )

    draw.rounded_rectangle(
        (x, y, x + button_w, y + button_h),
        radius=26,
        fill=button_color
    )

    draw.text(
        (x + padding_x, y + padding_y - 4),
        text,
        fill=text_color,
        font=font
    )


def get_default_layer_config(canvas_w: int, canvas_h: int):
    return {
        "title": {
            "x": 80,
            "y": 80,
            "font_size": 64,
            "color": "#111111",
            "font_name": "msyh",
            "art_style": "stroke_shadow"
        },
        "subtitle": {
            "x": 80,
            "y": 165,
            "font_size": 42,
            "color": "#D81B60",
            "font_name": "msyh",
            "art_style": "stroke_shadow"
        },
        "selling_point_1": {
            "x": 80,
            "y": 240,
            "font_size": 34,
            "color": "#111111",
            "font_name": "msyh",
            "art_style": "shadow"
        },
        "selling_point_2": {
            "x": 80,
            "y": 295,
            "font_size": 34,
            "color": "#111111",
            "font_name": "msyh",
            "art_style": "shadow"
        },
        "cta_text": {
            "x": 80,
            "y": canvas_h - 170,
            "font_size": 42,
            "color": "#FFFFFF",
            "font_name": "msyh",
            "art_style": "normal",
            "button_color": "#111111"
        }
    }



def fit_rgba(image: Image.Image, box_w: int, box_h: int) -> Image.Image:
    """等比缩放放入框内，透明填充，避免拉伸变形。"""
    img = image.convert("RGBA")
    iw, ih = img.size
    if iw <= 0 or ih <= 0:
        return Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    scale = min(box_w / iw, box_h / ih)
    nw, nh = max(1, int(iw * scale)), max(1, int(ih * scale))
    resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (box_w, box_h), (0, 0, 0, 0))
    canvas.paste(resized, ((box_w - nw) // 2, (box_h - nh) // 2), resized)
    return canvas


def paste_product_with_shadow(
    canvas: Image.Image,
    product: Image.Image,
    x: int,
    y: int,
    shadow: bool = True,
) -> None:
    # 轻微羽化 alpha，减轻白边/锯齿
    product = product.convert("RGBA")
    r, g, b, a = product.split()
    a = a.filter(ImageFilter.GaussianBlur(0.8))
    product = Image.merge("RGBA", (r, g, b, a))

    if shadow:
        alpha = product.split()[-1]
        shadow_layer = Image.new("RGBA", product.size, (0, 0, 0, 0))
        shadow_layer.putalpha(alpha.point(lambda v: int(v * 0.42)))
        shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(18))
        canvas.alpha_composite(shadow_layer, (x + 14, y + 22))
        # 更贴地的淡接触阴影
        contact = Image.new("RGBA", product.size, (0, 0, 0, 0))
        contact.putalpha(alpha.point(lambda v: int(v * 0.18)))
        contact = contact.filter(ImageFilter.GaussianBlur(6))
        canvas.alpha_composite(contact, (x + 4, y + product.size[1] // 12))
    canvas.alpha_composite(product, (x, y))


def sanitize_poster_text(text: str) -> str:
    """去掉字体常缺字形（emoji/特殊符号），避免方框乱码。"""
    if not text:
        return ""
    out = []
    for ch in str(text):
        o = ord(ch)
        if ch in " ··-–—&/|%+.,:;!?()[]【】「」《》°×÷•…":
            out.append(ch)
            continue
        if (
            ("0" <= ch <= "9")
            or ("a" <= ch <= "z")
            or ("A" <= ch <= "Z")
            or ("\u4e00" <= ch <= "\u9fff")
            or ("\u3400" <= ch <= "\u4dbf")
        ):
            out.append(ch)
            continue
        if o < 32 or (0x2000 <= o <= 0x2BFF) or (0x1F000 <= o <= 0x1FFFF) or (0xFE00 <= o <= 0xFE0F):
            continue
        if o <= 0xFFFF and not (0xE000 <= o <= 0xF8FF):
            out.append(ch)
    return re.sub(r"\s+", " ", "".join(out)).strip()


def ellipsize_to_width(draw, text: str, font, max_width: int) -> str:
    text = sanitize_poster_text(text)
    if not text:
        return ""

    def _w(s: str) -> int:
        b = draw.textbbox((0, 0), s, font=font)
        return b[2] - b[0]

    if _w(text) <= max_width:
        return text
    ell = "…"
    while text and _w(text + ell) > max_width:
        text = text[:-1]
    return (text + ell) if text else ell


def wrap_text_lines(draw, text: str, font, max_width: int, max_lines: int = 3, allow_truncate: bool = True) -> list:
    """按像素宽度换行；默认尽量排完，必要时再省略。"""
    text = sanitize_poster_text(text)
    if not text or max_width <= 0:
        return [text] if text else []

    def _width(s: str) -> int:
        box = draw.textbbox((0, 0), s, font=font)
        return box[2] - box[0]

    has_cjk = any("\u4e00" <= ch <= "\u9fff" for ch in text)
    use_words = (" " in text) and (not has_cjk)
    units = text.split() if use_words else list(text)
    sep = " " if use_words else ""

    lines, cur = [], ""
    for piece in units:
        trial = piece if not cur else f"{cur}{sep}{piece}"
        if _width(trial) <= max_width or not cur:
            if not cur and _width(piece) > max_width:
                for ch in piece:
                    t2 = cur + ch
                    if _width(t2) <= max_width or not cur:
                        cur = t2
                    else:
                        lines.append(cur)
                        cur = ch
            else:
                cur = trial
        else:
            lines.append(cur)
            cur = piece
            # 新行单词仍超宽：按字符切开
            if _width(cur) > max_width:
                buf = ""
                for ch in cur:
                    t2 = buf + ch
                    if _width(t2) <= max_width or not buf:
                        buf = t2
                    else:
                        lines.append(buf)
                        buf = ch
                cur = buf
    if cur:
        lines.append(cur)

    if not lines:
        return [text]

    if len(lines) <= max_lines:
        return [ln for ln in lines if ln]

    if not allow_truncate:
        # 调用方应先缩小字号；这里仍返回前 max_lines 但不加省略，避免「半词+…」
        return lines[:max_lines]

    kept = lines[:max_lines]
    kept = [ellipsize_to_width(draw, ln, font, max_width) for ln in kept]
    # 有剩余内容才在末行加省略
    if len(lines) > max_lines and kept:
        base = kept[-1].rstrip("…")
        kept[-1] = ellipsize_to_width(draw, base + "…", font, max_width)
    return kept


def fit_wrapped_text(draw, text: str, font_name: str, prefer_size: int, max_width: int, max_lines: int = 3, min_size: int = 18):
    """缩小字号直到全文可在 max_lines 内排下（尽量不省略）。"""
    text = sanitize_poster_text(text)
    size = prefer_size
    font = load_font(size, font_name)
    while size >= min_size:
        lines = wrap_text_lines(draw, text, font, max_width, max_lines=max_lines, allow_truncate=False)
        covered = "".join(lines).replace(" ", "")
        raw = text.replace(" ", "")
        # 行数超限或内容盖不全 → 继续缩小
        trial = wrap_text_lines(draw, text, font, max_width, max_lines=99, allow_truncate=False)
        if len(trial) <= max_lines:
            widest = max((draw.textbbox((0, 0), ln, font=font)[2] - draw.textbbox((0, 0), ln, font=font)[0]) for ln in trial) if trial else 0
            if widest <= max_width:
                return font, size, trial
        size -= 2
        font = load_font(size, font_name)
    # 最后兜底：允许省略
    font = load_font(min_size, font_name)
    lines = wrap_text_lines(draw, text, font, max_width, max_lines=max_lines, allow_truncate=True)
    return font, min_size, lines


def text_safe_zone(canvas_w: int, canvas_h: int, template_config: dict) -> dict:
    overlays = template_config.get("overlays") or []
    layout = template_config.get("layout_mode") or "stack"
    pad = int(min(canvas_w, canvas_h) * 0.06)
    zone = {
        "x": pad,
        "y": pad,
        "w": int(canvas_w * 0.52),
        "h": int(canvas_h * 0.42),
        "cta_y": canvas_h - pad - 90,
        "align": "left",
        "on_panel": False,
        "panel_light": False,
        "layout": layout,
    }
    for ov in overlays:
        kind = ov.get("type")
        color = ov.get("color") or [0, 0, 0, 120]
        alpha = color[3] if len(color) > 3 else 120
        rgb = color[:3]
        lum = (0.299 * rgb[0] + 0.587 * rgb[1] + 0.114 * rgb[2]) if rgb else 128
        if kind in ("left_panel", "left_fade", "soft_card"):
            ratio = float(ov.get("ratio", 0.42))
            zone.update({
                "x": pad,
                "y": int(canvas_h * 0.08),
                "w": int(canvas_w * ratio) - pad * 2,
                "h": int(canvas_h * 0.72),
                "cta_y": canvas_h - pad - 100,
                "on_panel": True,
                "panel_light": lum > 150 or kind in ("left_fade", "soft_card"),
            })
        elif kind in ("top_band", "top_fade"):
            ratio = float(ov.get("ratio", 0.28))
            zone.update({
                "x": pad,
                "y": int(pad * 0.7),
                "w": canvas_w - pad * 2,
                "h": int(canvas_h * ratio) - pad,
                "cta_y": int(canvas_h * ratio) - pad - 70,
                "on_panel": True,
                "panel_light": lum > 160 and alpha >= 140,
            })
        elif kind in ("bottom_band", "bottom_fade"):
            ratio = float(ov.get("ratio", 0.28))
            band_h = int(canvas_h * ratio)
            zone.update({
                "x": pad,
                "y": canvas_h - band_h + int(pad * 0.7),
                "w": canvas_w - pad * 2,
                "h": band_h - pad,
                "cta_y": canvas_h - pad - 80,
                "on_panel": True,
                "panel_light": lum > 160 and alpha >= 140,
            })
    purpose = str(template_config.get("purpose") or "")
    if "白底" in purpose or "Amazon" in purpose:
        zone.update({
            "x": pad,
            "y": int(canvas_h * 0.78),
            "w": int(canvas_w * 0.62),
            "h": int(canvas_h * 0.18),
            "cta_y": int(canvas_h * 0.86),
            "on_panel": True,
            "panel_light": True,
        })
    if layout == "lifestyle":
        zone.update({
            "x": pad,
            "y": int(canvas_h * 0.07),
            "w": int(canvas_w * 0.56),
            "h": int(canvas_h * 0.62),
            "cta_y": canvas_h - pad - 88,
            "panel_light": True,
        })
    elif layout == "premium_dark":
        zone.update({
            "x": pad,
            "y": int(canvas_h * 0.06),
            "w": canvas_w - pad * 2,
            "h": int(canvas_h * 0.28),
            "cta_y": canvas_h - pad - 70,
            "panel_light": False,
        })
    zone["w"] = max(160, zone["w"])
    zone["h"] = max(80, zone["h"])
    return zone


def region_luminance(image: Image.Image, x: int, y: int, w: int, h: int) -> float:
    rgb = image.convert("RGB")
    W, H = rgb.size
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(W, x + max(1, w)), min(H, y + max(1, h))
    if x1 <= x0 or y1 <= y0:
        return 128.0
    crop = rgb.crop((x0, y0, x1, y1)).resize((24, 24), Image.Resampling.BILINEAR)
    pixels = list(crop.getdata())
    if not pixels:
        return 128.0
    return sum(0.299 * r + 0.587 * g + 0.114 * b for r, g, b in pixels) / len(pixels)


def draw_multiline_art(
    draw, lines, x, y, font, fill, art_style, line_gap,
    stroke_enabled, stroke_color, stroke_width, shadow_enabled,
) -> int:
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + line_gap
    cy = y
    for line in lines:
        draw_text_with_art_style(
            draw=draw, text=line, x=x, y=cy, font=font, fill=fill,
            art_style=art_style, stroke_enabled=stroke_enabled,
            stroke_color=stroke_color, stroke_width=stroke_width,
            shadow_enabled=shadow_enabled,
        )
        cy += line_h
    return cy


def draw_accent_line(draw, x: int, y: int, width: int, color: str = "#5B7C6E") -> None:
    draw.rectangle((x, y, x + width, y + 4), fill=color)


def draw_subtitle_pill(draw, text: str, x: int, y: int, font, fill="#FFFFFF", bg="#3A3A3A", max_width: int = 0) -> int:
    text = sanitize_poster_text(text)
    if not text:
        return y
    pad_x, pad_y = 22, 10
    if max_width and max_width > 80:
        lines = wrap_text_lines(draw, text, font, max_width - pad_x * 2, max_lines=2, allow_truncate=False)
        trial = wrap_text_lines(draw, text, font, max_width - pad_x * 2, max_lines=99, allow_truncate=False)
        if len(trial) > 2:
            lines = wrap_text_lines(draw, text, font, max_width - pad_x * 2, max_lines=2, allow_truncate=True)
    else:
        lines = [text]
    ascent, descent = font.getmetrics()
    line_h = ascent + descent + 4
    max_tw = 0
    for ln in lines:
        bb = draw.textbbox((0, 0), ln, font=font)
        max_tw = max(max_tw, bb[2] - bb[0])
    bw = min(max_width, max_tw + pad_x * 2) if max_width else (max_tw + pad_x * 2)
    bh = line_h * len(lines) + pad_y * 2 - 4
    draw.rounded_rectangle((x, y, x + bw, y + bh), radius=max(12, min(bh // 2, 28)), fill=bg)
    ty = y + pad_y - 2
    for ln in lines:
        draw.text((x + pad_x, ty), ln, fill=fill, font=font)
        ty += line_h
    return y + bh + 18


def draw_feature_chips(
    draw, chips, x, y, font, max_width,
    text_color="#243038", border_color="#243038", fill_color=None,
) -> int:
    """卖点标签：短句用芯片；长句自动改为多行完整文本，避免省略号裁切。"""
    chips = [sanitize_poster_text(c) for c in chips if sanitize_poster_text(c)]
    if not chips:
        return y
    cy = y
    gap = 12
    for label in chips:
        # 长文案：完整换行展示（带左侧小条）
        bbox0 = draw.textbbox((0, 0), label, font=font)
        tw0 = bbox0[2] - bbox0[0]
        if tw0 + 36 > max_width or len(label) > 18:
            lines = wrap_text_lines(draw, label, font, max_width - 28, max_lines=3, allow_truncate=False)
            # 若仍超行，缩小字号再排
            f = font
            if len(wrap_text_lines(draw, label, font, max_width - 28, max_lines=99, allow_truncate=False)) > 3:
                # 无法拿 font size，用多行截断但不加奇怪半词：交给 fit 更稳
                lines = wrap_text_lines(draw, label, font, max_width - 28, max_lines=3, allow_truncate=True)
            ascent, descent = f.getmetrics()
            line_h = ascent + descent + 4
            block_h = line_h * len(lines) + 16
            if fill_color:
                draw.rounded_rectangle((x, cy, x + max_width, cy + block_h), radius=12, fill=fill_color)
            draw.rounded_rectangle((x, cy, x + max_width, cy + block_h), radius=12, outline=border_color, width=2)
            draw.rectangle((x + 10, cy + 12, x + 14, cy + block_h - 12), fill=border_color)
            ty = cy + 8
            for ln in lines:
                draw.text((x + 24, ty), ln, fill=text_color, font=f)
                ty += line_h
            cy += block_h + gap
            continue

        pad_x, pad_y = 16, 8
        bbox = draw.textbbox((0, 0), label, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        bw, bh = tw + pad_x * 2, th + pad_y * 2
        if fill_color:
            draw.rounded_rectangle((x, cy, x + bw, cy + bh), radius=10, fill=fill_color)
        draw.rounded_rectangle((x, cy, x + bw, cy + bh), radius=10, outline=border_color, width=2)
        draw.text((x + pad_x, cy + pad_y - 2), label, fill=text_color, font=font)
        cy += bh + gap
    return cy


def _gradient_horizontal(w: int, h: int, color) -> Image.Image:
    r, g, b = color[:3]
    a0 = color[3] if len(color) > 3 else 140
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = layer.load()
    for x in range(w):
        t = x / max(1, w - 1)
        a = a0 if t < 0.55 else int(a0 * (1 - (t - 0.55) / 0.45))
        for y in range(h):
            px[x, y] = (r, g, b, max(0, a))
    return layer


def _gradient_vertical(w: int, h: int, color, from_top: bool = True) -> Image.Image:
    r, g, b = color[:3]
    a0 = color[3] if len(color) > 3 else 140
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    px = layer.load()
    for y in range(h):
        t = y / max(1, h - 1)
        a = int(a0 * (1 - t * 0.85)) if from_top else int(a0 * (0.15 + t * 0.85))
        for x in range(w):
            px[x, y] = (r, g, b, max(0, min(255, a)))
    return layer


def apply_template_overlays(canvas: Image.Image, overlays: list) -> Image.Image:
    if not overlays:
        return canvas
    out = canvas.convert("RGBA")
    w, h = out.size
    for ov in overlays:
        kind = ov.get("type", "rect")
        color = ov.get("color", [0, 0, 0, 90])
        if len(color) == 3:
            color = list(color) + [120]
        color = tuple(int(c) for c in color)
        if kind == "top_band":
            band_h = int(h * float(ov.get("ratio", 0.28)))
            out.alpha_composite(Image.new("RGBA", (w, band_h), color), (0, 0))
        elif kind == "bottom_band":
            band_h = int(h * float(ov.get("ratio", 0.22)))
            out.alpha_composite(Image.new("RGBA", (w, band_h), color), (0, h - band_h))
        elif kind == "left_panel":
            panel_w = int(w * float(ov.get("ratio", 0.42)))
            out.alpha_composite(Image.new("RGBA", (panel_w, h), color), (0, 0))
        elif kind == "left_fade":
            panel_w = int(w * float(ov.get("ratio", 0.5)))
            out.alpha_composite(_gradient_horizontal(panel_w, h, color), (0, 0))
        elif kind == "top_fade":
            band_h = int(h * float(ov.get("ratio", 0.32)))
            out.alpha_composite(_gradient_vertical(w, band_h, color, True), (0, 0))
        elif kind == "bottom_fade":
            band_h = int(h * float(ov.get("ratio", 0.28)))
            out.alpha_composite(_gradient_vertical(w, band_h, color, False), (0, h - band_h))
        elif kind == "soft_card":
            ratio = float(ov.get("ratio", 0.42))
            card_w = int(w * ratio)
            card_h = int(h * float(ov.get("height_ratio", 0.55)))
            x0 = int(ov.get("x", int(w * 0.045)))
            y0 = int(ov.get("y", int(h * 0.06)))
            card = Image.new("RGBA", (card_w, card_h), (0, 0, 0, 0))
            ImageDraw.Draw(card).rounded_rectangle((0, 0, card_w - 1, card_h - 1), radius=28, fill=color)
            out.alpha_composite(card, (x0, y0))
        elif kind == "vignette":
            vignette = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            d = ImageDraw.Draw(vignette)
            edge = int(min(w, h) * 0.08)
            for i in range(edge):
                a = int(70 * (1 - i / edge))
                d.rectangle([i, i, w - 1 - i, h - 1 - i], outline=(0, 0, 0, a))
            out = Image.alpha_composite(out, vignette)
        elif kind == "frame":
            inset = int(ov.get("inset", 28))
            ImageDraw.Draw(out).rectangle(
                [inset, inset, w - inset, h - inset],
                outline=(color[0], color[1], color[2], 180),
                width=2,
            )
        elif kind == "rect":
            x = int(ov.get("x", 0))
            y = int(ov.get("y", 0))
            rw = int(ov.get("w", w))
            rh = int(ov.get("h", 120))
            out.alpha_composite(Image.new("RGBA", (rw, rh), color), (x, y))
    return out


def compose_poster(
    matted_url: str,
    bg_url: str,
    template_config: dict,
    title: str = "",
    discount: str = "",
    price: str = "",
    style_options: Optional[dict] = None,
):
    config = template_config
    style_options = style_options or {}
    sd_refine = bool(style_options.get("sd_refine"))  # 兼容旧字段：开启精修
    refine_enabled = bool(style_options.get("refine_enabled", sd_refine))
    refine_engine = str(style_options.get("refine_engine") or "seedream").strip().lower()
    refine_strength = float(style_options.get("sd_refine_strength", 0.28))
    product_hint = str(style_options.get("product_hint") or "")
    layout_mode = config.get("layout_mode") or "stack"

    canvas_w = config["canvas"]["width"]
    canvas_h = config["canvas"]["height"]

    bg_path = url_to_path(bg_url)
    product_path = url_to_path(matted_url)
    if not bg_path.exists():
        raise FileNotFoundError(f"背景图不存在：{bg_path}")
    if not product_path.exists():
        raise FileNotFoundError(f"商品图不存在：{product_path}")

    bg = Image.open(bg_path).convert("RGBA")
    bg = bg.resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
    bg = apply_template_overlays(bg, config.get("overlays") or [])

    product = Image.open(product_path).convert("RGBA")
    product_cfg = config["product"]
    product = fit_rgba(product, product_cfg["w"], product_cfg["h"])
    paste_product_with_shadow(
        bg, product, product_cfg["x"], product_cfg["y"],
        shadow=bool(config.get("product_shadow", True)),
    )

    if refine_enabled:
        try:
            import importlib.util
            repo_root = Path(__file__).resolve().parents[2]
            svc_path = repo_root / "module3-background" / "app" / "services.py"
            spec = importlib.util.spec_from_file_location("m3_refine", svc_path)
            m3 = importlib.util.module_from_spec(spec)
            assert spec.loader is not None
            spec.loader.exec_module(m3)
            tmp = POSTER_DIR / f"_pre_refine_{uuid.uuid4().hex}.jpg"
            bg.convert("RGB").save(tmp, "JPEG", quality=92)
            size = f"{canvas_w}x{canvas_h}"
            # Seedream 常见尺寸；非方图时退回 1024x1024
            if abs(canvas_w - canvas_h) > 80:
                size = "1024x1024"
            refined = m3.refine_composite(
                tmp,
                POSTER_DIR,
                engine=refine_engine,
                prompt=(
                    "Lightly refine this commercial product composite into a seamless lifestyle photo. "
                    f"Product context: {product_hint}. "
                    "Keep the exact product packaging, logo and shape unchanged. "
                    "Only soften cutout edges, add natural contact shadow on the surface, "
                    "match scene lighting. No extra objects, no text overlay, no watermark, no redesign."
                ),
                strength=refine_strength,
                size=size,
            )
            bg = Image.open(refined).convert("RGBA").resize((canvas_w, canvas_h), Image.Resampling.LANCZOS)
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
        except Exception as exc:
            print(f"[poster] {refine_engine} refine skipped: {exc}")

    draw = ImageDraw.Draw(bg, "RGBA")
    auto_layout = bool(style_options.get("auto_layout", True))
    stroke_enabled = style_options.get("text_stroke_enabled", False)
    stroke_color = style_options.get("text_stroke_color", "#FFFFFF")
    stroke_width = style_options.get("text_stroke_width", 2)
    shadow_enabled = style_options.get("text_shadow_enabled", True)

    default_layer_config = get_default_layer_config(canvas_w, canvas_h)
    for key, override in (config.get("text_defaults") or {}).items():
        if key in default_layer_config and isinstance(override, dict):
            default_layer_config[key] = {**default_layer_config[key], **override}

    text_layers = style_options.get("text_layers") or [
        {"key": "title", "text": title},
        {"key": "subtitle", "text": discount},
        {"key": "cta_text", "text": price},
    ]
    for layer in text_layers:
        layer["text"] = sanitize_poster_text(layer.get("text") or "")

    zone = text_safe_zone(canvas_w, canvas_h, config) if auto_layout else None
    cursor_y = zone["y"] if zone else None
    max_w = zone["w"] if zone else int(canvas_w * 0.48)
    if zone and zone.get("panel_light") and not style_options.get("force_stroke"):
        stroke_enabled = False

    chip_texts = []
    if layout_mode in ("chips", "lifestyle", "premium_dark"):
        for layer in text_layers:
            if layer.get("key") in ("selling_point_1", "selling_point_2") and layer.get("text"):
                chip_texts.append(layer["text"])

    accent = config.get("accent_color") or "#5B7C6E"
    chips_drawn = False

    def _draw_chips_at(y_pos: int) -> int:
        chip_font = load_font(22, "msyh")
        border = "#FFFFFF" if layout_mode == "premium_dark" else "#2A343A"
        tcol = "#FFFFFF" if layout_mode == "premium_dark" else "#2A343A"
        fill = (255, 255, 255, 36) if layout_mode == "premium_dark" else (255, 255, 255, 90)
        # 长卖点先缩小字号再画，尽量完整
        fitted = []
        for t in chip_texts:
            f, _, _ = fit_wrapped_text(draw, t, "msyh", 22, max_w - 28, max_lines=3, min_size=16)
            fitted.append(t)
        return draw_feature_chips(
            draw, fitted, zone["x"] if zone else 60, y_pos, chip_font, max_w,
            text_color=tcol, border_color=border, fill_color=fill,
        )

    for layer in text_layers:
        text = layer.get("text", "")
        if not text:
            continue
        key = layer.get("key")
        if key in ("selling_point_1", "selling_point_2") and layout_mode in ("chips", "lifestyle", "premium_dark"):
            continue

        default_cfg = default_layer_config.get(key, default_layer_config["title"])
        manual_xy = layer.get("x") is not None or layer.get("y") is not None
        x = layer.get("x") if layer.get("x") is not None else default_cfg["x"]
        y = layer.get("y") if layer.get("y") is not None else default_cfg["y"]
        font_size = layer.get("font_size") if layer.get("font_size") is not None else default_cfg["font_size"]
        color = layer.get("color") or default_cfg["color"]
        font_name = layer.get("font_name") or default_cfg.get("font_name", "msyh")
        art_style = layer.get("art_style") or default_cfg.get("art_style", "normal")

        if auto_layout and not manual_xy and zone is not None:
            x = zone["x"]
            y = zone["cta_y"] if key == "cta_text" else (cursor_y if cursor_y is not None else y)

        if zone and zone.get("panel_light") and art_style in ("stroke_shadow", "glow", "strong"):
            art_style = "normal" if key != "title" else "shadow"

        sample_lum = region_luminance(bg, x, y, min(max_w, 360), max(40, font_size + 20))
        layer_stroke = stroke_enabled
        layer_stroke_color = stroke_color
        if sample_lum > 170 and art_style in ("stroke", "stroke_shadow"):
            if color.lower() in ("#ffffff", "#fff", "#f8f8f6", "#e8fff8"):
                layer_stroke_color = "#222222"
            else:
                layer_stroke = False
                art_style = "shadow" if art_style == "stroke_shadow" else "normal"
        elif sample_lum < 70 and art_style == "normal" and not (zone and zone.get("panel_light")):
            art_style = "shadow"

        font = load_font(font_size, font_name)
        if auto_layout and key != "cta_text":
            max_lines = 3 if key == "title" else 2
            font, font_size, _ = fit_wrapped_text(
                draw, text, font_name, font_size, max_w, max_lines=max_lines, min_size=18,
            )

        if key == "cta_text":
            if chip_texts and not chips_drawn and cursor_y is not None:
                cursor_y = _draw_chips_at(cursor_y)
                chips_drawn = True
            button_color = layer.get("button_color") or default_cfg.get("button_color", "#111111")
            draw_cta_button(
                draw=draw, text=text, x=x,
                y=(zone["cta_y"] if (auto_layout and zone and not manual_xy) else y),
                font=font, text_color=color, button_color=button_color, art_style=art_style,
            )
        elif key == "subtitle" and layout_mode == "lifestyle" and config.get("subtitle_as_pill"):
            pill_font = load_font(max(20, font_size - 2), font_name)
            next_y = draw_subtitle_pill(
                draw, text, x, y, pill_font, fill="#FFFFFF",
                bg=default_cfg.get("pill_bg") or "#3A3A3A",
                max_width=max_w,
            )
            if auto_layout and not manual_xy and cursor_y is not None:
                cursor_y = next_y
                if chip_texts and not chips_drawn:
                    cursor_y = _draw_chips_at(cursor_y)
                    chips_drawn = True
        else:
            max_lines = 3 if key == "title" else 2
            if auto_layout:
                font, font_size, lines = fit_wrapped_text(
                    draw, text, font_name, font_size, max_w, max_lines=max_lines, min_size=18,
                )
            else:
                lines = [ellipsize_to_width(draw, text, font, max_w)]
            next_y = draw_multiline_art(
                draw, lines, x, y, font, color, art_style, 6 if key == "title" else 4,
                layer_stroke, layer_stroke_color, stroke_width, shadow_enabled,
            )
            if key == "title" and config.get("title_underline"):
                draw_accent_line(draw, x, next_y - 4, min(120, max_w // 3), accent)
                next_y += 14
            if auto_layout and not manual_xy and cursor_y is not None:
                cursor_y = next_y + (22 if key == "title" else 16)
                if key == "subtitle" and chip_texts and not chips_drawn:
                    cursor_y = _draw_chips_at(cursor_y)
                    chips_drawn = True

    if chip_texts and not chips_drawn and cursor_y is not None:
        _draw_chips_at(cursor_y)

    filename = f"poster_{uuid.uuid4().hex}.png"
    save_path = POSTER_DIR / filename
    POSTER_DIR.mkdir(parents=True, exist_ok=True)
    bg.convert("RGB").save(save_path, quality=95)
    return f"/static/poster/{filename}"
