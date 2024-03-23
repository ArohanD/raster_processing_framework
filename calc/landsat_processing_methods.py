import json
import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
import numpy as np


def calc_surface_temp(
    scene, celsius=False, window=False, bounds=False, reprojection_config=False
):
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
        # If reprojection_config is provided, prepare for reprojection
        if reprojection_config:
            # Define destination array for the reprojected data
            dest_array = np.empty(
                (reprojection_config["height"], reprojection_config["width"]),
                dtype=src.meta["dtype"],
            )
            reproject(
                source=rasterio.band(src, 1),
                destination=dest_array,
                src_transform=src.transform,
                src_crs=src.crs,
                dst_transform=reprojection_config["transform"],
                dst_crs=reprojection_config["crs"],
                resampling=Resampling.bilinear,
            )
            # Update meta with the reprojection config
            meta = src.meta.copy()
            meta.update(
                {
                    "crs": reprojection_config["crs"],
                    "transform": reprojection_config["transform"],
                    "width": reprojection_config["width"],
                    "height": reprojection_config["height"],
                }
            )
            b10 = dest_array
        else:
            # Process without reprojection
            new_window = (
                from_bounds(
                    bounds[0], bounds[1], bounds[2], bounds[3], transform=src.transform
                )
                if bounds
                else None
            )
            b10 = src.read(1, window=new_window) if window else src.read(1)
            meta = src.meta
            bounds = src.bounds
            resolution = src.res

    with open(path_mtl, "r") as f:
        mtl = json.load(f)

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
    new_band = multiplier * b10 + coefficient + celsius_scalar

    # Update metadata for output
    new_meta = meta.copy()
    new_meta.update(
        {
            "compress": "deflate",
            "height": new_band.shape[0],
            "width": new_band.shape[1],
        }
    )

    import ipdb; ipdb.set_trace()

    return {
        "band": new_band,
        "meta": new_meta,
        "mtl": mtl,
        "bounds": bounds,
        "resolution": resolution,
    }
