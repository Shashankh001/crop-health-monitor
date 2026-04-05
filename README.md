# Crop Health Monitor

A Python-based NDVI (Normalized Difference Vegetation Index) analysis tool for assessing crop and vegetation health using Landsat 7 satellite imagery.

## Overview

This tool processes Landsat 7 Level-2 surface reflectance satellite imagery to generate vegetation health assessments. It computes NDVI values from red and near-infrared (NIR) bands and classifies pixels into meaningful vegetation zones, producing colour-coded maps and statistical reports.

## Features

- **NDVI Computation**: Calculates NDVI from Landsat 7 red (B4) and NIR (B5) bands
- **Zone Classification**: Classifies vegetation into 5 meaningful zones:
  - Dense vegetation (NDVI > 0.6)
  - Moderate crop (NDVI 0.3-0.6)
  - Stressed/sparse vegetation (NDVI 0.1-0.3)
  - Bare/dry soil (NDVI 0.0-0.1)
  - Water/built-up areas (NDVI < 0.0)
- **Visual Outputs**: Generates colour-coded NDVI maps and greyscale band visualisations
- **Statistical Reports**: Produces both human-readable text reports and machine-readable CSV files
- **Stress Alerts**: Automatically flags potential crop stress conditions

## Requirements

- Python 3.10+
- Dependencies:
  - `numpy` - Numerical processing
  - `rasterio` - GeoTIFF file handling
  - `Pillow` - Image generation

## Installation

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install numpy rasterio pillow
   ```

## Usage

### Basic Command

```bash
python main.py --red B4.TIF --nir B5.TIF
```

### With Custom Output Directory

```bash
python main.py --red B4.TIF --nir B5.TIF --output ./my_results
```

### Command-Line Arguments

- `--red` (required): Path to red band GeoTIFF file (Landsat B4, ~670nm)
- `--nir` (required): Path to NIR band GeoTIFF file (Landsat B5, ~800nm)
- `--output` (optional): Output directory for results (default: `./output`)

## Output Files

Each analysis run creates a timestamped subfolder (e.g., `run_20260405_095730`) containing:

### Images
- `ndvi_map.png` - Colour-coded vegetation zone map
- `red_band.png` - Greyscale visualisation of the red band
- `nir_band.png` - Greyscale visualisation of the NIR band

### Reports
- `report.txt` - Human-readable statistical summary with zone breakdown and alerts
- `zones.csv` - Machine-readable CSV file with zone statistics

### Input Copies
- Original input GeoTIFF files (B4.TIF, B5.TIF) are copied to the run folder for organisation

## Example Workflow

```bash
# Run analysis on Landsat 7 bands
python main.py --red LC08_B4.TIF --nir LC08_B5.TIF --output ./crop_analysis

# Check the results
cd output/run_20260405_095730/
# View ndvi_map.png for visual assessment
# Read report.txt for detailed statistics
```

## Understanding the Output

### NDVI Values
- **+1.0 to +0.6**: Dense, healthy vegetation (forests, mature crops)
- **+0.6 to +0.3**: Moderate vegetation (growing crops, grasslands)
- **+0.3 to +0.1**: Stressed or sparse vegetation (poor growth)
- **+0.1 to 0.0**: Bare soil or very dry vegetation
- **0.0 to -1.0**: Water bodies, built-up areas, or non-vegetated surfaces

### Colour Map
- **Dark green**: Dense vegetation
- **Bright green**: Moderate crop health
- **Yellow-orange**: Stressed/sparse vegetation
- **Tan**: Bare/dry soil
- **Blue**: Water/built-up areas
- **Dark grey**: No data

### Stress Alerts
The tool automatically flags potential crop stress if stressed/sparse vegetation and bare/dry soil combined exceed 30% of the valid pixels.

## Module Structure

- `main.py` - Entry point and pipeline orchestration
- `file_loader.py` - GeoTIFF loading and preprocessing
- `ndvi_processor.py` - NDVI computation and zone classification
- `visualiser.py` - Image generation and colour mapping
- `report_writer.py` - Statistical analysis and report generation

## Data Sources

This tool is designed for **Landsat 7 Level-2 surface reflectance** products. Download data from:
- [USGS EarthExplorer](https://earthexplorer.usgs.gov/)
- [NASA Earthdata](https://earthdata.nasa.gov/)

Required bands:
- **B4** (Red): 630-680 nm
- **B5** (NIR): 845-885 nm

## License

This project is provided as-is for educational and research purposes.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests for improvements.
