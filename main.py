#!/usr/bin/env python3
"""
Crop Health Monitor - NDVI Analysis Pipeline

Main entry point for processing Landsat 7 satellite imagery to assess
crop and vegetation health using the Normalized Difference Vegetation
Index (NDVI).

Usage:
    python main.py --red B4.TIF --nir B5.TIF [--output ./output]

This script processes red and near-infrared bands from Landsat 7 Level-2
surface reflectance products to generate:
    - Colour-coded NDVI vegetation zone map (PNG)
    - Greyscale band visualisations (PNG)
    - Statistical analysis report (TXT)
    - Zone breakdown data (CSV)

Each run creates a timestamped subfolder within the output directory,
and copies the input TIF files into that folder for organisation.
"""

import argparse
import os
import shutil
import sys
from datetime import datetime

from file_loader import load_bands
from ndvi_processor import compute_ndvi, classify_zones
from visualiser import save_outputs
from report_writer import compute_stats, write_txt_report, write_csv_report


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        None (reads from sys.argv)

    Returns:
        argparse.Namespace with parsed arguments:
            - red: Path to red band GeoTIFF (B4)
            - nir: Path to NIR band GeoTIFF (B5)
            - output: Output directory path

    Raises:
        SystemExit: If required arguments are missing.
    """
    parser = argparse.ArgumentParser(
        description='Crop Health Monitor - NDVI Analysis Pipeline',
        epilog='Process Landsat 7 imagery to assess vegetation health.',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--red',
        type=str,
        required=True,
        help='Path to red band GeoTIFF file (Landsat B4, ~670nm)'
    )

    parser.add_argument(
        '--nir',
        type=str,
        required=True,
        help='Path to NIR band GeoTIFF file (Landsat B5, ~800nm)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='./output',
        help='Output directory for results (default: ./output)'
    )

    return parser.parse_args()


def create_run_folder(base_output: str) -> str:
    """
    Create a timestamped subfolder for this analysis run.

    Generates a unique folder name using the current timestamp in the
    format 'run_YYYYMMDD_HHMMSS' to organise multiple analysis runs.

    Args:
        base_output: Base output directory path.

    Returns:
        Full path to the created run-specific subfolder.

    Raises:
        OSError: If the directory cannot be created.
    """
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    run_folder = os.path.join(base_output, f'run_{timestamp}')
    os.makedirs(run_folder, exist_ok=True)
    return run_folder


def copy_input_files(red_path: str, nir_path: str, run_folder: str) -> tuple[str, str]:
    """
    Copy input TIF files to the run folder for organisation.

    Copies the original red and NIR band files into the run-specific
    output folder to keep inputs and outputs together.

    Args:
        red_path: Path to the original red band GeoTIFF file.
        nir_path: Path to the original NIR band GeoTIFF file.
        run_folder: Destination folder for the copies.

    Returns:
        Tuple of (new_red_path, new_nir_path) pointing to the copied files.

    Raises:
        FileNotFoundError: If source files do not exist.
        OSError: If files cannot be copied.
    """
    red_filename = os.path.basename(red_path)
    nir_filename = os.path.basename(nir_path)

    new_red_path = os.path.join(run_folder, red_filename)
    new_nir_path = os.path.join(run_folder, nir_filename)

    shutil.copy2(red_path, new_red_path)
    shutil.copy2(nir_path, new_nir_path)

    return new_red_path, new_nir_path


def main() -> int:
    """
    Execute the NDVI analysis pipeline.

    Orchestrates the full processing workflow:
        1. Parse command-line arguments
        2. Create timestamped run folder within output directory
        3. Copy input TIF files to run folder
        4. Load red and NIR bands from GeoTIFF files
        5. Compute NDVI
        6. Classify into vegetation zones
        7. Save visualisation outputs (PNG images)
        8. Compute statistics
        9. Write text and CSV reports

    Args:
        None

    Returns:
        Exit code: 0 for success, 1 for error.

    Raises:
        None (all exceptions are caught and reported).
    """
    try:
        # Parse arguments
        args = parse_arguments()

        print("=" * 50)
        print("CROP HEALTH MONITOR - NDVI Analysis")
        print("=" * 50)
        print()

        # Create base output directory if it doesn't exist
        print(f"[1/8] Setting up output directory: {args.output}")
        os.makedirs(args.output, exist_ok=True)

        # Create timestamped run folder
        run_folder = create_run_folder(args.output)
        print(f"       Created run folder: {os.path.basename(run_folder)}")

        # Copy input TIF files to run folder
        print(f"[2/8] Copying input files to run folder...")
        copy_input_files(args.red, args.nir, run_folder)
        print(f"       Copied: {os.path.basename(args.red)}, {os.path.basename(args.nir)}")

        # Load bands
        print(f"[3/8] Loading red band: {args.red}")
        print(f"       Loading NIR band: {args.nir}")
        red, nir = load_bands(args.red, args.nir)
        print(f"       Image dimensions: {red.shape[1]} x {red.shape[0]} pixels")

        # Compute NDVI
        print("[4/8] Computing NDVI...")
        ndvi = compute_ndvi(red, nir)
        print("       NDVI computation complete.")

        # Classify zones
        print("[5/8] Classifying vegetation zones...")
        zones = classify_zones(ndvi)
        print("       Zone classification complete.")

        # Save visualisation outputs
        print("[6/8] Generating visualisations...")
        save_outputs(ndvi, red, nir, run_folder)
        print(f"       Saved: ndvi_map.png, red_band.png, nir_band.png")

        # Compute statistics
        print("[7/8] Computing statistics...")
        stats = compute_stats(ndvi, zones)
        print(f"       Valid pixels: {stats['valid_pixels']:,}")
        print(f"       Mean NDVI: {stats['mean_ndvi']:.4f}")

        # Write reports
        print("[8/8] Writing reports...")
        txt_path = os.path.join(run_folder, 'report.txt')
        csv_path = os.path.join(run_folder, 'zones.csv')
        write_txt_report(stats, txt_path)
        write_csv_report(stats, csv_path)
        print(f"       Saved: report.txt, zones.csv")

        print()
        print("=" * 50)
        print("ANALYSIS COMPLETE")
        print("=" * 50)
        print(f"Results saved to: {os.path.abspath(run_folder)}")

        # Print quick zone summary
        print()
        print("Zone Summary:")
        for zone_name, zone_data in stats['zones'].items():
            print(f"  {zone_name}: {zone_data['percentage']:.1f}%")

        # Check for stress alert
        stressed_pct = stats['zones']['stressed/sparse']['percentage']
        bare_pct = stats['zones']['bare/dry soil']['percentage']
        if stressed_pct + bare_pct > 30.0:
            print()
            print("⚠️  ALERT: High stress detected! See report.txt for details.")

        return 0

    except FileNotFoundError as e:
        print(f"\nERROR: File not found - {e}", file=sys.stderr)
        print("Please check that the specified band files exist.", file=sys.stderr)
        return 1

    except ValueError as e:
        print(f"\nERROR: Invalid data - {e}", file=sys.stderr)
        return 1

    except Exception as e:
        print(f"\nERROR: Unexpected error - {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
