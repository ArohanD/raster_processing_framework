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

def print_num_scenes_by_year(scenes_by_year):
    for year in scenes_by_year:
        print(f"{year}: {len(scenes_by_year[year])} scenes")


def average_by_year(processed_scene_library):
    print("Aggregating processed bands by year...")

    scenes_by_year = {}

    for scene in processed_scene_library:
        date_acquired = processed_scene_library[scene]["mtl"]["LANDSAT_METADATA_FILE"][
            "IMAGE_ATTRIBUTES"
        ]["DATE_ACQUIRED"]
        date_obj = datetime.strptime(date_acquired, "%Y-%m-%d")
        year = date_obj.year
        if year in scenes_by_year:
            scenes_by_year[year].append(processed_scene_library[scene])
        else:
            scenes_by_year[year] = [processed_scene_library[scene]]

    print_num_scenes_by_year(scenes_by_year)
    averages_by_year = {}
    for year in scenes_by_year:
        averages_by_year[f"{year}_average"] = average_bands(scenes_by_year[year])

    return averages_by_year

def average_all_data(scene_library):
    print("Averaging ALL processed bands into an average...")

    scenes = list(scene_library.values())
    averages = average_bands(scenes)

    return {"averaged_ST_entire_dataset": averages}
