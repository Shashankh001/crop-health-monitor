"""
NDVI processor module for vegetation index computation and classification.

This module provides functions to compute the Normalized Difference Vegetation
Index (NDVI) from red and NIR bands, and classify the results into meaningful
vegetation/land cover zones.
"""

import numpy as np


# Zone threshold constants
DENSE_VEG_THRESHOLD = 0.6
MODERATE_CROP_THRESHOLD = 0.3
STRESSED_SPARSE_THRESHOLD = 0.1
BARE_SOIL_THRESHOLD = 0.0

# Zone labels
ZONE_DENSE_VEG = "dense vegetation"
ZONE_MODERATE = "moderate crop"
ZONE_STRESSED = "stressed/sparse"
ZONE_BARE_DRY = "bare/dry soil"
ZONE_WATER_BUILT = "water/built-up"
ZONE_NODATA = "nodata"


def compute_ndvi(red: np.ndarray, nir: np.ndarray) -> np.ndarray:
    """
    Compute the Normalized Difference Vegetation Index (NDVI).

    NDVI is calculated as (NIR - Red) / (NIR + Red), which quantifies
    vegetation greenness. The result ranges from -1.0 to +1.0, where
    higher values indicate denser, healthier vegetation.

    Args:
        red: 2D numpy array of red band reflectance values (float32).
             No-data pixels should be represented as np.nan.
        nir: 2D numpy array of NIR band reflectance values (float32).
             No-data pixels should be represented as np.nan.

    Returns:
        A 2D numpy array of NDVI values clipped to [-1.0, 1.0].
        Pixels where both inputs are NaN remain NaN.
        Pixels where (NIR + Red) == 0 are set to NaN (division guard).

    Raises:
        ValueError: If red and nir arrays have different shapes.
    """
    if red.shape != nir.shape:
        raise ValueError(
            f"Array shape mismatch: red {red.shape} vs NIR {nir.shape}"
        )

    # Create output array initialized with NaN
    ndvi = np.full(red.shape, np.nan, dtype=np.float32)

    # Compute sum for denominator
    denominator = nir + red

    # Find valid pixels (both bands have data and denominator is non-zero)
    valid_mask = ~(np.isnan(red) | np.isnan(nir)) & (denominator != 0)

    # Compute NDVI with divide-by-zero protection
    with np.errstate(divide='ignore', invalid='ignore'):
        ndvi[valid_mask] = (nir[valid_mask] - red[valid_mask]) / denominator[valid_mask]

    # Clip to valid NDVI range [-1.0, 1.0]
    ndvi = np.clip(ndvi, -1.0, 1.0)

    return ndvi


def classify_zones(ndvi: np.ndarray) -> np.ndarray:
    """
    Classify NDVI values into vegetation/land cover zones.

    Applies threshold-based classification to categorize each pixel
    into one of six zones based on its NDVI value:
        > 0.6   : "dense vegetation"
        0.3-0.6 : "moderate crop"
        0.1-0.3 : "stressed/sparse"
        0.0-0.1 : "bare/dry soil"
        < 0.0   : "water/built-up"
        NaN     : "nodata"

    Args:
        ndvi: 2D numpy array of NDVI values (float32).
              No-data pixels should be represented as np.nan.

    Returns:
        A 2D numpy array of string labels (dtype=object) with the same
        shape as the input, where each pixel is classified into a zone.
    """
    # Define conditions in order of evaluation
    # Note: np.select evaluates conditions in order, first True wins
    conditions = [
        np.isnan(ndvi),                                    # nodata (check first)
        ndvi > DENSE_VEG_THRESHOLD,                        # > 0.6
        (ndvi > MODERATE_CROP_THRESHOLD) & (ndvi <= DENSE_VEG_THRESHOLD),    # 0.3-0.6
        (ndvi > STRESSED_SPARSE_THRESHOLD) & (ndvi <= MODERATE_CROP_THRESHOLD),  # 0.1-0.3
        (ndvi >= BARE_SOIL_THRESHOLD) & (ndvi <= STRESSED_SPARSE_THRESHOLD),     # 0.0-0.1
        ndvi < BARE_SOIL_THRESHOLD,                        # < 0.0
    ]

    choices = [
        ZONE_NODATA,
        ZONE_DENSE_VEG,
        ZONE_MODERATE,
        ZONE_STRESSED,
        ZONE_BARE_DRY,
        ZONE_WATER_BUILT,
    ]

    # Use np.select for vectorized conditional assignment
    zones = np.select(conditions, choices, default=ZONE_NODATA)

    return zones
