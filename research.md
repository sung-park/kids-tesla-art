# Kids Tesla Art — Research Document

## UV Glass/Window Masking Issue (2026-03-06)

### Problem
When a kid's drawing is mapped onto the Tesla UV template, the **window/glass areas** on the side panels get painted with the kid's drawing content (or blank space). The kid's template has empty window areas (light blue visual guides), but the full side-view region (including windows) gets warped and composited onto the UV template.

### Current Pipeline Analysis

#### 1. Kid Template (generate_templates.py)
- Side views: Left y=20-390, Right y=730-1000 in 1024x1024 space
- Windows drawn in light blue `(210, 230, 248)` as visual guides
- Kids color the body area but leave windows empty
- The window region occupies roughly the top 40% of each side panel (y=0.10 to 0.44 normalized)

#### 2. Warp Mapping (model3_warp.json)
- `left_side` src_points: y range 20-390 (full height including windows)
  - 5x3 grid: rows at y=20 (roofline/window top), y=205 (mid), y=390 (bottom/wheels)
- `right_side` src_points: y range 730-1000 (full height including windows)
- Maps to UV strips: left x=14-278, right x=749-1014, y=131-994

#### 3. Compositing (compositing.py)
- `generate_uv_mask()` treats ALL white areas (gray > 200) as paintable
- No distinction between body panels and glass/window regions in UV space
- Kid's drawing (including empty window area) gets composited everywhere the mask allows

#### 4. UV Template (model3.png)
- Outline-only drawing, all interior areas are white
- Side strips include both body and glass regions with no color differentiation
- The mask treats both as equally paintable

### Root Cause
No glass/window exclusion zones defined in the UV space. The paintable mask includes window areas, so warped content (including the kid's uncolored window space) paints over them.

### Key Coordinates

#### Left Side in UV Space
- Full strip: x=14-278, y=131-994
- Panels (top-to-bottom in UV): rear_quarter(131-380), rear_door(380-590), front_door(590-800), front_fender(800-994)
- The UV template outline shows window cutouts in the door panels

#### Right Side in UV Space
- Full strip: x=749-1014, y=131-994
- Mirror of left side

### Solution Options

#### Option A: Glass Exclusion Mask in UV Space (Recommended)
- Define polygon regions for each glass area in UV coordinates
- Add glass_regions to model3_warp.json or model3_panels.json
- Modify `generate_uv_mask()` to zero out glass regions from paintable mask
- Optionally fill glass with tinted color for realistic appearance
- **Pros**: Doesn't change warp math, works regardless of kid's drawing, clean separation
- **Cons**: Need to manually identify glass polygon coordinates from UV template

#### Option B: Split Warp Regions (body-only mapping)
- Change warp src_points to only cover body portion (below windows)
- Change dst_points to only target body area of UV strips
- **Pros**: More precise mapping, less wasted warp computation
- **Cons**: Requires precise window line coordinates in both kid and UV space, more complex

#### Option C: Color-based filtering in compositing
- Detect the light blue window color from warped image and exclude
- **Pros**: Simple concept
- **Cons**: Fragile (depends on exact color surviving camera capture + processing)

**Recommendation: Option A** — cleanest, least invasive, most robust.

---

## Previous Research (archived)

### TPS-based Warping (implemented)
- Piecewise affine warping via Delaunay triangulation replaces per-panel perspective
- 5x3 control point grids per side region, separate grids for hood/roof/trunk
- cv2.remap() for fast application (<10ms per image)

### Tesla Custom Wrap Specs
- PNG, 1024x1024, ≤1MB, USB "Wraps" folder
- Apply via Toybox → Paint Shop → Wraps

### Infrastructure
- OCI ARM64, Docker, Nginx, GitHub Actions CI/CD
