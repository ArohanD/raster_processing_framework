import json
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling
from .band_stat_calculators import CELSIUS_SCALAR

def calc_surface_temp(scene, celsius=False, reprojection_config=False):
    print(f"Calculating surface temperature for {scene['B10']}...")

    required_bands = ["B10", "MTL"]
    all_bands_exist = all(band in scene for band in required_bands)
    if not all_bands_exist:
        raise Exception(
            f"Required bands are {required_bands}, only {scene.keys()} were provided"
        )
    path_band_10 = scene["B10"]
    path_mtl = scene["MTL"]

    with rasterio.open(path_band_10) as src:
        b10 = src.read(1)
        meta = src.meta.copy()

    with open(path_mtl, "r") as f:
        mtl = json.load(f)

    # Perform a temperature conversion calculation using metadata
    multiplier = float(
        mtl["LANDSAT_METADATA_FILE"]["LEVEL2_SURFACE_TEMPERATURE_PARAMETERS"][
            "TEMPERATURE_MULT_BAND_ST_B10"
        ]
    )
    coefficient = float(
        mtl["LANDSAT_METADATA_FILE"]["LEVEL2_SURFACE_TEMPERATURE_PARAMETERS"][
            "TEMPERATURE_ADD_BAND_ST_B10"
        ]
    )
    print(CELSIUS_SCALAR)
    celsius_scalar = CELSIUS_SCALAR if celsius else 0
    converted_b10 = multiplier * b10 + coefficient + celsius_scalar

    # Reproject if doing bulk processing
    if reprojection_config:
        dest_array = np.empty(
            (reprojection_config["height"], reprojection_config["width"]),
            dtype=converted_b10.dtype,
        )
        reproject(
            source=converted_b10,
            destination=dest_array,
            src_transform=meta["transform"],
            src_crs=meta["crs"],
            dst_transform=reprojection_config["transform"],
            dst_crs=reprojection_config["crs"],
            resampling=Resampling.bilinear,
        )
        new_band = dest_array
        # Update meta with the reprojection config
        new_meta = meta.copy()
        new_meta.update(
            {
                "crs": reprojection_config["crs"],
                "transform": reprojection_config["transform"],
                "width": reprojection_config["width"],
                "height": reprojection_config["height"],
                "compress": "deflate",
            }
        )
    else:
        new_band = converted_b10
        new_meta = meta

    return {
        "band": new_band,
        "meta": new_meta,
        "mtl": mtl,
    }




def calc_ndvi(scene, reprojection_config=False):
    print(f"Calculating NDVI using {scene['B4']} and {scene['B5']}...")

    required_bands = ["B4", "B5", "MTL"]
    all_bands_exist = all(band in scene for band in required_bands)
    if not all_bands_exist:
        raise Exception(
            f"Required bands are {required_bands}, only {scene.keys()} were provided"
        )

    path_band_4 = scene["B4"]
    path_band_5 = scene["B5"]
    path_mtl = scene["MTL"]

    b4, b5, meta = None, None, None

    with rasterio.open(path_band_4) as src:
        b4 = src.read(1)
        meta = src.meta.copy()
        nodata = src.nodatavals[0]  # Assuming nodata is the same for both bands

    with rasterio.open(path_band_5) as src:
        b5 = src.read(1)

    with open(path_mtl, "r") as f:
        mtl = json.load(f)

    # Calculate NDVI with safe division and nodata handling
    np.seterr(divide="ignore", invalid="ignore")
    ndvi = np.where((b5 + b4) == 0, nodata, (b5 - b4) / (b5 + b4))
    ndvi = ndvi.astype(np.float32)  # Ensure the output is float32 for NDVI values

    if reprojection_config:
        # Prepare a destination array for reprojected NDVI data
        dest_array = np.empty(
            (reprojection_config["height"], reprojection_config["width"]),
            dtype=ndvi.dtype,
        )

        reproject(
            source=ndvi,
            destination=dest_array,
            src_transform=meta["transform"],
            src_crs=meta["crs"],
            dst_transform=reprojection_config["transform"],
            dst_crs=reprojection_config["crs"],
            resampling=Resampling.bilinear,
        )
        new_band = dest_array

        new_meta = meta.copy()
        new_meta.update(
            {
                "crs": reprojection_config["crs"],
                "transform": reprojection_config["transform"],
                "width": reprojection_config["width"],
                "height": reprojection_config["height"],
                "compress": "deflate",
                "dtype": "float32",
                "nodata": nodata,
            }
        )
    else:
        new_band = ndvi
        new_meta = meta
        new_meta.update({"dtype": "float32", "nodata": nodata})

    return {
        "band": new_band,
        "meta": new_meta,
        "mtl": mtl,
    }
