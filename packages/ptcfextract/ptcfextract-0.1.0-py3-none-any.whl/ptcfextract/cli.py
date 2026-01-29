import argparse
import cv2

from .core import process_pointcloud


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="ptcfextract",
        description="Compute per-point linearity/planarity/scattering for LAS/LAZ and export two outputs."
    )

    p.add_argument("-i", "--input", required=True, help="Path to input .las or .laz")
    p.add_argument("-o", "--output", required=True, help="Base output path (.las/.laz). Suffixes will be added.")

    # Neighborhood
    p.add_argument("--radius", type=float, default=0.50, help="Neighborhood radius (same units as coordinates)")
    p.add_argument("--min-neighbors", type=int, default=10, help="Minimum neighbors required to compute features")
    p.add_argument("--eps", type=float, default=1e-12, help="Eigenvalue guard to avoid division by zero")

    # Downsample
    p.add_argument("--downsample", action="store_true", help="Enable voxel downsampling")
    p.add_argument("--voxel", type=float, default=0.10, help="Voxel size (requires --downsample)")

    # Outlier removal
    p.add_argument("--outlier", choices=["none", "sor", "ror"], default="sor", help="Outlier removal mode")
    p.add_argument("--sor-nn", type=int, default=20, help="SOR nb_neighbors")
    p.add_argument("--sor-std", type=float, default=2.0, help="SOR std_ratio")
    p.add_argument("--ror-np", type=int, default=6, help="ROR nb_points")
    p.add_argument("--ror-r", type=float, default=0.50, help="ROR radius")

    # Visualization
    p.add_argument("--no-viz", action="store_true", help="Disable Open3D visualization")
    p.add_argument("--viz", choices=["rgb", "linearity", "planarity", "scattering"], default="rgb",
                   help="Visualization mode")
    p.add_argument("--colormap", choices=["jet"], default="jet", help="Colormap (currently only jet)")

    # Outputs (Only two, but allow disabling either)
    p.add_argument("--no-overwrite-rgb", action="store_true",
                   help="Disable output 1 (overwrite RGB with LPS)")
    p.add_argument("--no-add-dims", action="store_true",
                   help="Disable output 2 (add ExtraBytes L/P/S while keeping original RGB)")

    return p


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    cmap = cv2.COLORMAP_JET  # currently only option

    process_pointcloud(
        input_path=args.input,
        output_base=args.output,
        radius=args.radius,
        min_neighbors=args.min_neighbors,
        eps=args.eps,
        use_downsample=bool(args.downsample),
        voxel_size=args.voxel,
        outlier_mode=args.outlier,
        sor_nb_neighbors=args.sor_nn,
        sor_std_ratio=args.sor_std,
        ror_nb_points=args.ror_np,
        ror_radius=args.ror_r,
        visualize=not args.no_viz,
        visualize_mode=args.viz,
        colormap=cmap,
        export_rgb_lps_overwrite=not args.no_overwrite_rgb,
        export_add_dims_keep_original_rgb=not args.no_add_dims,
    )
