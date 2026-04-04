"""
Report writer module for NDVI analysis statistics and outputs.

This module provides functions to compute statistics from NDVI and zone
classification arrays, and to generate human-readable text reports and
machine-readable CSV reports.
"""

import csv
from typing import Any


# Zone labels (must match ndvi_processor.py)
ZONE_DENSE_VEG = "dense vegetation"
ZONE_MODERATE = "moderate crop"
ZONE_STRESSED = "stressed/sparse"
ZONE_BARE_DRY = "bare/dry soil"
ZONE_WATER_BUILT = "water/built-up"
ZONE_NODATA = "nodata"

# All zone labels in display order
ALL_ZONES = [
    ZONE_DENSE_VEG,
    ZONE_MODERATE,
    ZONE_STRESSED,
    ZONE_BARE_DRY,
    ZONE_WATER_BUILT,
]

# Alert threshold: warn if stressed + bare exceeds this percentage
STRESS_ALERT_THRESHOLD = 30.0


def compute_stats(ndvi: 'np.ndarray', zones: 'np.ndarray') -> dict[str, Any]:
    """
    Compute statistics from NDVI values and zone classifications.

    Calculates summary statistics including valid pixel count, mean NDVI,
    and per-zone pixel counts and percentages.

    Args:
        ndvi: 2D numpy array of NDVI values (float32), with NaN for no-data.
        zones: 2D numpy array of zone labels (strings) matching ndvi shape.

    Returns:
        A dictionary containing:
            - 'total_pixels': int, total number of pixels in the image
            - 'valid_pixels': int, number of non-NaN pixels
            - 'nodata_pixels': int, number of NaN pixels
            - 'mean_ndvi': float, mean NDVI of valid pixels
            - 'min_ndvi': float, minimum NDVI of valid pixels
            - 'max_ndvi': float, maximum NDVI of valid pixels
            - 'zones': dict mapping zone name to {'count': int, 'percentage': float}

    Raises:
        ValueError: If ndvi and zones arrays have different shapes.
    """
    import numpy as np

    if ndvi.shape != zones.shape:
        raise ValueError(
            f"Array shape mismatch: ndvi {ndvi.shape} vs zones {zones.shape}"
        )

    total_pixels = ndvi.size
    valid_mask = ~np.isnan(ndvi)
    valid_pixels = int(np.sum(valid_mask))
    nodata_pixels = total_pixels - valid_pixels

    # Compute NDVI statistics for valid pixels
    if valid_pixels > 0:
        valid_ndvi = ndvi[valid_mask]
        mean_ndvi = float(np.nanmean(valid_ndvi))
        min_ndvi = float(np.nanmin(valid_ndvi))
        max_ndvi = float(np.nanmax(valid_ndvi))
    else:
        mean_ndvi = float('nan')
        min_ndvi = float('nan')
        max_ndvi = float('nan')

    # Compute per-zone statistics
    zone_stats = {}
    for zone_name in ALL_ZONES:
        zone_mask = zones == zone_name
        count = int(np.sum(zone_mask))
        if valid_pixels > 0:
            percentage = (count / valid_pixels) * 100.0
        else:
            percentage = 0.0
        zone_stats[zone_name] = {
            'count': count,
            'percentage': percentage,
        }

    return {
        'total_pixels': total_pixels,
        'valid_pixels': valid_pixels,
        'nodata_pixels': nodata_pixels,
        'mean_ndvi': mean_ndvi,
        'min_ndvi': min_ndvi,
        'max_ndvi': max_ndvi,
        'zones': zone_stats,
    }


def write_txt_report(stats: dict[str, Any], out_path: str) -> None:
    """
    Write a human-readable text report of NDVI analysis results.

    Generates a formatted report including scene summary statistics,
    zone breakdown with pixel counts and percentages, and alerts
    if stressed and bare soil zones exceed 30% of valid pixels.

    Args:
        stats: Statistics dictionary as returned by compute_stats().
        out_path: File path where the text report will be written.

    Returns:
        None

    Raises:
        OSError: If the output file cannot be written.
    """
    lines = []

    # Header
    lines.append("=" * 60)
    lines.append("CROP HEALTH ANALYSIS REPORT")
    lines.append("NDVI-Based Vegetation Assessment")
    lines.append("=" * 60)
    lines.append("")

    # Scene Summary
    lines.append("SCENE SUMMARY")
    lines.append("-" * 40)
    lines.append(f"Total pixels:      {stats['total_pixels']:,}")
    lines.append(f"Valid pixels:      {stats['valid_pixels']:,}")
    lines.append(f"No-data pixels:    {stats['nodata_pixels']:,}")
    lines.append("")
    lines.append(f"Mean NDVI:         {stats['mean_ndvi']:.4f}")
    lines.append(f"Min NDVI:          {stats['min_ndvi']:.4f}")
    lines.append(f"Max NDVI:          {stats['max_ndvi']:.4f}")
    lines.append("")

    # Zone Breakdown
    lines.append("ZONE BREAKDOWN")
    lines.append("-" * 40)
    lines.append(f"{'Zone':<20} {'Pixels':>12} {'Percentage':>12}")
    lines.append("-" * 44)

    for zone_name in ALL_ZONES:
        zone_data = stats['zones'][zone_name]
        count = zone_data['count']
        pct = zone_data['percentage']
        lines.append(f"{zone_name:<20} {count:>12,} {pct:>11.2f}%")

    lines.append("")

    # Alert check: stressed + bare > 30%
    stressed_pct = stats['zones'][ZONE_STRESSED]['percentage']
    bare_pct = stats['zones'][ZONE_BARE_DRY]['percentage']
    combined_stress = stressed_pct + bare_pct

    if combined_stress > STRESS_ALERT_THRESHOLD:
        lines.append("!" * 60)
        lines.append("ALERT: POTENTIAL CROP STRESS DETECTED")
        lines.append("!" * 60)
        lines.append(f"Stressed/sparse + bare/dry soil = {combined_stress:.2f}%")
        lines.append(f"This exceeds the {STRESS_ALERT_THRESHOLD:.0f}% threshold.")
        lines.append("Recommendation: Investigate field conditions and consider")
        lines.append("irrigation, fertilisation, or pest management interventions.")
        lines.append("")

    # Footer
    lines.append("=" * 60)
    lines.append("End of Report")
    lines.append("=" * 60)

    # Write to file
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))


def write_csv_report(stats: dict[str, Any], out_path: str) -> None:
    """
    Write a CSV report of zone statistics.

    Generates a machine-readable CSV file with columns for zone name,
    pixel count, and percentage of valid pixels.

    Args:
        stats: Statistics dictionary as returned by compute_stats().
        out_path: File path where the CSV report will be written.

    Returns:
        None

    Raises:
        OSError: If the output file cannot be written.
    """
    with open(out_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)

        # Write header row
        writer.writerow(['zone', 'pixel_count', 'percentage'])

        # Write data rows for each zone
        for zone_name in ALL_ZONES:
            zone_data = stats['zones'][zone_name]
            writer.writerow([
                zone_name,
                zone_data['count'],
                f"{zone_data['percentage']:.4f}",
            ])
