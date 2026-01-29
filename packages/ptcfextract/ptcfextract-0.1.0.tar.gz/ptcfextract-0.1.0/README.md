# ptcfextract

`ptcfextract` computes **per-point local geometry features** from point clouds stored in **LAS/LAZ**, useful for feature extraction research pipelines:

- **Linearity**
- **Planarity**
- **Scattering**

It can be used as:
- a **library** (feature extraction only, integrate with your own pipeline)
- a **ready-to-run pipeline** (downsample/outlier removal + visualization + two outputs)
- a **CLI tool** (`ptcfextract`)

---

## Features (What it does)

### Core feature extraction
For each point, neighbors within a radius are used to compute a covariance matrix and eigenvalues. The outputs are:

- `linearity  = (e2 - e1) / e2`
- `planarity  = (e1 - e0) / e2`
- `scattering = e0 / e2`

Robust handling:
- If a point has too few neighbors → outputs are `NaN`
- If covariance is degenerate or division by zero would occur → outputs are `NaN`
- Small negative eigenvalues due to numeric noise are clipped to 0

---

## Outputs (only two)

If your output base is `out.laz`, the tool writes:

### Output 1: RGB overwritten with L/P/S
**`out_rgbLPS_overwriteRGB.laz`**
- RGB is overwritten with normalized `[L,P,S]`
  - **R = Linearity**
  - **G = Planarity**
  - **B = Scattering**
- All other original point dimensions are preserved

This is for instant visualization in CloudCompare / other viewers.

### Output 2: Original RGB kept + scalar fields added
**`out_addLPS_extraFields_keepOriginalRGB.laz`**
- Original RGB remains unchanged
- Adds three ExtraBytes scalar fields (float32):
  - `linearity`
  - `planarity`
  - `scattering`
- All other original point dimensions are preserved

This is for analysis workflows where you want to keep original appearance.

**Note:** If the input has no RGB fields and you request Output 1, ptcfextract upgrades point format to write RGB and prints a warning (some vendor-specific extra dims may not be preserved).

---

## Installation

### Standard install
```bash
pip install ptcfextract
```

### Recommended for LAZ (compressed) support
```bash
pip install "ptcfextract[laz]"
```

## CLI Usage

### Basic (defaults)

```bash
ptcfextract -i input.laz -o out.laz
```

### Help

```bash
ptcfextract --help
```

### Choose neighborhood settings

```bash
ptcfextract -i input.laz -o out.laz --radius 0.5 --min-neighbors 15
```

### Enable downsampling (faster for huge clouds)

```bash
ptcfextract -i input.laz -o out.laz --downsample --voxel 0.1
```

### Outlier removal options

#### No outlier removal

```bash
ptcfextract -i input.laz -o out.laz --outlier none
```

#### Statistical Outlier Removal (SOR)

```bash
ptcfextract -i input.laz -o out.laz --outlier sor --sor-nn 20 --sor-std 2.0
```

#### Radius Outlier Removal (ROR)

```bash
ptcfextract -i input.laz -o out.laz --outlier ror --ror-np 6 --ror-r 0.5
```

### Visualization options

#### Disable visualization (headless / faster batch runs)

```bash
ptcfextract -i input.laz -o out.laz --no-viz
```

#### Visualize a single feature

```bash
ptcfextract -i input.laz -o out.laz --viz linearity
ptcfextract -i input.laz -o out.laz --viz planarity
ptcfextract -i input.laz -o out.laz --viz scattering
```

#### Visualize RGB=[L,P,S]

```bash
ptcfextract -i input.laz -o out.laz --viz rgb
```

### Export control (Only two supported outputs)

#### Disable Output 1 (overwrite RGB with LPS)

```bash
ptcfextract -i input.laz -o out.laz --no-overwrite-rgb
```

#### Disable Output 2 (add L/P/S scalar fields, keep original RGB)

```bash
ptcfextract -i input.laz -o out.laz --no-add-dims
```

---

## Python Usage (Library)

### 1) Feature extraction only (Integrate into your own pipeline)

Use this if you want your own:

* downsampling strategy (e.g., random, uniform, octree)
* visualization (CloudCompare, PyVista, Open3D custom)
* ML pipeline / feature engineering

```python
import laspy
import numpy as np
from ptcfextract import compute_lps_features

las = laspy.read("input.laz")
xyz = np.vstack([las.x, las.y, las.z]).T

features = compute_lps_features(xyz, radius=0.5, min_neighbors=10)

linearity = features[:, 0]
planarity = features[:, 1]
scattering = features[:, 2]
```

### 2) Use the helper voxel downsampler + feature extraction

```python
import laspy
import numpy as np
from ptcfextract import voxel_downsample_indices, compute_lps_features

las = laspy.read("input.laz")
xyz = np.vstack([las.x, las.y, las.z]).T

idx = voxel_downsample_indices(xyz, voxel_size=0.1)
xyz_ds = xyz[idx]

features_ds = compute_lps_features(xyz_ds, radius=0.5, min_neighbors=10)
```

### 3) Apply optional outlier removal indices (but keep full control)

```python
import laspy
import numpy as np
from ptcfextract import outlier_removal_indices, compute_lps_features

las = laspy.read("input.laz")
xyz = np.vstack([las.x, las.y, las.z]).T

inliers = outlier_removal_indices(
    xyz,
    mode="sor",
    sor_nb_neighbors=20,
    sor_std_ratio=2.0,
    ror_nb_points=6,
    ror_radius=0.5,
)

xyz_in = xyz[inliers]
features_in = compute_lps_features(xyz_in, radius=0.5, min_neighbors=10)
```

### 4) Convert features to RGB=[L,P,S] (for your own visualization)

```python
from ptcfextract import features_to_rgb

rgb01 = features_to_rgb(features_in)   # Nx3 float in [0,1]
```

### 5) Convert a single feature to a colormap RGB (for your own visualization)

```python
from ptcfextract import scalar_to_colormap_rgb

rgb_L = scalar_to_colormap_rgb(features_in[:, 0])  # linearity colormap
rgb_P = scalar_to_colormap_rgb(features_in[:, 1])  # planarity colormap
rgb_S = scalar_to_colormap_rgb(features_in[:, 2])  # scattering colormap
```

### 6) Run the full pipeline from Python (downsample→outliers→viz→export)

```python
from ptcfextract import process_pointcloud

process_pointcloud(
    input_path="input.laz",
    output_base="out.laz",
    radius=0.5,
    min_neighbors=10,
    use_downsample=True,
    voxel_size=0.1,
    outlier_mode="sor",
    sor_nb_neighbors=20,
    sor_std_ratio=2.0,
    visualize=True,
    visualize_mode="rgb",
    export_rgb_lps_overwrite=True,
    export_add_dims_keep_original_rgb=True,
)
```

### 7) Export features to LAS manually (advanced control)

If you computed features yourself and want to export using the same preservation logic:

```python
import laspy
import numpy as np
from ptcfextract import write_las_preserve_all, compute_lps_features, features_to_rgb

base = laspy.read("input.laz")
xyz = np.vstack([base.x, base.y, base.z]).T
features = compute_lps_features(xyz, radius=0.5, min_neighbors=10)
rgb01 = features_to_rgb(features)

orig_idx = np.arange(xyz.shape[0], dtype=np.int64)

# Output 1: overwrite RGB with LPS
write_las_preserve_all(
    out_path="out_rgbLPS_overwriteRGB.laz",
    base_las=base,
    kept_orig_indices=orig_idx,
    rgb01=rgb01,
    add_lps_dims=False,
)

# Output 2: keep original RGB, add extra dims
write_las_preserve_all(
    out_path="out_addLPS_extraFields_keepOriginalRGB.laz",
    base_las=base,
    kept_orig_indices=orig_idx,
    rgb01=None,
    add_lps_dims=True,
    lps_features=features,
)
```

---

## Notes & Troubleshooting

### Units matter (meters vs feet)

* `radius`, `voxel`, and `ror-r` are in the same units as the LAS coordinates.
* If your cloud is in **feet**, typical values often need to be larger than meter-based defaults.

### Many NaNs in features

You’ll see a NaN count printed (pipeline mode). If it’s high:

* Increase `--radius`
* Decrease `--min-neighbors`
* Downsample less aggressively (smaller `--voxel`)
* If the cloud is sparse, a small radius may not find enough neighbors

### Performance tips for huge point clouds

* Enable downsampling (`--downsample --voxel 0.1` or larger)
* Disable visualization (`--no-viz`)
* Consider outlier removal only after downsampling

### Input has no RGB fields

* Output 2 still works (extra dims added, original dims preserved).
* Output 1 requires RGB, so ptcfextract upgrades point format to write RGB and prints a warning.

  * This can drop some unusual vendor-specific dimensions depending on the LAS point format and library limitations.

### Viewing in CloudCompare

* Output 1: visualize using **RGB**.
* Output 2: visualize using scalar fields:

  * `linearity`, `planarity`, `scattering`
  * In CloudCompare: open the scalar field dropdown to choose which to view.

---

## Citation

If you use `ptcfextract` in academic work, cite the Zenodo DOI associated with the GitHub release.

