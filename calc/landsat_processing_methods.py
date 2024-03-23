import json
import rasterio
from rasterio.windows import from_bounds

def calc_surface_temp(scene, celsius=False, window=False, bounds=False):
    required_bands = ["B10", "EMIS", "MTL"]
    all_bands_exist = all(band in scene for band in required_bands)
    if not all_bands_exist:
        raise Exception(
            f"Required bands are {required_bands}, only {scene.keys()} were provided"
        )
    path_band_10 = scene["B10"]
    path_mtl = scene["MTL"]

    with rasterio.open(path_band_10) as src:
        transform = src.transform
        new_window = from_bounds(
            bounds[0], bounds[1], bounds[2], bounds[3], transform=transform
        ) if bounds else None
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
    new_meta = meta.copy()
    new_meta.update({
        "compress": "deflate",
        "height": new_band.shape[0],
        "width": new_band.shape[1],

        })
    return {
        "band": new_band,
        "meta": new_meta,
        "mtl": mtl,
        "bounds": bounds,
        "resolution": resolution,
    }