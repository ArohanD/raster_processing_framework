import numpy as np
from datetime import datetime

def average_bands(scene_list):
    band_sum = None
    for scene in scene_list:
        band, meta = (
            scene["band"],
            scene["meta"],
        )
        if band_sum is None:
            band_sum = np.zeros_like(band)
        band_sum += band

    bands_average = band_sum / len(scene_list)
    return {"band": bands_average, "meta": meta.copy()}


def average_ST_by_year(st_scene_library):
    print("Aggregating processed bands by year...")

    scenes_by_year = {}

    for scene in st_scene_library:
        date_acquired = st_scene_library[scene]["mtl"]["LANDSAT_METADATA_FILE"][
            "LEVEL2_PROCESSING_RECORD"
        ]["DATE_PRODUCT_GENERATED"]
        date_obj = datetime.strptime(date_acquired, "%Y-%m-%dT%H:%M:%SZ")
        year = date_obj.year
        if year in scenes_by_year:
            scenes_by_year[year].append(st_scene_library[scene])
        else:
            scenes_by_year[year] = [st_scene_library[scene]]

    averages_by_year = {}
    for year in scenes_by_year:
        averages_by_year[f"averaged_ST_{year}"] = average_bands(scenes_by_year[year])

    return averages_by_year
