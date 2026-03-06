#!/usr/bin/env python3
"""Interactive warp calibration UI.

Parameters are center + span + offset per region — easier to tune than raw coordinates.

Usage:
    cd /Users/sung-park/Dev/kids-tesla-art
    backend/.venv/bin/python scripts/calibrate_warp.py [model3|modely] [--input PATH]

Controls:
    S  — save current values to *_warp.json
    R  — reset to original values
    Q  — quit without saving
"""

import argparse
import json
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO / "backend"))

import cv2
import numpy as np
from PIL import Image, ImageDraw

TEMPLATES_DIR = REPO / "backend" / "app" / "templates"
OUTPUT_SIZE = 1024

# ---------------------------------------------------------------------------
# Warp helpers (inline, no import of cached module so we can recompute freely)
# ---------------------------------------------------------------------------

def _delaunay_triangles(points):
    rect = (0, 0, OUTPUT_SIZE, OUTPUT_SIZE)
    subdiv = cv2.Subdiv2D(rect)
    clamped = points.copy()
    clamped[:, 0] = np.clip(clamped[:, 0], 1, OUTPUT_SIZE - 2)
    clamped[:, 1] = np.clip(clamped[:, 1], 1, OUTPUT_SIZE - 2)
    for pt in clamped:
        subdiv.insert((float(pt[0]), float(pt[1])))
    tri_list = subdiv.getTriangleList()
    triangles = []
    for t in tri_list:
        tri_pts = np.array([[t[0], t[1]], [t[2], t[3]], [t[4], t[5]]])
        indices = []
        for tp in tri_pts:
            dists = np.sum((clamped - tp) ** 2, axis=1)
            idx = int(np.argmin(dists))
            if dists[idx] < 10.0:
                indices.append(idx)
        if len(indices) == 3 and len(set(indices)) == 3:
            triangles.append(indices)
    return np.array(triangles, dtype=np.int32)


def _build_region_warp_map(src_pts, dst_pts):
    triangles = _delaunay_triangles(dst_pts)
    if len(triangles) == 0:
        return (np.full((OUTPUT_SIZE, OUTPUT_SIZE), -1.0, dtype=np.float32),
                np.full((OUTPUT_SIZE, OUTPUT_SIZE), -1.0, dtype=np.float32))
    mapx = np.full((OUTPUT_SIZE, OUTPUT_SIZE), -1.0, dtype=np.float32)
    mapy = np.full((OUTPUT_SIZE, OUTPUT_SIZE), -1.0, dtype=np.float32)
    for tri_idx in range(len(triangles)):
        t = triangles[tri_idx]
        d0, d1, d2 = dst_pts[t[0]], dst_pts[t[1]], dst_pts[t[2]]
        s0, s1, s2 = src_pts[t[0]], src_pts[t[1]], src_pts[t[2]]
        xs = [float(d0[0]), float(d1[0]), float(d2[0])]
        ys = [float(d0[1]), float(d1[1]), float(d2[1])]
        x_min = max(0, int(min(xs)))
        x_max = min(OUTPUT_SIZE - 1, int(max(xs)) + 1)
        y_min = max(0, int(min(ys)))
        y_max = min(OUTPUT_SIZE - 1, int(max(ys)) + 1)
        if x_min >= x_max or y_min >= y_max:
            continue
        dst_tri = np.float32([d0, d1, d2])
        src_tri = np.float32([s0, s1, s2])
        area = abs((d1[0]-d0[0])*(d2[1]-d0[1]) - (d2[0]-d0[0])*(d1[1]-d0[1]))
        if area < 1.0:
            continue
        M = cv2.getAffineTransform(dst_tri, src_tri)
        yy, xx = np.mgrid[y_min:y_max + 1, x_min:x_max + 1]
        px = xx.flatten().astype(np.float64)
        py = yy.flatten().astype(np.float64)
        dx0, dy0 = float(d0[0]), float(d0[1])
        dx1, dy1 = float(d1[0]), float(d1[1])
        dx2, dy2 = float(d2[0]), float(d2[1])
        denom = (dy1-dy2)*(dx0-dx2) + (dx2-dx1)*(dy0-dy2)
        if abs(denom) < 1e-10:
            continue
        a = ((dy1-dy2)*(px-dx2) + (dx2-dx1)*(py-dy2)) / denom
        b = ((dy2-dy0)*(px-dx2) + (dx0-dx2)*(py-dy2)) / denom
        c = 1.0 - a - b
        inside = (a >= -1e-3) & (b >= -1e-3) & (c >= -1e-3)
        src_x = M[0,0]*px + M[0,1]*py + M[0,2]
        src_y = M[1,0]*px + M[1,1]*py + M[1,2]
        ix = xx.flatten()[inside]
        iy = yy.flatten()[inside]
        mapx[iy, ix] = src_x[inside].astype(np.float32)
        mapy[iy, ix] = src_y[inside].astype(np.float32)
    return mapx, mapy


def build_warp_maps_from_config(regions):
    combined_mapx = np.full((OUTPUT_SIZE, OUTPUT_SIZE), -1.0, dtype=np.float32)
    combined_mapy = np.full((OUTPUT_SIZE, OUTPUT_SIZE), -1.0, dtype=np.float32)
    for region in regions:
        src_pts = np.float32(region["src_points"])
        dst_pts = np.float32(region["dst_points"])
        mx, my = _build_region_warp_map(src_pts, dst_pts)
        valid = mx >= 0
        combined_mapx[valid] = mx[valid]
        combined_mapy[valid] = my[valid]
    return combined_mapx, combined_mapy


def do_warp(src, regions):
    mapx, mapy = build_warp_maps_from_config(regions)
    warped = cv2.remap(src.astype(np.float32), mapx, mapy,
                       cv2.INTER_LINEAR, borderMode=cv2.BORDER_CONSTANT,
                       borderValue=(0, 0, 0, 0))
    warped = np.clip(warped, 0, 255).astype(np.uint8)
    # Feather alpha edges
    alpha = warped[:, :, 3]
    kernel = np.ones((3, 3), np.uint8)
    alpha = cv2.erode(alpha, kernel, iterations=1)
    alpha = cv2.GaussianBlur(alpha.astype(np.float32), (5, 5), 1.0)
    warped[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return warped


# ---------------------------------------------------------------------------
# Background removal (same logic as removal.py)
# ---------------------------------------------------------------------------

def remove_bg(rgba: np.ndarray) -> np.ndarray:
    """Make paper background transparent."""
    result = rgba.copy()
    hsv = cv2.cvtColor(result[:, :, :3], cv2.COLOR_RGB2HSV)
    gray = cv2.cvtColor(result[:, :, :3], cv2.COLOR_RGB2GRAY)
    # Detect background: bright enough and low saturation
    bg_mask = ((gray > 170) & (hsv[:, :, 1] < 45)).astype(np.uint8) * 255
    # Morphological closing fills texture gaps / paper wrinkles in background mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (21, 21))
    bg_mask = cv2.morphologyEx(bg_mask, cv2.MORPH_CLOSE, kernel)
    alpha = result[:, :, 3].astype(np.float32)
    alpha[bg_mask > 0] = 0
    alpha = cv2.GaussianBlur(alpha, (5, 5), 1.0)
    result[:, :, 3] = np.clip(alpha, 0, 255).astype(np.uint8)
    return result


# ---------------------------------------------------------------------------
# Colored synthetic kid template
# ---------------------------------------------------------------------------

PANEL_COLORS = {
    "left_front_fender":  (255, 80, 80, 255),
    "left_front_door":    (80, 200, 80, 255),
    "left_rear_door":     (80, 80, 255, 255),
    "left_rear_quarter":  (255, 200, 0, 255),
    "hood":               (255, 128, 0, 255),
    "roof":               (128, 0, 255, 255),
    "trunk":              (0, 200, 200, 255),
    "right_front_fender": (255, 80, 80, 255),
    "right_front_door":   (80, 200, 80, 255),
    "right_rear_door":    (80, 80, 255, 255),
    "right_rear_quarter": (255, 200, 0, 255),
}


def make_colored_kid_image(panels_config):
    img = Image.new("RGBA", (OUTPUT_SIZE, OUTPUT_SIZE), (255, 255, 255, 0))
    draw = ImageDraw.Draw(img)
    for panel in panels_config["panels"]:
        name = panel["name"]
        kq = panel["kid_quad"]
        color = PANEL_COLORS.get(name, (200, 200, 200, 255))
        x0 = min(pt[0] for pt in kq)
        y0 = min(pt[1] for pt in kq)
        x1 = max(pt[0] for pt in kq)
        y1 = max(pt[1] for pt in kq)
        draw.rectangle([x0, y0, x1, y1], fill=color)
        cx, cy = (x0+x1)//2, (y0+y1)//2
        al = min(x1-x0, y1-y0)*0.25
        draw.line([(cx-al, cy), (cx+al, cy)], fill=(0,0,0,255), width=3)
        draw.polygon([(cx+al, cy), (cx+al-10, cy-7), (cx+al-10, cy+7)], fill=(0,0,0,255))
        draw.text((x0+5, y0+3), "ABC", fill=(0,0,0,255))
    return np.array(img)


# ---------------------------------------------------------------------------
# Region builders
# ---------------------------------------------------------------------------

SIDE_X_COLS = [20, 217, 400, 512, 625, 778, 1004]
# Relative positions of SIDE_X_COLS in [0, 1] (for span scaling)
_SIDE_X_LO, _SIDE_X_HI = SIDE_X_COLS[0], SIDE_X_COLS[-1]
SIDE_X_REL = [(_x - _SIDE_X_LO) / (_SIDE_X_HI - _SIDE_X_LO) for _x in SIDE_X_COLS]


def scaled_side_x(x_start, x_end):
    span = x_end - x_start
    return [int(round(x_start + r * span)) for r in SIDE_X_REL]

LEFT_DST_X  = [210, 112, 14]
LEFT_DST_Y  = [994, 816, 640, 500, 420, 358, 131]

RIGHT_DST_X = {"model3": [817, 916, 1014], "modely": [827, 913, 999]}
RIGHT_DST_Y = {"model3": [994, 816, 640, 500, 420, 358, 131],
               "modely": [992, 810, 630, 490, 400, 340, 147]}

HOOD_DST  = {"model3": [[368,175],[512,175],[655,175],[368,399],[512,399],[655,399]],
             "modely": [[361,151],[512,151],[662,151],[361,392],[512,392],[662,392]]}
ROOF_DST  = {"model3": [[276,25],[512,25],[748,25],[276,166],[512,166],[748,166]],
             "modely": [[254,8],[513,8],[771,8],[254,149],[513,149],[771,149]]}
TRUNK_DST = {"model3": [[366,684],[511,684],[655,684],[366,897],[511,897],[655,897]],
             "modely": [[302,633],[512,633],[721,633],[302,941],[512,941],[721,941]]}


def make_side_region(name, dst_x_cols, dst_y_cols, y_start, y_end, x_start, x_end, x_offset):
    """Build a side region with 3-row grid."""
    y_mid = (y_start + y_end) // 2
    y_rows = [y_start, y_mid, y_end]
    x_cols = scaled_side_x(x_start, x_end)
    src_pts, dst_pts = [], []
    for dx, sy in zip(dst_x_cols, y_rows):
        for dy, sx in zip(dst_y_cols, x_cols):
            src_pts.append([int(np.clip(sx + x_offset, -500, 2000)), int(np.clip(sy, 0, 1023))])
            dst_pts.append([dx, dy])
    return {"name": name, "src_points": src_pts, "dst_points": dst_pts}


def make_top_region(name, sx_cols, sy_rows, dst_pts_flat, x_offset, y_offset):
    src_pts = [[int(np.clip(sx + x_offset, 0, 1023)), int(np.clip(sy + y_offset, 0, 1023))]
               for sy in sy_rows for sx in sx_cols]
    return {"name": name, "src_points": src_pts, "dst_points": dst_pts_flat}


def build_regions(p, model):
    regions = []
    _X_CENTER = 512
    lh = p["left_x_span"] // 2
    regions.append(make_side_region("left_side",
        LEFT_DST_X, LEFT_DST_Y,
        p["left_y_start"], p["left_y_end"],
        _X_CENTER - lh, _X_CENTER + lh, p["left_x_off"]))
    rh = p["right_x_span"] // 2
    regions.append(make_side_region("right_side",
        RIGHT_DST_X[model], RIGHT_DST_Y[model],
        p["right_y_start"], p["right_y_end"],
        _X_CENTER - rh, _X_CENTER + rh, p["right_x_off"]))

    hx = [p["top_x_start"], 500, p["top_x_end"]]
    regions.append(make_top_region("hood", hx,
        [p["hood_y_start"], p["hood_y_end"]],
        HOOD_DST[model], p["top_x_off"], p["hood_y_off"]))
    regions.append(make_top_region("roof", hx,
        [p["roof_y_start"], p["roof_y_end"]],
        ROOF_DST[model], p["top_x_off"], p["roof_y_off"]))
    regions.append(make_top_region("trunk", hx,
        [p["trunk_y_start"], p["trunk_y_end"]],
        TRUNK_DST[model], p["top_x_off"], p["trunk_y_off"]))
    return regions


# ---------------------------------------------------------------------------
# Load defaults from current JSON
# ---------------------------------------------------------------------------

def load_defaults(model):
    path = TEMPLATES_DIR / f"{model}_warp.json"
    cfg = json.loads(path.read_text())

    def r(name):
        for region in cfg["regions"]:
            if region["name"] == name:
                return region
        return None

    ls = r("left_side")["src_points"]
    rs = r("right_side")["src_points"]
    hood = r("hood")["src_points"]
    roof = r("roof")["src_points"]
    trunk = r("trunk")["src_points"]

    _X_CENTER = 512
    return {
        # left side
        "left_y_start":  int(ls[0][1]),
        "left_y_end":    int(ls[14][1]),
        "left_x_span":   int(ls[6][0]) - int(ls[0][0]),
        "left_x_off":    (int(ls[0][0]) + int(ls[6][0])) // 2 - _X_CENTER,
        # right side
        "right_y_start": int(rs[0][1]),
        "right_y_end":   int(rs[14][1]),
        "right_x_span":  int(rs[6][0]) - int(rs[0][0]),
        "right_x_off":   (int(rs[0][0]) + int(rs[6][0])) // 2 - _X_CENTER,
        # top regions
        "top_x_start":  int(hood[0][0]),
        "top_x_end":    int(hood[2][0]),
        "top_x_off":    0,
        "hood_y_start": int(hood[0][1]),
        "hood_y_end":   int(hood[3][1]),
        "hood_y_off":   0,
        "roof_y_start": int(roof[0][1]),
        "roof_y_end":   int(roof[3][1]),
        "roof_y_off":   0,
        "trunk_y_start": int(trunk[0][1]),
        "trunk_y_end":   int(trunk[3][1]),
        "trunk_y_off":  0,
    }


def save_json(params, model):
    regions = build_regions(params, model)
    path = TEMPLATES_DIR / f"{model}_warp.json"
    path.write_text(json.dumps({"regions": regions}, indent=2))
    print(f"Saved → {path}")


# ---------------------------------------------------------------------------
# Trackbar spec: (label, min, max, param_key)
# value stored in params = lo + trackbar_position
# ---------------------------------------------------------------------------

TRACKBARS = [
    # --- Left side ---
    ("L y_start",   -50,  700,  "left_y_start"),
    ("L y_end",       0,  800,  "left_y_end"),
    ("L x_span",    100, 2000,  "left_x_span"),
    ("L x_offset", -600,  600,  "left_x_off"),
    # --- Right side ---
    ("R y_start",   560, 1023,  "right_y_start"),
    ("R y_end",     635, 1023,  "right_y_end"),
    ("R x_span",    100, 2000,  "right_x_span"),
    ("R x_offset", -600,  600,  "right_x_off"),
    # --- Top view x span (shared) ---
    ("Top x_start",    0,  700, "top_x_start"),
    ("Top x_end",    425, 1200, "top_x_end"),
    ("Top x_off",   -200,  200, "top_x_off"),
    # --- Hood ---
    ("Hood y_start", 200,  775, "hood_y_start"),
    ("Hood y_end",   300,  875, "hood_y_end"),
    ("Hood y_off",  -160,  160, "hood_y_off"),
    # --- Roof ---
    ("Roof y_start", 300,  800, "roof_y_start"),
    ("Roof y_end",   400,  900, "roof_y_end"),
    ("Roof y_off",  -160,  160, "roof_y_off"),
    # --- Trunk ---
    ("Trunk y_start", 400,  900, "trunk_y_start"),
    ("Trunk y_end",   500, 1023, "trunk_y_end"),
    ("Trunk y_off",  -160,  160, "trunk_y_off"),
]

WIN_PREV = "Preview  [click here then S=save R=reset Q=quit]"
WIN_CTRL = "Controls"


def run(model, input_path=None):
    defaults = load_defaults(model)
    params = dict(defaults)

    uv_template = np.array(
        Image.open(TEMPLATES_DIR / f"{model}.png").convert("RGBA")
          .resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
    )

    panels_config = json.loads(
        (TEMPLATES_DIR / f"{model}_panels.json").read_text()
    )

    if input_path:
        raw = np.array(
            Image.open(input_path).convert("RGBA")
              .resize((OUTPUT_SIZE, OUTPUT_SIZE), Image.LANCZOS)
        )
        kid_img = remove_bg(raw)
        print(f"Input: {input_path}  (background removal applied)")
    else:
        kid_img = make_colored_kid_image(panels_config)
        print("Using synthetic colored template (pass --input for real scan)")

    def render():
        regions = build_regions(params, model)
        warped = do_warp(kid_img, regions)
        # White background
        out = np.full((OUTPUT_SIZE, OUTPUT_SIZE, 3), 255, dtype=np.float32)
        uv_f = uv_template.astype(np.float32)
        uv_a = uv_f[:, :, 3:4] / 255.0          # UV mask (car body shape)
        # UV template at 40% opacity for reference (text not dominant)
        out = uv_f[:, :, :3] * (uv_a * 0.4) + out * (1 - uv_a * 0.4)
        # Warped drawing cropped to UV panel boundaries
        w_alpha = warped[:, :, 3:4].astype(np.float32) / 255.0 * uv_a
        out = warped[:, :, :3].astype(np.float32) * w_alpha + out * (1 - w_alpha)
        out = np.clip(out, 0, 255).astype(np.uint8)
        out = cv2.cvtColor(out, cv2.COLOR_RGB2BGR)
        # Overlay actual parameter values in top-left corner
        lines = [
            f"L  y:{params['left_y_start']}-{params['left_y_end']}  span:{params['left_x_span']}  off:{params['left_x_off']}",
            f"R  y:{params['right_y_start']}-{params['right_y_end']}  span:{params['right_x_span']}  off:{params['right_x_off']}",
            f"Top x:{params['top_x_start']}-{params['top_x_end']}  off:{params['top_x_off']}",
            f"Hood y:{params['hood_y_start']}-{params['hood_y_end']}  off:{params['hood_y_off']}",
            f"Roof y:{params['roof_y_start']}-{params['roof_y_end']}  off:{params['roof_y_off']}",
            f"Trunk y:{params['trunk_y_start']}-{params['trunk_y_end']}  off:{params['trunk_y_off']}",
        ]
        font, scale, thick = cv2.FONT_HERSHEY_SIMPLEX, 0.45, 1
        pad = 4
        for i, line in enumerate(lines):
            y = 18 + i * 20
            cv2.putText(out, line, (pad + 1, y + 1), font, scale, (0, 0, 0), thick + 1)
            cv2.putText(out, line, (pad, y), font, scale, (255, 255, 0), thick)
        return out

    # ---- windows ----
    cv2.namedWindow(WIN_PREV, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_PREV, 720, 720)

    cv2.namedWindow(WIN_CTRL, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(WIN_CTRL, 520, 30)

    ctrl_img = np.zeros((30, 500, 3), dtype=np.uint8)
    cv2.imshow(WIN_CTRL, ctrl_img)

    dirty = [True]

    def make_cb(key, lo):
        def cb(val):
            params[key] = lo + val
            dirty[0] = True
        return cb

    for label, lo, hi, key in TRACKBARS:
        span = hi - lo + 2          # +2 so macOS Cocoa never hits init==max
        init = min(max(params[key] - lo, 0), span - 1)
        cv2.createTrackbar(label, WIN_CTRL, init, span, make_cb(key, lo))

    print("\nCalibration running.  Click Preview window, then:")
    print("  S = save JSON  |  R = reset  |  Q = quit")

    cv2.imshow(WIN_PREV, render())

    while True:
        if dirty[0]:
            dirty[0] = False
            try:
                cv2.imshow(WIN_PREV, render())
            except Exception as e:
                print(f"Render error: {e}")

        k = cv2.waitKey(50) & 0xFF
        if k in (ord('q'), 27):
            print("Quit (not saved).")
            break
        elif k == ord('s'):
            save_json(params, model)
        elif k == ord('r'):
            params.update(defaults)
            for label, lo, hi, key in TRACKBARS:
                span = hi - lo + 2
                cv2.setTrackbarPos(label, WIN_CTRL, min(params[key] - lo, span - 1))
            dirty[0] = True
            print("Reset.")

    cv2.destroyAllWindows()


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Warp calibration UI")
    ap.add_argument("model", nargs="?", default="modely",
                    choices=["model3", "modely"])
    ap.add_argument("--input", "-i", help="Scanned kid template image path")
    args = ap.parse_args()
    run(args.model, args.input)
