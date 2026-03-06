#!/usr/bin/env python3
"""Generate printable PDF templates for Kids Tesla Art.

Each template is an A4 page with:
  - Tesla side-view silhouettes (Left Side, Right Side) that kids recognize as a car
  - Top-view layout for Hood, Roof, Trunk
  - 4 ArUco markers (DICT_4X4_50, IDs 0-3) at page corners

Panel regions match the kid_quad coordinates in *_panels.json exactly,
so coloring maps directly onto the Tesla UV wrap via per-panel perspective warping.

Usage:
    python scripts/generate_templates.py

Outputs:
    frontend/public/templates/model3-template.pdf
    frontend/public/templates/modely-template.pdf
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import cv2
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas as rl_canvas
except ImportError as exc:
    print(f"Missing dependency: {exc}")
    print("Install with: pip install opencv-contrib-python Pillow reportlab")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
PDF_OUTPUT_DIR = REPO_ROOT / "frontend" / "public" / "templates"
UV_DIR = REPO_ROOT / "backend" / "app" / "templates"

# A4 at 300 DPI
PAGE_W_PX, PAGE_H_PX = 2480, 3508
PAGE_W_PT, PAGE_H_PT = A4

ARUCO_DICT_ID = cv2.aruco.DICT_4X4_50
MARKER_PX = 200
MARGIN_PX = 100

# Drawable area (inside markers)
DRAW_X0 = MARGIN_PX + MARKER_PX
DRAW_Y0 = MARGIN_PX + MARKER_PX
DRAW_X1 = PAGE_W_PX - MARGIN_PX - MARKER_PX
DRAW_Y1 = PAGE_H_PX - MARGIN_PX - MARKER_PX
DRAW_W = DRAW_X1 - DRAW_X0
DRAW_H = DRAW_Y1 - DRAW_Y0

# kid_quad uses 1024x1024 coordinate space — scale to page
KID_SCALE_X = DRAW_W / 1024.0
KID_SCALE_Y = DRAW_H / 1024.0


def _kid_to_page(kx, ky):
    return (DRAW_X0 + kx * KID_SCALE_X, DRAW_Y0 + ky * KID_SCALE_Y)


def _load_font(size):
    for path in [
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except (IOError, OSError):
            pass
    return ImageFont.load_default()


def _generate_aruco(marker_id, size_px):
    aruco_dict = cv2.aruco.getPredefinedDictionary(ARUCO_DICT_ID)
    marker_bgr = cv2.aruco.generateImageMarker(aruco_dict, marker_id, size_px)
    return Image.fromarray(cv2.cvtColor(marker_bgr, cv2.COLOR_BGR2RGB))


def _draw_aruco_markers(img):
    for marker_id, (mx, my) in enumerate([
        (MARGIN_PX, MARGIN_PX),
        (PAGE_W_PX - MARGIN_PX - MARKER_PX, MARGIN_PX),
        (PAGE_W_PX - MARGIN_PX - MARKER_PX, PAGE_H_PX - MARGIN_PX - MARKER_PX),
        (MARGIN_PX, PAGE_H_PX - MARGIN_PX - MARKER_PX),
    ]):
        img.paste(_generate_aruco(marker_id, MARKER_PX), (mx, my))


# ---------------------------------------------------------------------------
# Tesla side profile point definitions (normalized 0.0–1.0 within bounding box)
# ---------------------------------------------------------------------------

# Model 3: low roofline, fastback silhouette
_MODEL3_BODY = [
    (0.01, 0.96), (0.01, 0.68), (0.04, 0.56), (0.07, 0.50),
    (0.25, 0.44), (0.33, 0.16), (0.39, 0.09),
    (0.69, 0.09), (0.77, 0.24), (0.84, 0.43),
    (0.89, 0.50), (0.93, 0.56), (0.99, 0.68), (0.99, 0.96),
]
# Full side glass: A-pillar to C-pillar, roofline to beltline
_MODEL3_SIDE_GLASS = [
    (0.25, 0.50), (0.33, 0.17), (0.39, 0.10),
    (0.69, 0.10), (0.77, 0.25), (0.84, 0.49),
]
# Pillar positions (normalized x): A-pillar, B-pillar, C-pillar
_MODEL3_A_PILLAR = ((0.29, 0.48), (0.36, 0.14))
_MODEL3_B_PILLAR_X = 0.535
_MODEL3_C_PILLAR = ((0.73, 0.18), (0.80, 0.47))
_MODEL3_FRONT_WHEEL = (0.20, 0.90, 0.085)
_MODEL3_REAR_WHEEL = (0.77, 0.90, 0.085)
_MODEL3_DOOR_X = 0.535

# Model Y: taller, more upright SUV profile
_MODELY_BODY = [
    (0.01, 0.96), (0.01, 0.66), (0.04, 0.54), (0.07, 0.48),
    (0.25, 0.40), (0.32, 0.12), (0.38, 0.06),
    (0.69, 0.06), (0.77, 0.12), (0.84, 0.40),
    (0.89, 0.48), (0.93, 0.54), (0.99, 0.66), (0.99, 0.96),
]
_MODELY_SIDE_GLASS = [
    (0.25, 0.47), (0.32, 0.13), (0.38, 0.07),
    (0.69, 0.07), (0.77, 0.13), (0.84, 0.46),
]
_MODELY_A_PILLAR = ((0.29, 0.45), (0.35, 0.11))
_MODELY_B_PILLAR_X = 0.535
_MODELY_C_PILLAR = ((0.73, 0.15), (0.81, 0.44))
_MODELY_FRONT_WHEEL = (0.20, 0.90, 0.085)
_MODELY_REAR_WHEEL = (0.77, 0.90, 0.085)
_MODELY_DOOR_X = 0.535


def _scale_pts(pts, x0, y0, w, h):
    return [(x0 + p[0] * w, y0 + p[1] * h) for p in pts]


def _draw_car_side(draw, x0, y0, w, h, model="model3", flip=False,
                   fill=(255, 255, 255)):
    if model == "modely":
        body_pts_n = _MODELY_BODY
        glass_pts_n = _MODELY_SIDE_GLASS
        a_pillar_n = _MODELY_A_PILLAR
        b_pillar_x_n = _MODELY_B_PILLAR_X
        c_pillar_n = _MODELY_C_PILLAR
        fw = _MODELY_FRONT_WHEEL
        rw = _MODELY_REAR_WHEEL
        door_x_n = _MODELY_DOOR_X
    else:
        body_pts_n = _MODEL3_BODY
        glass_pts_n = _MODEL3_SIDE_GLASS
        a_pillar_n = _MODEL3_A_PILLAR
        b_pillar_x_n = _MODEL3_B_PILLAR_X
        c_pillar_n = _MODEL3_C_PILLAR
        fw = _MODEL3_FRONT_WHEEL
        rw = _MODEL3_REAR_WHEEL
        door_x_n = _MODEL3_DOOR_X

    if flip:
        body_pts_n = [(1.0 - p[0], p[1]) for p in body_pts_n]
        glass_pts_n = [(1.0 - p[0], p[1]) for p in glass_pts_n]
        a_pillar_n = ((1.0 - a_pillar_n[0][0], a_pillar_n[0][1]),
                      (1.0 - a_pillar_n[1][0], a_pillar_n[1][1]))
        b_pillar_x_n = 1.0 - b_pillar_x_n
        c_pillar_n = ((1.0 - c_pillar_n[0][0], c_pillar_n[0][1]),
                      (1.0 - c_pillar_n[1][0], c_pillar_n[1][1]))
        fw = (1.0 - fw[0], fw[1], fw[2])
        rw = (1.0 - rw[0], rw[1], rw[2])
        door_x_n = 1.0 - door_x_n

    body_pts = _scale_pts(body_pts_n, x0, y0, w, h)
    glass_pts = _scale_pts(glass_pts_n, x0, y0, w, h)

    # Car body fill
    draw.polygon(body_pts, fill=fill)

    # Full side glass (large area covering A-pillar to C-pillar)
    draw.polygon(glass_pts, fill=(200, 220, 245), outline=(100, 120, 140), width=4)

    # Pillar lines (A, B, C) as visual separators within glass
    a_p = _scale_pts(list(a_pillar_n), x0, y0, w, h)
    draw.line(a_p, fill=(80, 100, 120), width=6)
    c_p = _scale_pts(list(c_pillar_n), x0, y0, w, h)
    draw.line(c_p, fill=(80, 100, 120), width=6)

    # B-pillar (vertical divider at door line within glass)
    glass_ys = [p[1] for p in glass_pts_n]
    glass_top_y = min(glass_ys)
    glass_bot_y = max(glass_ys)
    bp_top = (x0 + b_pillar_x_n * w, y0 + (glass_top_y + 0.02) * h)
    bp_bot = (x0 + b_pillar_x_n * w, y0 + glass_bot_y * h)
    draw.line([bp_top, bp_bot], fill=(80, 100, 120), width=8)

    # Headlights / taillights
    hl_x = x0 + (0.07 if not flip else 0.93) * w
    hl_y = y0 + 0.62 * h
    draw.ellipse([hl_x - 15, hl_y - 9, hl_x + 15, hl_y + 9],
                 fill=(255, 240, 180), outline=(160, 140, 80), width=3)
    tl_x = x0 + (0.93 if not flip else 0.07) * w
    tl_y = y0 + 0.64 * h
    draw.ellipse([tl_x - 15, tl_y - 9, tl_x + 15, tl_y + 9],
                 fill=(255, 160, 160), outline=(180, 80, 80), width=3)

    # Door line (below glass only — beltline to sill)
    door_x = x0 + door_x_n * w
    door_top_y = y0 + glass_bot_y * h
    door_bot_y = y0 + 0.70 * h
    draw.line([(door_x, door_top_y), (door_x, door_bot_y)],
              fill=(160, 160, 160), width=5)

    # Door handles
    handle_y = glass_bot_y + 0.04
    handle_positions = [(0.38, handle_y), (0.67, handle_y)]
    if flip:
        handle_positions = [(1.0 - hx, hy) for hx, hy in handle_positions]
    for hx_n, hy_n in handle_positions:
        hx = x0 + hx_n * w
        hy = y0 + hy_n * h
        hw, hh = w * 0.06, h * 0.025
        draw.rectangle([hx - hw / 2, hy - hh / 2, hx + hw / 2, hy + hh / 2],
                       fill=(180, 180, 180), outline=(100, 100, 100), width=2)

    # Body outline
    for i in range(len(body_pts)):
        p1 = body_pts[i]
        p2 = body_pts[(i + 1) % len(body_pts)]
        draw.line([p1, p2], fill=(60, 60, 60), width=9)

    # Wheels
    for (cx_n, cy_n, cr_n) in [fw, rw]:
        cx = x0 + cx_n * w
        cy = y0 + cy_n * h
        cr = cr_n * w
        draw.ellipse([cx - cr, cy - cr, cx + cr, cy + cr],
                     fill=(80, 80, 80), outline=(40, 40, 40), width=4)
        inner = cr * 0.55
        draw.ellipse([cx - inner, cy - inner, cx + inner, cy + inner],
                     fill=(200, 200, 200), outline=(120, 120, 120), width=3)


def _draw_car_top(draw, x0, y0, w, h):
    taper = w * 0.13
    body_pts = [
        (x0 + taper, y0),
        (x0 + w - taper, y0),
        (x0 + w, y0 + h * 0.12),
        (x0 + w, y0 + h * 0.88),
        (x0 + w - taper, y0 + h),
        (x0 + taper, y0 + h),
        (x0, y0 + h * 0.88),
        (x0, y0 + h * 0.12),
    ]
    hood_split = y0 + h * 0.30
    roof_split = y0 + h * 0.65

    # Hood
    hood_pts = [
        (x0 + taper, y0), (x0 + w - taper, y0),
        (x0 + w, y0 + h * 0.12), (x0 + w, hood_split),
        (x0, hood_split), (x0, y0 + h * 0.12),
    ]
    draw.polygon(hood_pts, fill=(255, 255, 255))

    # Roof
    roof_pts = [
        (x0, hood_split), (x0 + w, hood_split),
        (x0 + w, roof_split), (x0, roof_split),
    ]
    draw.polygon(roof_pts, fill=(255, 255, 255))

    # Trunk
    trunk_pts = [
        (x0, roof_split), (x0 + w, roof_split),
        (x0 + w, y0 + h * 0.88),
        (x0 + w - taper, y0 + h), (x0 + taper, y0 + h),
        (x0, y0 + h * 0.88),
    ]
    draw.polygon(trunk_pts, fill=(255, 255, 255))

    # Section dividers
    draw.line([(x0, hood_split), (x0 + w, hood_split)], fill=(160, 160, 160), width=5)
    draw.line([(x0, roof_split), (x0 + w, roof_split)], fill=(160, 160, 160), width=5)

    # Windshield (front)
    ins = w * 0.15
    ws_y1 = hood_split - h * 0.02
    ws_y2 = hood_split + h * 0.06
    ws_pts = [(x0 + ins, ws_y1), (x0 + w - ins, ws_y1),
              (x0 + w - ins * 0.8, ws_y2), (x0 + ins * 0.8, ws_y2)]
    draw.polygon(ws_pts, fill=(200, 218, 240), outline=(100, 120, 140), width=3)

    # Rear window
    rw_y1 = roof_split - h * 0.04
    rw_y2 = roof_split + h * 0.04
    rw_pts = [(x0 + ins, rw_y1), (x0 + w - ins, rw_y1),
              (x0 + w - ins * 0.8, rw_y2), (x0 + ins * 0.8, rw_y2)]
    draw.polygon(rw_pts, fill=(200, 218, 240), outline=(100, 120, 140), width=3)

    # Outline
    for i in range(len(body_pts)):
        p1 = body_pts[i]
        p2 = body_pts[(i + 1) % len(body_pts)]
        draw.line([p1, p2], fill=(60, 60, 60), width=9)


def generate_template_png(model):
    panels_path = UV_DIR / f"{model}_panels.json"
    panels = json.loads(panels_path.read_text())["panels"] if panels_path.exists() else []

    img = Image.new("RGB", (PAGE_W_PX, PAGE_H_PX), (255, 255, 255))
    draw = ImageDraw.Draw(img)

    # -----------------------------------------------------------------------
    # Compute page rects for each kid_quad region
    # -----------------------------------------------------------------------
    def kid_rect(name):
        for p in panels:
            if p["name"] == name:
                kq = p["kid_quad"]
                kx0 = min(pt[0] for pt in kq)
                ky0 = min(pt[1] for pt in kq)
                kx1 = max(pt[0] for pt in kq)
                ky1 = max(pt[1] for pt in kq)
                px0, py0 = _kid_to_page(kx0, ky0)
                px1, py1 = _kid_to_page(kx1, ky1)
                return px0, py0, px1 - px0, py1 - py0
        return None

    def kid_rect_group(prefix):
        rects = [kid_rect(p["name"]) for p in panels if p["name"].startswith(prefix)]
        rects = [r for r in rects if r]
        if not rects:
            return None
        x0 = min(r[0] for r in rects)
        y0 = min(r[1] for r in rects)
        x1 = max(r[0] + r[2] for r in rects)
        y1 = max(r[1] + r[3] for r in rects)
        return x0, y0, x1 - x0, y1 - y0

    left_r = kid_rect_group("left_")
    right_r = kid_rect_group("right_")
    hood_r = kid_rect("hood")
    roof_r = kid_rect("roof")
    trunk_r = kid_rect("trunk")

    # Panel boundary x-positions for divider lines (in page coords)
    side_dividers = []
    for kx in [266, 512, 758]:
        px, _ = _kid_to_page(kx, 0)
        side_dividers.append(px)

    # -----------------------------------------------------------------------
    # Draw section labels above each view
    # -----------------------------------------------------------------------
    label_font = _load_font(52)
    small_font = _load_font(40)

    def section_header(text, x0, y0, w, color=(80, 80, 80), y_offset=-55):
        draw.text((x0 + w / 2, y0 + y_offset), text, fill=color, anchor="mm", font=label_font)

    # -----------------------------------------------------------------------
    # LEFT SIDE VIEW
    # -----------------------------------------------------------------------
    if left_r:
        x0, y0, w, h = left_r
        pad = w * 0.02
        _draw_car_side(draw, x0 + pad, y0 + pad * 2,
                       w - pad * 2, h - pad * 4,
                       model=model, flip=False)
        for dx in side_dividers:
            for seg_y in range(int(y0 + h * 0.08), int(y0 + h * 0.92), 30):
                draw.line([(dx, seg_y), (dx, seg_y + 15)],
                          fill=(180, 180, 180), width=3)
        section_header("Left Side", x0, y0, w, (160, 80, 80))

    # -----------------------------------------------------------------------
    # TOP VIEW (hood + roof + trunk stacked)
    # -----------------------------------------------------------------------
    if hood_r and roof_r and trunk_r:
        top_x0 = hood_r[0]
        top_y0 = hood_r[1]
        top_w = hood_r[2]
        top_h = trunk_r[1] + trunk_r[3] - hood_r[1]
        pad = top_w * 0.04
        _draw_car_top(draw, top_x0 + pad, top_y0,
                      top_w - pad * 2, top_h)

        # Section labels
        for name, rect in [("Hood", hood_r), ("Front Bumper", roof_r), ("Trunk", trunk_r)]:
            rx, ry, rw, rh = rect
            draw.text((rx + rw / 2, ry + rh / 2), name,
                      fill=(90, 90, 90), anchor="mm", font=label_font)

        section_header("Top View", top_x0, top_y0, top_w, (80, 100, 160))

    # -----------------------------------------------------------------------
    # RIGHT SIDE VIEW (flipped)
    # -----------------------------------------------------------------------
    if right_r:
        x0, y0, w, h = right_r
        pad = w * 0.02
        _draw_car_side(draw, x0 + pad, y0 + pad * 2,
                       w - pad * 2, h - pad * 4,
                       model=model, flip=False)
        for dx in side_dividers:
            for seg_y in range(int(y0 + h * 0.08), int(y0 + h * 0.92), 30):
                draw.line([(dx, seg_y), (dx, seg_y + 15)],
                          fill=(180, 180, 180), width=3)
        section_header("Right Side", x0, y0, w, (80, 80, 160), y_offset=65)

    # -----------------------------------------------------------------------
    # ArUco markers
    # -----------------------------------------------------------------------
    _draw_aruco_markers(img)

    # -----------------------------------------------------------------------
    # Bottom instructions
    # -----------------------------------------------------------------------
    model_label = "Model 3" if model == "model3" else "Model Y"
    lines = [
        f"Kids Tesla Art — {model_label}",
        "Color each section with crayons or markers.",
        "Keep all 4 corner squares visible when you take a photo!",
        "Upload at tesla.sunggeun.com",
    ]
    title_font = _load_font(60)
    inst_font = _load_font(40)
    base_y = PAGE_H_PX - MARGIN_PX - MARKER_PX // 2
    for i, line in enumerate(lines):
        font = title_font if i == 0 else inst_font
        color = (60, 60, 60) if i == 0 else (120, 120, 120)
        draw.text(
            (PAGE_W_PX // 2, base_y - (len(lines) - 1 - i) * 70),
            line, fill=color, anchor="mm", font=font,
        )

    return img


def create_pdf(template_png, output_path):
    import io
    output_path.parent.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    template_png.save(buf, format="PNG")
    buf.seek(0)
    c = rl_canvas.Canvas(str(output_path), pagesize=A4)
    c.drawImage(ImageReader(buf), 0, 0, width=PAGE_W_PT, height=PAGE_H_PT)
    c.save()
    print(f"  PDF saved: {output_path}")


def main(args=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["model3", "modely"])
    opts = parser.parse_args(args)
    PDF_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    for model in opts.models:
        print(f"\nGenerating: {model}")
        create_pdf(generate_template_png(model), PDF_OUTPUT_DIR / f"{model}-template.pdf")
    print("\nDone.")


if __name__ == "__main__":
    main()
