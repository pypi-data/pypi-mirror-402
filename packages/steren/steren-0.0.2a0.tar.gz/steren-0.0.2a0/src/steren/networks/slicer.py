#!/usr/bin/env python3
"""
yolo_sliced_geotiff_to_shp.py

Run Ultralytics YOLO on a very large georeferenced TIFF by slicing it into overlapping tiles,
mapping detections back to geospatial coordinates, performing a global class-aware NMS,
and exporting results to a Shapefile (.shp).

Usage:
    python yolo_sliced_geotiff_to_shp.py --tif path/to/large.tif --weights yolov8n.pt --out out_detections.shp
"""

import argparse
import math
import os
from pathlib import Path
import numpy as np
import cv2
from ultralytics import YOLO
import torch
from torchvision.ops import batched_nms
import rasterio
from rasterio.windows import Window
from rasterio.transform import Affine
from shapely.geometry import box as shapely_box
import geopandas as gpd
from tqdm import tqdm
import rasterio
from rasterio.windows import Window
from rasterio.transform import Affine, xy  # <- add xy here


# ----------------------------
# helpers
# ----------------------------
def make_tiles(img_w, img_h, tile_size, overlap):
    """Return list of (x1,y1,x2,y2) pixel coords covering image with overlap (pixels)."""
    step = tile_size - overlap
    nx = max(1, math.ceil((img_w - overlap) / step))
    ny = max(1, math.ceil((img_h - overlap) / step))

    tiles = []
    for iy in range(ny):
        for ix in range(nx):
            x1 = ix * step
            y1 = iy * step
            x2 = x1 + tile_size
            y2 = y1 + tile_size

            if x2 > img_w:
                x2 = img_w
                x1 = max(0, x2 - tile_size)
            if y2 > img_h:
                y2 = img_h
                y1 = max(0, y2 - tile_size)

            tiles.append((int(x1), int(y1), int(x2), int(y2)))
    # remove duplicates
    tiles = list(dict.fromkeys(tiles))
    return tiles

def read_tile_rgb(dataset, x1, y1, x2, y2, out_size=None):
    """
    Read window [x1,x2) x [y1,y2) from rasterio dataset and return HWC RGB uint8 array.
    out_size: (height, width) to rescale the read tile to (optional).
    Assumes raster has at least 3 bands (RGB). If >3 bands, uses first 3.
    """
    w = x2 - x1
    h = y2 - y1
    window = Window(x1, y1, w, h)
    # Read bands (1-indexed). Read minimum of 3 bands or all if fewer
    count = dataset.count
    bands_to_read = min(3, count)
    arr = dataset.read(range(1, bands_to_read + 1), window=window)  # shape (bands, h, w)

    # If bands < 3, replicate or pad
    if arr.shape[0] == 1:
        arr = np.repeat(arr, 3, axis=0)
    elif arr.shape[0] == 2:
        arr = np.vstack([arr, arr[0:1, :, :]])

    # convert to HWC
    tile = np.transpose(arr, (1, 2, 0))  # H, W, C

    # Raster values may be not in 0-255. Attempt rescale if dtype != uint8
    if tile.dtype != np.uint8:
        # scale using min/max per-tile (safe heuristic). If you want to use dataset-specific scaling, change here.
        tmin, tmax = tile.min(), tile.max()
        if tmax > tmin:
            tile = ((tile - tmin) / (tmax - tmin) * 255.0).astype(np.uint8)
        else:
            tile = np.clip(tile, 0, 255).astype(np.uint8)
    else:
        tile = tile.copy()

    # If out_size specified, resize tile to that size (width,height)
    if out_size is not None:
        tile = cv2.resize(tile, (out_size[1], out_size[0]), interpolation=cv2.INTER_LINEAR)

    # Ensure channel order is RGB (rasterio gives bands in dataset order)
    return tile

def pixel_to_geo(transform: Affine, x, y):
    """Map pixel coordinates (x,y) to geographic coords using rasterio transform (upper-left origin)."""
    # rasterio.transform.xy expects row, col -> y, x (row = y pixel)
    # but we pass x,y as pixel coords so row=y, col=x
    # xy returns (x_geo, y_geo)
    from rasterio.transform import xy
    xgeo, ygeo = xy(transform, y,x, offset='center')
    return xgeo, ygeo

# ----------------------------
# main tiled inference -> shapefile
# ----------------------------
def run_geotiff_sliced_to_shp(
    tif_path,
    weights="yolov8n.pt",
    tile_size=512,
    overlap=200,
    conf_thresh=0.25,
    iou_thresh=0.45,
    device=None,
    out_shp="detections.shp",
    class_names=None,
    debug=False
):
    tif_path = str(tif_path)
    if not os.path.exists(tif_path):
        raise FileNotFoundError(tif_path)

    # open dataset
    with rasterio.open(tif_path) as ds:
        img_w = ds.width
        img_h = ds.height
        transform = ds.transform
        crs = ds.crs  # may be None

        tiles = make_tiles(img_w, img_h, tile_size, overlap)
        print(f"[info] image: {img_w}x{img_h}, tiles: {len(tiles)}, tile={tile_size}, overlap={overlap}")
        model = YOLO(weights)
        if device:
            model.model.to(device)

        all_boxes = []   # pixel-space boxes [x1,y1,x2,y2]
        all_scores = []
        all_classes = []

        for t_idx, (x1, y1, x2, y2) in enumerate(tqdm(tiles)):
            # Read tile into RGB np.uint8. Resize to model-friendly size if desired (we let model auto-resize)
            tile_rgb = read_tile_rgb(ds, x1, y1, x2, y2, out_size=None)  # HWC uint8
            if tile_rgb is None:
                continue

            # Ultralytics model.predict accepts numpy HWC (RGB)
            # we pass imgsz=min(tile_size,2048) and conf threshold
            results = model.predict(source=tile_rgb, conf=conf_thresh, imgsz=min(tile_size, 2048), device=device, verbose=False)
            r = results[0]

            if r.boxes is None or len(r.boxes) == 0:
                if debug:
                    print(f" tile {t_idx+1}/{len(tiles)}: 0 boxes")
                continue

            boxes = r.boxes.xyxy.cpu().numpy()  # coordinates in tile pixel space
            scores = r.boxes.conf.cpu().numpy()
            classes = r.boxes.cls.cpu().numpy().astype(int)

            # map tile coords -> full image pixel coords by adding offsets
            boxes[:, 0] += x1  # x1
            boxes[:, 1] += y1  # y1
            boxes[:, 2] += x1  # x2
            boxes[:, 3] += y1  # y2

            for b, s, c in zip(boxes, scores, classes):
                all_boxes.append(b.tolist())
                all_scores.append(float(s))
                all_classes.append(int(c))

            if debug:
                print(f" tile {t_idx+1}/{len(tiles)}: {len(boxes)} boxes")

    # no detections
    if len(all_boxes) == 0:
        print("[info] no detections found")
        return

    # convert to tensors and clamp within image bounds
    boxes = torch.tensor(all_boxes, dtype=torch.float32)
    scores = torch.tensor(all_scores, dtype=torch.float32)
    labels = torch.tensor(all_classes, dtype=torch.int64)

    # clamp boxes to image
    boxes[:, 0].clamp_(0, img_w - 1)
    boxes[:, 1].clamp_(0, img_h - 1)
    boxes[:, 2].clamp_(0, img_w - 1)
    boxes[:, 3].clamp_(0, img_h - 1)

    # Perform class-aware NMS
    keep = batched_nms(boxes, scores, labels, iou_thresh)
    boxes_kept = boxes[keep].cpu().numpy()
    scores_kept = scores[keep].cpu().numpy()
    labels_kept = labels[keep].cpu().numpy()

    print(f"[info] {len(all_boxes)} raw boxes -> {len(keep)} after global NMS")

    # Build GeoDataFrame with bbox polygons
    geoms = []
    attrs = []

    for (x1, y1, x2, y2), s, cls in zip(boxes_kept, scores_kept, labels_kept):

        # Convert BOX EDGES → PIXEL CENTERS
        print(y1)
        print(y2)
       
        x1g, y1g = xy(transform, [y1], [x1], offset='ul')
        x2g, y2g = xy(transform, [y2], [x2], offset='ul')

        print(y1g)
        print(y2g)

        xmin, xmax = sorted([x1g, x2g])
        ymin, ymax = sorted([y1g, y2g])
        geoms.append(shapely_box(xmin, ymin, xmax, ymax))

        attrs.append({
            "class_id": int(cls),
            "score": float(s)
        })

    gdf = gpd.GeoDataFrame(attrs, geometry=geoms, crs=crs)

    # If class names provided, add column
    if class_names is not None:
        # create name column mapping through IDs
        gdf["class_name"] = gdf["class_id"].apply(lambda x: class_names[x] if 0 <= x < len(class_names) else str(x))

    # Save to shapefile (driver determined by extension)
    out_shp = str(out_shp)
    out_dir = os.path.dirname(out_shp)
    if out_dir and not os.path.exists(out_dir):
        os.makedirs(out_dir, exist_ok=True)

    # geopandas will save as shapefile when .shp extension provided. Note: shapefile has 10-char limits for field names.
    print(f"[info] writing {len(gdf)} features to {out_shp} (CRS={crs})")
    gdf.to_file(out_shp, driver="ESRI Shapefile")
    print("[info] done.")


# ----------------------------
# CLI
# ----------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--tif", required=True, help="Path to large georeferenced TIFF")
    parser.add_argument("--weights", default="yolov8n.pt", help="YOLO weights")
    parser.add_argument("--tile_size", type=int, default=1024)
    parser.add_argument("--overlap", type=int, default=200)
    parser.add_argument("--conf_thresh", type=float, default=0.25)
    parser.add_argument("--iou_thresh", type=float, default=0.45)
    parser.add_argument("--device", default=None, help="'cpu' or 'cuda:0'")
    parser.add_argument("--out", default="detections.shp", help="Output shapefile (.shp)")
    parser.add_argument("--class_names", default=None, help="Optional path to newline-separated class names file")
    parser.add_argument("--debug", action="store_true")
    args = parser.parse_args()

    class_names = None
    if args.class_names:
        with open(args.class_names, "r") as f:
            class_names = [ln.strip() for ln in f if ln.strip()]

    run_geotiff_sliced_to_shp(
        tif_path=args.tif,
        weights=args.weights,
        tile_size=args.tile_size,
        overlap=args.overlap,
        conf_thresh=args.conf_thresh,
        iou_thresh=args.iou_thresh,
        device=args.device,
        out_shp=args.out,
        class_names=class_names,
        debug=args.debug
    )

