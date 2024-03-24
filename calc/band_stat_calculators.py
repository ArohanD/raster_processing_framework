import numpy as np

CELSIUS_SCALAR = -272.15


def surface_temp_stats(band, meta, celsius=False):
    celsius_scalar = CELSIUS_SCALAR if celsius else 0
    temp_min = (
        meta["LEVEL2_SURFACE_TEMPERATURE_PARAMETERS"]["TEMPERATURE_MINIMUM_BAND_ST_B10"]
        + celsius_scalar
    )
    temp_max = (
        meta["LEVEL2_SURFACE_TEMPERATURE_PARAMETERS"]["TEMPERATURE_MAXIMUM_BAND_ST_B10"]
        + celsius_scalar
    )
    filter_mask = (band != meta["nodata"]) & (band > temp_min) & (band < temp_max)
    filtered_band = band[filter_mask]
    return {
        "mean": np.mean(filtered_band),
        "median": np.median(filtered_band),
        "std": np.std(filtered_band),
        "min": np.min(filtered_band),
        "max": np.max(filtered_band),
    }

def ndvi_stats(band, meta):
    filter_mask = (band != meta["nodata"]) & (band > -1) & (band < 1)
    filtered_band = band[filter_mask]
    return {
        "mean": np.mean(filtered_band),
        "median": np.median(filtered_band),
        "std": np.std(filtered_band),
        "min": -1,
        "max": 1,
    }
