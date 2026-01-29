# -*- coding: utf-8 -*-
"""
ptcfextract: Point Cloud Local Geometry Features (Linearity / Planarity / Scattering)

Core capabilities:
- Read LAS/LAZ (preserve all original point dimensions)
- Optional voxel downsampling (index-based)
- Optional outlier removal (Open3D SOR / ROR)
- Compute per-point local geometry features:
    linearity, planarity, scattering (L/P/S)
- Optional Open3D visualization:
    RGB=[L,P,S] or colormap on single feature
- Export ONLY TWO outputs:
    1) Overwrite RGB with normalized [L,P,S] (R=L,G=P,B=S), preserve other dims
    2) Preserve original RGB, add ExtraBytes dims: linearity/planarity/scattering (float32)

Author: Kenneth Kwabena Kenney
"""

import os
from typing import Optional, Tuple, Dict, Any

import numpy as np
import laspy
from laspy import ExtraBytesParams

import open3d as o3d
from scipy.spatial import cKDTree
import cv2


# -------------------------
# Utilities: scaling/color
# -------------------------

def safe_minmax_scale(col: np.ndarray, eps: float = 1e-12) -> np.ndarray:
    """
    Scale to [0,1] safely.
    - NaNs/infs -> 0
    - Constant arrays -> 0.5 on finite entries
    """
    col = col.astype(np.float64)
    mask = np.isfinite(col)
    if not np.any(mask):
        return np.zeros_like(col, dtype=np.float64)

    mn = np.nanmin(col[mask])
    mx = np.nanmax(col[mask])
    if (mx - mn) < eps:
        out = np.zeros_like(col, dtype=np.float64)
        out[mask] = 0.5
        return out

    out = (col - mn) / (mx - mn)
    out[~mask] = 0.0
    return out


def features_to_rgb(features_lps: np.ndarray) -> np.ndarray:
    """
    Map Nx3 [L,P,S] -> Nx3 RGB in [0,1] using per-column min-max scaling.
    R=L, G=P, B=S.
    """
    L = safe_minmax_scale(features_lps[:, 0])
    P = safe_minmax_scale(features_lps[:, 1])
    S = safe_minmax_scale(features_lps[:, 2])
    rgb = np.vstack([L, P, S]).T
    rgb = np.nan_to_num(rgb, nan=0.0, posinf=1.0, neginf=0.0)
    return np.clip(rgb, 0.0, 1.0)


def scalar_to_colormap_rgb(scalar: np.ndarray, cmap=cv2.COLORMAP_JET) -> np.ndarray:
    """
    Map scalar (N,) -> Nx3 RGB in [0,1] using OpenCV colormap.
    """
    s = safe_minmax_scale(scalar)
    s_u8 = np.uint8(np.clip(s * 255.0, 0, 255))
    cm = cv2.applyColorMap(s_u8, cmap)  # BGR
    cm = cm[:, 0, :]                    # Nx3
    cm = cm[:, ::-1]                    # BGR -> RGB
    return (cm.astype(np.float32) / 255.0)


def make_o3d_pointcloud(xyz: np.ndarray, rgb01: Optional[np.ndarray] = None) -> o3d.geometry.PointCloud:
    """
    Build an Open3D PointCloud, optionally with colors in [0,1].
    """
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(xyz.astype(np.float64))
    if rgb01 is not None:
        rgb01 = np.nan_to_num(rgb01, nan=0.0, posinf=1.0, neginf=0.0)
        rgb01 = np.clip(rgb01, 0.0, 1.0)
        pcd.colors = o3d.utility.Vector3dVector(rgb01.astype(np.float64))
    return pcd


# -------------------------
# Downsampling / Outliers
# -------------------------

def voxel_downsample_indices(xyz: np.ndarray, voxel_size: float) -> np.ndarray:
    """
    Voxel downsample by selecting the first point in each voxel.
    Returns indices into xyz.
    """
    if voxel_size is None or voxel_size <= 0:
        return np.arange(xyz.shape[0], dtype=np.int64)

    minXYZ = np.min(xyz, axis=0)
    v = np.floor((xyz - minXYZ) / voxel_size).astype(np.int64)

    nx = v[:, 0].max() + 1
    ny = v[:, 1].max() + 1
    voxel_id = (nx * ny * v[:, 2] + nx * v[:, 1] + v[:, 0]).astype(np.int64)

    _, first_idx = np.unique(voxel_id, return_index=True)
    first_idx = np.sort(first_idx)
    return first_idx.astype(np.int64)


def outlier_removal_indices(
    xyz: np.ndarray,
    mode: str,
    sor_nb_neighbors: int,
    sor_std_ratio: float,
    ror_nb_points: int,
    ror_radius: float,
) -> np.ndarray:
    """
    Returns inlier indices based on Open3D outlier removal.
    Indices refer to xyz passed in.
    """
    if mode is None or mode.lower() == "none":
        return np.arange(xyz.shape[0], dtype=np.int64)

    pcd = make_o3d_pointcloud(xyz)
    mode = mode.lower()

    if mode == "sor":
        _, ind = pcd.remove_statistical_outlier(
            nb_neighbors=int(sor_nb_neighbors),
            std_ratio=float(sor_std_ratio)
        )
        return np.array(ind, dtype=np.int64)

    if mode == "ror":
        _, ind = pcd.remove_radius_outlier(
            nb_points=int(ror_nb_points),
            radius=float(ror_radius)
        )
        return np.array(ind, dtype=np.int64)

    raise ValueError(f"Unknown outlier removal mode: {mode}")


# -------------------------
# Feature computation
# -------------------------

def compute_lps_features(
    xyz: np.ndarray,
    radius: float,
    min_neighbors: int = 10,
    eps: float = 1e-12
) -> np.ndarray:
    """
    Compute per-point linearity/planarity/scattering using radius neighbors.

    For each point i:
      - find neighbors within radius
      - compute covariance of neighbor xyz
      - eigenvalues: e0 <= e1 <= e2 (clipped to >= 0)
      - linearity  = (e2 - e1) / e2
      - planarity  = (e1 - e0) / e2
      - scattering = e0 / e2

    Robust to:
      - too few neighbors -> NaNs
      - degenerate covariance / division-by-zero -> NaNs
      - numerical noise -> clip eigenvalues to >= 0

    Returns: (N,3) columns [L,P,S]
    """
    xyz = xyz.astype(np.float64)
    kdtree = cKDTree(xyz)
    N = xyz.shape[0]
    feats = np.full((N, 3), np.nan, dtype=np.float64)

    min_neighbors = int(max(3, min_neighbors))

    for i in range(N):
        neighbors = kdtree.query_ball_point(xyz[i], radius)

        if len(neighbors) < min_neighbors:
            continue

        pts = xyz[neighbors]
        cov = np.cov(pts, rowvar=False)
        
        if not np.all(np.isfinite(cov)):
            continue
        
        # Covariance is symmetric => eigvalsh is stable
        e = np.linalg.eigvalsh(cov)
        e.sort()  # e0 <= e1 <= e2
        e = np.clip(e, 0.0, None)  # avoid tiny negative eigenvalues
        e0, e1, e2 = e

        if (not np.isfinite(e2)) or (e2 < eps):
            continue

        linearity = (e2 - e1) / e2
        planarity = (e1 - e0) / e2
        scattering = e0 / e2

        feats[i, :] = [linearity, planarity, scattering]

        if i % 100000 == 0:
            print(f"Feature Iteration: {i}/{N}")

    return feats


# -------------------------
# Export helpers
# -------------------------

def ensure_rgb_supported_or_upgrade(base_las: laspy.LasData) -> Tuple[laspy.LasData, bool]:
    """
    If base already supports RGB, return (base_las, False).
    Otherwise return (new LasData with RGB-supporting point format, True).
    """
    has_rgb = all(d in base_las.point_format.dimension_names for d in ("red", "green", "blue"))
    if has_rgb:
        return base_las, False

    upgraded = laspy.create(file_version=base_las.header.version, point_format=7)  # RGB + gps_time
    upgraded.header.scales = base_las.header.scales
    upgraded.header.offsets = base_las.header.offsets
    return upgraded, True


def write_las_preserve_all(
    out_path: str,
    base_las: laspy.LasData,
    kept_orig_indices: np.ndarray,
    rgb01: Optional[np.ndarray] = None,
    add_lps_dims: bool = False,
    lps_features: Optional[np.ndarray] = None
) -> None:
    """
    Write LAS/LAZ while preserving original dimensions by subsetting
    base_las.points[kept_orig_indices].

    If rgb01 is provided:
      - If original has RGB: overwrite RGB only, preserve all other dims.
      - If original lacks RGB: upgrade point format to write RGB and copy common dims.
        (May not preserve all vendor-specific extra dims.)

    If add_lps_dims True:
      - Add float32 ExtraBytes dims: linearity, planarity, scattering.
    """
    if not out_path:
        return

    kept_orig_indices = np.asarray(kept_orig_indices, dtype=np.int64)

    need_rgb = rgb01 is not None
    original_has_rgb = all(d in base_las.point_format.dimension_names for d in ("red", "green", "blue"))

    if need_rgb and not original_has_rgb:
        print(
            "Warning: Input point cloud has no RGB fields. "
            "Upgrading point format to write RGB. "
            "Some vendor-specific extra dimensions may not be preserved."
        )

        out_las, _ = ensure_rgb_supported_or_upgrade(base_las)

        out_las.x = base_las.x[kept_orig_indices]
        out_las.y = base_las.y[kept_orig_indices]
        out_las.z = base_las.z[kept_orig_indices]

        for dim in ("intensity", "gps_time", "classification",
                    "return_number", "number_of_returns",
                    "scan_angle_rank", "user_data", "point_source_id"):
            if hasattr(base_las, dim) and dim in out_las.point_format.dimension_names:
                setattr(out_las, dim, getattr(base_las, dim)[kept_orig_indices])

    else:
        out_las = laspy.LasData(base_las.header)
        out_las.points = base_las.points[kept_orig_indices]

    if add_lps_dims:
        if lps_features is None or lps_features.ndim != 2 or lps_features.shape[1] != 3:
            raise ValueError("lps_features must be Nx3 [linearity, planarity, scattering].")

        existing = set(out_las.point_format.dimension_names)
        for name in ("linearity", "planarity", "scattering"):
            if name not in existing:
                out_las.add_extra_dim(ExtraBytesParams(name=name, type=np.float32))

        out_las["linearity"] = lps_features[:, 0].astype(np.float32)
        out_las["planarity"] = lps_features[:, 1].astype(np.float32)
        out_las["scattering"] = lps_features[:, 2].astype(np.float32)

    if rgb01 is not None:
        rgb01 = np.nan_to_num(rgb01, nan=0.0, posinf=1.0, neginf=0.0)
        rgb01 = np.clip(rgb01, 0.0, 1.0)
        rgb_u16 = (rgb01 * 65535.0).round().astype(np.uint16)

        if not all(d in out_las.point_format.dimension_names for d in ("red", "green", "blue")):
            raise ValueError("Output does not support RGB; cannot write colors.")

        out_las.red = rgb_u16[:, 0]
        out_las.green = rgb_u16[:, 1]
        out_las.blue = rgb_u16[:, 2]

    out_las.write(out_path)
    print(f"Saved: {out_path}")


# -------------------------
# High-level pipeline
# -------------------------

def process_pointcloud(
    input_path: str,
    output_base: str,
    radius: float = 0.50,
    min_neighbors: int = 10,
    eps: float = 1e-12,
    use_downsample: bool = True,
    voxel_size: float = 0.10,
    outlier_mode: str = "sor",
    sor_nb_neighbors: int = 20,
    sor_std_ratio: float = 2.0,
    ror_nb_points: int = 6,
    ror_radius: float = 0.50,
    visualize: bool = True,
    visualize_mode: str = "rgb",
    colormap: int = cv2.COLORMAP_JET,
    export_rgb_lps_overwrite: bool = True,
    export_add_dims_keep_original_rgb: bool = True,
) -> Dict[str, Any]:
    """
    Run the full pipeline and write two outputs.

    output_base:
      A path like "out.laz" or "out.las". Suffixes are added automatically.

    Returns dict:
      - xyz (Nx3): final processed xyz used for features/viz/export
      - features (Nx3): [L,P,S] for xyz
      - orig_idx: indices into original LAS points (for preserving attributes on export)
    """
    if not os.path.isfile(input_path):
        raise FileNotFoundError(f"Input file not found: {input_path}")

    base_las = laspy.read(input_path)
    xyz0 = np.vstack([base_las.x, base_las.y, base_las.z]).T.astype(np.float64)
    N0 = xyz0.shape[0]
    print(f"Loaded points: {N0}")

    orig_idx = np.arange(N0, dtype=np.int64)
    xyz = xyz0

    if use_downsample:
        ds_idx = voxel_downsample_indices(xyz, voxel_size)
        xyz = xyz[ds_idx]
        orig_idx = orig_idx[ds_idx]
        print(f"After voxel downsample (voxel_size={voxel_size}): {xyz.shape[0]}")

    mode = (outlier_mode or "none").lower()
    if mode != "none":
        in_idx = outlier_removal_indices(
            xyz,
            mode=mode,
            sor_nb_neighbors=sor_nb_neighbors,
            sor_std_ratio=sor_std_ratio,
            ror_nb_points=ror_nb_points,
            ror_radius=ror_radius,
        )
        xyz = xyz[in_idx]
        orig_idx = orig_idx[in_idx]
        print(f"After outlier removal ({mode}): {xyz.shape[0]}")

    features = compute_lps_features(xyz, radius=radius, min_neighbors=min_neighbors, eps=eps)

    nan_count = int(np.isnan(features[:, 0]).sum())
    print(f"Features computed. NaN points: {nan_count}/{features.shape[0]}")

    rgb_lps = features_to_rgb(features)
    rgb_L = scalar_to_colormap_rgb(features[:, 0], colormap)
    rgb_P = scalar_to_colormap_rgb(features[:, 1], colormap)
    rgb_S = scalar_to_colormap_rgb(features[:, 2], colormap)

    if visualize:
        vm = visualize_mode.lower()
        if vm == "rgb":
            pcd = make_o3d_pointcloud(xyz, rgb_lps)
        elif vm == "linearity":
            pcd = make_o3d_pointcloud(xyz, rgb_L)
        elif vm == "planarity":
            pcd = make_o3d_pointcloud(xyz, rgb_P)
        elif vm == "scattering":
            pcd = make_o3d_pointcloud(xyz, rgb_S)
        else:
            raise ValueError(f"Unknown visualize_mode: {visualize_mode}")
        o3d.visualization.draw([pcd])

    stem, ext = os.path.splitext(output_base)
    if ext.lower() not in (".las", ".laz"):
        ext = ".las"

    if export_rgb_lps_overwrite:
        out1 = f"{stem}_rgbLPS_overwriteRGB{ext}"
        write_las_preserve_all(
            out_path=out1,
            base_las=base_las,
            kept_orig_indices=orig_idx,
            rgb01=rgb_lps,
            add_lps_dims=False,
            lps_features=None
        )

    if export_add_dims_keep_original_rgb:
        out2 = f"{stem}_addLPS_extraFields_keepOriginalRGB{ext}"
        write_las_preserve_all(
            out_path=out2,
            base_las=base_las,
            kept_orig_indices=orig_idx,
            rgb01=None,
            add_lps_dims=True,
            lps_features=features
        )

    print("Export complete (2 files).")
    return {"xyz": xyz, "features": features, "orig_idx": orig_idx}

