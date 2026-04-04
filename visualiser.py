"""
Visualisation module for NDVI maps and band imagery.

This module provides functions to create colour-mapped NDVI visualisations
and normalised greyscale band images, and to save them as PNG files.
"""

import os
import numpy as np
from PIL import Image


# RGB colour map for NDVI zones (R, G, B)
COLOUR_MAP = {
    "dense vegetation": (0, 100, 10),
    "moderate crop": (60, 180, 30),
    "stressed/sparse": (230, 180, 30),
    "bare/dry soil": (190, 150, 80),
    "water/built-up": (30, 80, 180),
    "nodata": (15, 15, 15),
}

# Zone thresholds (duplicated here to avoid circular imports)
DENSE_VEG_THRESHOLD = 0.6
MODERATE_CROP_THRESHOLD = 0.3
STRESSED_SPARSE_THRESHOLD = 0.1
BARE_SOIL_THRESHOLD = 0.0


def apply_colourmap(ndvi: np.ndarray) -> np.ndarray:
    """
    Apply a colour map to NDVI values to create an RGB image.

    Maps NDVI values to colours based on vegetation zone thresholds:
        > 0.6   : dark green (dense vegetation)
        0.3-0.6 : bright green (moderate crop)
        0.1-0.3 : yellow-orange (stressed/sparse)
        0.0-0.1 : tan (bare/dry soil)
        < 0.0   : blue (water/built-up)
        NaN     : dark grey (nodata)

    Args:
        ndvi: 2D numpy array of NDVI values (float32), with NaN for no-data.

    Returns:
        A 3D numpy array of shape (H, W, 3) with uint8 RGB values.
    """
    height, width = ndvi.shape
    rgb = np.zeros((height, width, 3), dtype=np.uint8)

    # Create boolean masks for each zone
    nodata_mask = np.isnan(ndvi)
    dense_mask = ndvi > DENSE_VEG_THRESHOLD
    moderate_mask = (ndvi > MODERATE_CROP_THRESHOLD) & (ndvi <= DENSE_VEG_THRESHOLD)
    stressed_mask = (ndvi > STRESSED_SPARSE_THRESHOLD) & (ndvi <= MODERATE_CROP_THRESHOLD)
    bare_mask = (ndvi >= BARE_SOIL_THRESHOLD) & (ndvi <= STRESSED_SPARSE_THRESHOLD)
    water_mask = (ndvi < BARE_SOIL_THRESHOLD) & ~nodata_mask

    # Apply colours using boolean indexing
    rgb[dense_mask] = COLOUR_MAP["dense vegetation"]
    rgb[moderate_mask] = COLOUR_MAP["moderate crop"]
    rgb[stressed_mask] = COLOUR_MAP["stressed/sparse"]
    rgb[bare_mask] = COLOUR_MAP["bare/dry soil"]
    rgb[water_mask] = COLOUR_MAP["water/built-up"]
    rgb[nodata_mask] = COLOUR_MAP["nodata"]

    return rgb


def normalise_band(band: np.ndarray) -> np.ndarray:
    """
    Normalise a band array to uint8 using percentile stretch.

    Applies a 2nd to 98th percentile stretch to enhance contrast,
    ignoring NaN values. Values below p2 are clipped to 0, values
    above p98 are clipped to 255.

    Args:
        band: 2D numpy array of band values (float32), with NaN for no-data.

    Returns:
        A 2D numpy array of uint8 values (0-255) suitable for greyscale display.
        NaN pixels are mapped to 0 (black).
    """
    # Get valid (non-NaN) pixels for percentile calculation
    valid_pixels = band[~np.isnan(band)]

    if len(valid_pixels) == 0:
        # All pixels are NaN, return black image
        return np.zeros(band.shape, dtype=np.uint8)

    # Calculate percentiles for contrast stretch
    p2 = np.percentile(valid_pixels, 2)
    p98 = np.percentile(valid_pixels, 98)

    # Avoid division by zero if p2 == p98
    if p98 == p2:
        # All valid pixels have the same value
        normalised = np.where(np.isnan(band), 0, 128).astype(np.uint8)
        return normalised

    # Apply linear stretch: map [p2, p98] to [0, 255]
    normalised = (band - p2) / (p98 - p2) * 255.0

    # Clip to valid range
    normalised = np.clip(normalised, 0, 255)

    # Handle NaN pixels (set to 0 / black)
    normalised = np.where(np.isnan(band), 0, normalised)

    return normalised.astype(np.uint8)


def save_outputs(
    ndvi: np.ndarray,
    red: np.ndarray,
    nir: np.ndarray,
    out_dir: str
) -> None:
    """
    Save NDVI colour map and band greyscale images to PNG files.

    Creates three output images:
        - ndvi_map.png: Colour-coded NDVI vegetation zone map
        - red_band.png: Greyscale visualisation of the red band
        - nir_band.png: Greyscale visualisation of the NIR band

    Args:
        ndvi: 2D numpy array of NDVI values (float32).
        red: 2D numpy array of red band reflectance values (float32).
        nir: 2D numpy array of NIR band reflectance values (float32).
        out_dir: Directory path where output images will be saved.
                 Directory must exist.

    Returns:
        None

    Raises:
        OSError: If the output directory does not exist or is not writable.
    """
    # Generate colour-mapped NDVI image
    ndvi_rgb = apply_colourmap(ndvi)
    ndvi_image = Image.fromarray(ndvi_rgb, mode='RGB')
    ndvi_image.save(os.path.join(out_dir, 'ndvi_map.png'))

    # Generate greyscale red band image
    red_grey = normalise_band(red)
    red_image = Image.fromarray(red_grey, mode='L')
    red_image.save(os.path.join(out_dir, 'red_band.png'))

    # Generate greyscale NIR band image
    nir_grey = normalise_band(nir)
    nir_image = Image.fromarray(nir_grey, mode='L')
    nir_image.save(os.path.join(out_dir, 'nir_band.png'))
