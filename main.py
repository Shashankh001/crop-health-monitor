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
"""

import argparse
import os
import sys

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


def main() -> int:
    """
    Execute the NDVI analysis pipeline.

    Orchestrates the full processing workflow:
        1. Parse command-line arguments
        2. Create output directory
        3. Load red and NIR bands from GeoTIFF files
        4. Compute NDVI
        5. Classify into vegetation zones
        6. Save visualisation outputs (PNG images)
        7. Compute statistics
        8. Write text and CSV reports

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

        # Create output directory if it doesn't exist
        print(f"[1/7] Setting up output directory: {args.output}")
        os.makedirs(args.output, exist_ok=True)

        # Load bands
        print(f"[2/7] Loading red band: {args.red}")
        print(f"      Loading NIR band: {args.nir}")
        red, nir = load_bands(args.red, args.nir)
        print(f"      Image dimensions: {red.shape[1]} x {red.shape[0]} pixels")

        # Compute NDVI
        print("[3/7] Computing NDVI...")
        ndvi = compute_ndvi(red, nir)
        print("      NDVI computation complete.")

        # Classify zones
        print("[4/7] Classifying vegetation zones...")
        zones = classify_zones(ndvi)
        print("      Zone classification complete.")

        # Save visualisation outputs
        print("[5/7] Generating visualisations...")
        save_outputs(ndvi, red, nir, args.output)
        print(f"      Saved: ndvi_map.png, red_band.png, nir_band.png")

        # Compute statistics
        print("[6/7] Computing statistics...")
        stats = compute_stats(ndvi, zones)
        print(f"      Valid pixels: {stats['valid_pixels']:,}")
        print(f"      Mean NDVI: {stats['mean_ndvi']:.4f}")

        # Write reports
        print("[7/7] Writing reports...")
        txt_path = os.path.join(args.output, 'report.txt')
        csv_path = os.path.join(args.output, 'zones.csv')
        write_txt_report(stats, txt_path)
        write_csv_report(stats, csv_path)
        print(f"      Saved: report.txt, zones.csv")

        print()
        print("=" * 50)
        print("ANALYSIS COMPLETE")
        print("=" * 50)
        print(f"Results saved to: {os.path.abspath(args.output)}")

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
