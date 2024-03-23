import json
import numpy as np
import rasterio
from rasterio.warp import reproject, Resampling


def calc_surface_temp(scene, celsius=False, reprojection_config=False):
    print("reprojection", reprojection_config)

    required_bands = ["B10", "EMIS", "MTL"]
    all_bands_exist = all(band in scene for band in required_bands)
    if not all_bands_exist:
        raise Exception(
            f"Required bands are {required_bands}, only {scene.keys()} were provided"
        )
    path_band_10 = scene["B10"]
    path_mtl = scene["MTL"]

    with rasterio.open(path_band_10) as src:
        # Read the band data
        b10 = src.read(1)
        meta = src.meta.copy()

    # Load the MTL data
    with open(path_mtl, "r") as f:
        mtl = json.load(f)

    # Perform the temperature conversion calculation
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
    celsius_scalar = -272.15 if celsius else 0
    converted_b10 = multiplier * b10 + coefficient + celsius_scalar

    # Reproject if required
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
