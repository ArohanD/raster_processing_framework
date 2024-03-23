import numpy as np
from datetime import datetime
from affine import Affine

def average_bands(scene_list):
    min_x, min_y, max_x, max_y = (
        float("inf"),
        float("inf"),
        float("-inf"),
        float("-inf"),
    )

    band_sum = None
    for scene in scene_list:
        band, meta, bounds, resolution = (
            scene["band"],
            scene["meta"],
            scene["bounds"],
            scene["resolution"],
        )
        if band_sum is None:
            band_sum = np.zeros_like(band)
        band_sum += band
        min_x = min(min_x, bounds.left)
        min_y = min(min_y, bounds.bottom)
        max_x = max(max_x, bounds.right)
        max_y = max(max_y, bounds.top)
    # Assuming resolutions are all the same, which they are (30 x 30)
    res_x, res_y = scene_list[0]["resolution"]

    output_transform = Affine(res_x, 0, min_x, 0, -res_y, max_y)

    # Calculate the width and height of the output raster
    output_width = int((max_x - min_x) / res_x)
    output_height = int((max_y - min_y) / abs(res_y))
    bands_average = band_sum / len(scene_list)
    new_meta = meta.copy()
    new_meta.update(
        {
            "transform": output_transform,
            "width": output_width,
            "height": output_height,
            "compress": "deflate",
        }
    )
    return {"band": bands_average, "meta": new_meta}

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