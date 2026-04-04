"""
File loader module for Landsat 7 GeoTIFF band data.

This module provides functions to load and preprocess Landsat 7 Level-2
surface reflectance bands from GeoTIFF files, applying the appropriate
scale factor and handling no-data values.
"""

import numpy as np
import rasterio


# Landsat Level-2 surface reflectance scale factor
SCALE_FACTOR = 0.0000275
OFFSET = -0.2
NODATA_SENTINEL = 0


def load_band(filepath: str) -> np.ndarray:
    """
    Load a single Landsat band from a GeoTIFF file.

    Opens the specified GeoTIFF file, reads band 1, applies the Landsat
    Level-2 scale factor (pixel * 0.0000275 - 0.2), and masks no-data
    pixels (value == 0) as NaN.

    Args:
        filepath: Path to the GeoTIFF file containing the band data.

    Returns:
        A 2D numpy array of float32 values representing surface reflectance.
        No-data pixels are represented as np.nan.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        rasterio.errors.RasterioIOError: If the file cannot be opened as a raster.
    """
    with rasterio.open(filepath) as src:
        # Read band 1 as float32 for precision in calculations
        band_data = src.read(1).astype(np.float32)

    # Create mask for no-data pixels (sentinel value == 0)
    nodata_mask = band_data == NODATA_SENTINEL

    # Apply Landsat Level-2 scale factor: DN * 0.0000275 - 0.2
    band_data = band_data * SCALE_FACTOR + OFFSET

    # Mask no-data pixels as NaN
    band_data[nodata_mask] = np.nan

    return band_data


def load_bands(red_path: str, nir_path: str) -> tuple[np.ndarray, np.ndarray]:
    """
    Load red and NIR bands from GeoTIFF files.

    Convenience function that loads both the red (B4) and near-infrared (B5)
    bands required for NDVI calculation.

    Args:
        red_path: Path to the red band GeoTIFF file (typically B4.TIF).
        nir_path: Path to the NIR band GeoTIFF file (typically B5.TIF).

    Returns:
        A tuple of two 2D numpy arrays (red, nir), each containing float32
        surface reflectance values with no-data pixels as np.nan.

    Raises:
        FileNotFoundError: If either specified file does not exist.
        rasterio.errors.RasterioIOError: If either file cannot be opened as a raster.
        ValueError: If the two bands have different shapes.
    """
    red_band = load_band(red_path)
    nir_band = load_band(nir_path)

    # Validate that both bands have the same dimensions
    if red_band.shape != nir_band.shape:
        raise ValueError(
            f"Band shape mismatch: red {red_band.shape} vs NIR {nir_band.shape}"
        )

    return red_band, nir_band
