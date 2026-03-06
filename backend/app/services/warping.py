"""Piecewise affine warping: kid-template space -> UV space.

Uses control point pairs and Delaunay triangulation to build a smooth
non-linear warp map. The warp map is precomputed once at startup and
reused for every request via cv2.remap() (<10ms per image).

This replaces the old per-panel perspective transform approach which
could not handle the 90-degree rotation between the side-view template
and the vertical UV panel strips.
"""

import json
from pathlib import Path

import cv2
import numpy as np

TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
UV_SIZE = 1024

# Cache: model -> (mapx, mapy)
_warp_cache: dict[str, tuple[np.ndarray, np.ndarray]] = {}


def _load_warp_config(model: str) -> list[dict]:
    path = TEMPLATES_DIR / f"{model}_warp.json"
    if not path.exists():
        raise ValueError(f"Warp config not found for model '{model}': {path}")
    return json.loads(path.read_text())["regions"]


def _find_triangle_index(point: np.ndarray, triangles: np.ndarray,
                         pts: np.ndarray) -> int:
    """Find which Delaunay triangle contains the given point.

    Uses barycentric coordinate test for each triangle.
    Returns triangle index or -1 if not found.
    """
    px, py = float(point[0]), float(point[1])

    for i in range(len(triangles)):
        t = triangles[i]
        x1, y1 = float(pts[t[0]][0]), float(pts[t[0]][1])
        x2, y2 = float(pts[t[1]][0]), float(pts[t[1]][1])
        x3, y3 = float(pts[t[2]][0]), float(pts[t[2]][1])

        denom = (y2 - y3) * (x1 - x3) + (x3 - x2) * (y1 - y3)
        if abs(denom) < 1e-10:
            continue

        a = ((y2 - y3) * (px - x3) + (x3 - x2) * (py - y3)) / denom
        b = ((y3 - y1) * (px - x3) + (x1 - x3) * (py - y3)) / denom
        c = 1.0 - a - b

        if a >= -1e-4 and b >= -1e-4 and c >= -1e-4:
            return i

    return -1


def _delaunay_triangles(points: np.ndarray) -> np.ndarray:
    """Compute Delaunay triangulation, returning triangle vertex indices."""
    rect = (0, 0, UV_SIZE, UV_SIZE)
    subdiv = cv2.Subdiv2D(rect)

    # Clamp points to valid range for Subdiv2D
    clamped = points.copy()
    clamped[:, 0] = np.clip(clamped[:, 0], 1, UV_SIZE - 2)
    clamped[:, 1] = np.clip(clamped[:, 1], 1, UV_SIZE - 2)

    for pt in clamped:
        subdiv.insert((float(pt[0]), float(pt[1])))

    tri_list = subdiv.getTriangleList()
    triangles = []

    for t in tri_list:
        tri_pts = np.array([[t[0], t[1]], [t[2], t[3]], [t[4], t[5]]])
        # Map triangle vertices back to point indices
        indices = []
        for tp in tri_pts:
            dists = np.sum((clamped - tp) ** 2, axis=1)
            idx = int(np.argmin(dists))
            if dists[idx] < 10.0:
                indices.append(idx)
        if len(indices) == 3 and len(set(indices)) == 3:
            triangles.append(indices)

    return np.array(triangles, dtype=np.int32)


def _build_region_warp_map(
    src_pts: np.ndarray,
    dst_pts: np.ndarray,
    output_size: int = UV_SIZE,
) -> tuple[np.ndarray, np.ndarray]:
    """Build remap arrays for one region using piecewise affine warping.

    For each pixel in the destination (UV space), find which Delaunay
    triangle it belongs to, compute barycentric coordinates, and look up
    the corresponding source pixel.
    """
    triangles = _delaunay_triangles(dst_pts)

    if len(triangles) == 0:
        return (np.zeros((output_size, output_size), dtype=np.float32),
                np.zeros((output_size, output_size), dtype=np.float32))

    mapx = np.full((output_size, output_size), -1.0, dtype=np.float32)
    mapy = np.full((output_size, output_size), -1.0, dtype=np.float32)

    # For each triangle, compute the affine inverse mapping
    for tri_idx in range(len(triangles)):
        t = triangles[tri_idx]
        d0, d1, d2 = dst_pts[t[0]], dst_pts[t[1]], dst_pts[t[2]]
        s0, s1, s2 = src_pts[t[0]], src_pts[t[1]], src_pts[t[2]]

        # Bounding box of dst triangle
        xs = [float(d0[0]), float(d1[0]), float(d2[0])]
        ys = [float(d0[1]), float(d1[1]), float(d2[1])]
        x_min = max(0, int(min(xs)))
        x_max = min(output_size - 1, int(max(xs)) + 1)
        y_min = max(0, int(min(ys)))
        y_max = min(output_size - 1, int(max(ys)) + 1)

        if x_min >= x_max or y_min >= y_max:
            continue

        # Compute affine transform: dst -> src
        dst_tri = np.float32([d0, d1, d2])
        src_tri = np.float32([s0, s1, s2])

        # Check for degenerate triangle
        area = abs((d1[0] - d0[0]) * (d2[1] - d0[1]) -
                   (d2[0] - d0[0]) * (d1[1] - d0[1]))
        if area < 1.0:
            continue

        M = cv2.getAffineTransform(dst_tri, src_tri)

        # Generate pixel grid for this bounding box
        yy, xx = np.mgrid[y_min:y_max + 1, x_min:x_max + 1]
        px = xx.flatten().astype(np.float64)
        py = yy.flatten().astype(np.float64)

        # Barycentric coordinates to check if pixel is inside triangle
        dx0, dy0 = float(d0[0]), float(d0[1])
        dx1, dy1 = float(d1[0]), float(d1[1])
        dx2, dy2 = float(d2[0]), float(d2[1])

        denom = (dy1 - dy2) * (dx0 - dx2) + (dx2 - dx1) * (dy0 - dy2)
        if abs(denom) < 1e-10:
            continue

        a = ((dy1 - dy2) * (px - dx2) + (dx2 - dx1) * (py - dy2)) / denom
        b = ((dy2 - dy0) * (px - dx2) + (dx0 - dx2) * (py - dy2)) / denom
        c = 1.0 - a - b

        inside = (a >= -1e-3) & (b >= -1e-3) & (c >= -1e-3)

        # Apply affine transform for inside pixels
        src_x = M[0, 0] * px + M[0, 1] * py + M[0, 2]
        src_y = M[1, 0] * px + M[1, 1] * py + M[1, 2]

        # Write to map
        ix = xx.flatten()[inside]
        iy = yy.flatten()[inside]
        mapx[iy, ix] = src_x[inside].astype(np.float32)
        mapy[iy, ix] = src_y[inside].astype(np.float32)

    return mapx, mapy


def build_warp_maps(model: str) -> tuple[np.ndarray, np.ndarray]:
    """Build combined warp maps for all regions of a model.

    Returns (mapx, mapy) arrays for use with cv2.remap().
    """
    if model in _warp_cache:
        return _warp_cache[model]

    regions = _load_warp_config(model)

    combined_mapx = np.full((UV_SIZE, UV_SIZE), -1.0, dtype=np.float32)
    combined_mapy = np.full((UV_SIZE, UV_SIZE), -1.0, dtype=np.float32)

    for region in regions:
        src_pts = np.float32(region["src_points"])
        dst_pts = np.float32(region["dst_points"])

        region_mapx, region_mapy = _build_region_warp_map(src_pts, dst_pts)

        # Merge: overwrite where region has valid mappings
        valid = region_mapx >= 0
        combined_mapx[valid] = region_mapx[valid]
        combined_mapy[valid] = region_mapy[valid]

    _warp_cache[model] = (combined_mapx, combined_mapy)
    return combined_mapx, combined_mapy


def warp_image(
    src_image: np.ndarray,
    model: str,
) -> np.ndarray:
    """Warp a kid's drawing from template space to UV space.

    Args:
        src_image: RGBA numpy array (1024x1024) from kid template.
        model: Tesla model id ('model3' or 'modely').

    Returns:
        RGBA numpy array (1024x1024) warped to UV layout.
    """
    mapx, mapy = build_warp_maps(model)

    warped = cv2.remap(
        src_image.astype(np.float32),
        mapx,
        mapy,
        interpolation=cv2.INTER_LINEAR,
        borderMode=cv2.BORDER_CONSTANT,
        borderValue=(0, 0, 0, 0),
    )

    return np.clip(warped, 0, 255).astype(np.uint8)


def _load_glass_regions(model: str) -> list[np.ndarray]:
    path = TEMPLATES_DIR / f"{model}_panels.json"
    if not path.exists():
        return []
    config = json.loads(path.read_text())
    regions = []
    for region in config.get("glass_regions", []):
        pts = np.array(region["polygon"], dtype=np.int32)
        regions.append(pts)
    return regions


def generate_uv_mask(uv_template: np.ndarray, model: str = "") -> np.ndarray:
    """Generate a paintable-area mask from the UV template.

    White/bright areas in the template are paintable surfaces.
    Glass regions (from panels config) are excluded from painting.

    Returns:
        Single-channel uint8 mask (0=protected, 255=paintable).
    """
    if uv_template.shape[2] == 4:
        alpha = uv_template[:, :, 3]
        gray = cv2.cvtColor(uv_template[:, :, :3], cv2.COLOR_RGB2GRAY)
        mask = ((gray > 200) & (alpha > 128)).astype(np.uint8) * 255
    else:
        gray = cv2.cvtColor(uv_template, cv2.COLOR_RGB2GRAY)
        mask = (gray > 200).astype(np.uint8) * 255

    # Erode slightly to avoid painting over outlines
    kernel = np.ones((3, 3), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)

    # Exclude glass/window regions from paintable mask
    if model:
        for pts in _load_glass_regions(model):
            cv2.fillPoly(mask, [pts], 0)

    return mask
