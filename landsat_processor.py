import argparse
import json
import os
import sys
from datetime import datetime
from pprint import pprint

import numpy as np
import rasterio
from affine import Affine
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


process_dict = {
    "surface_temp": {"folder_process": calc_surface_temp, "bulk_process": None},
    "surface_temp_celsius": {
        "folder_process": lambda scene, celsius=True, window=None, bounds=None: calc_surface_temp(
            scene, celsius, window, bounds
        ),
        "bulk_process": None,
    },
    "averaged_surface_temp_celsius": {
        "folder_process": lambda scene, celsius=True, window=None, bounds=None: calc_surface_temp(
            scene, celsius, window, bounds
        ),
        "bulk_process": average_ST_by_year,
    },
}


def load_bands(scene_folder, band_numbers, meta_bands):
    band_paths = {}
    fileTails = [f"_B{band_number}.TIF" for band_number in band_numbers] + meta_bands
    for file in os.listdir(scene_folder):
        for tail in fileTails:
            if file.endswith(tail):
                band_name = tail.replace("_", "").split(".")[0]
                if band_name in band_paths:
                    print(
                        f"WARNING: Multiple files found in {scene_folder} ending with {tail}"
                    )
                else:
                    band_paths[band_name] = os.path.join(scene_folder, file)
    return band_paths


def write_outputs(output_path, output_suffix, output_library):
    print("Writing output files...")
    print(f"Output path: {output_path}")
    for scene_key in output_library:
        current_scene = output_library[scene_key]
        modified_scene_key = scene_key.replace("./landsat", "", 1) if scene_key.startswith("./landsat") else f"/{scene_key}"
        file_path = f"{output_path}{modified_scene_key}_{output_suffix}.tif"
        print(f"Writing {file_path}")
        with rasterio.open(file_path, "w", **current_scene["meta"]) as destination:
            band_data = current_scene["band"]
            destination.write(band_data, 1)

            # Mask no-data values if specified, else use the data as is
            if "nodata" in current_scene["meta"]:
                mask = band_data != current_scene["meta"]["nodata"]
                valid_data = band_data[mask]
            else:
                valid_data = band_data

            # Compute statistics
            stats_minimum = np.min(valid_data)
            stats_maximum = np.max(valid_data)
            stats_mean = np.mean(valid_data)
            stats_stddev = np.std(valid_data)
            stats_valid_percent = 100.0 * np.count_nonzero(valid_data) / valid_data.size

            # Update metadata with statistics for the band
            destination.update_tags(
                1,
                STATISTICS_MINIMUM=stats_minimum,
                STATISTICS_MAXIMUM=stats_maximum,
                STATISTICS_MEAN=stats_mean,
                STATISTICS_STDDEV=stats_stddev,
                STATISTICS_VALID_PERCENT=stats_valid_percent,
            )


def get_common_window(scene_library):
    # Initialize bounds to the first raster's bounds
    first_scene_key = list(scene_library.keys())[0]
    with rasterio.open(scene_library[first_scene_key]["B10"]) as src:
        min_x, min_y, max_x, max_y = src.bounds

    # Update bounds based on the intersection of all raster bounds
    for scene_key in list(scene_library.keys())[1:]:
        with rasterio.open(scene_library[scene_key]["B10"]) as src:
            b = src.bounds
            min_x = max(min_x, b.left)
            max_x = min(max_x, b.right)
            min_y = max(min_y, b.bottom)
            max_y = min(max_y, b.top)

    # Calculate the window of overlap in pixel coordinates
    overlap_window = from_bounds(
        min_x,
        min_y,
        max_x,
        max_y,
        transform=rasterio.Affine(30.0, 0.0, min_x, 0.0, -30.0, max_y),
    )
    return {"window": overlap_window, "bounds": (min_x, min_y, max_x, max_y)}


def process_landsat_data(
    input_folder, processing_method, output_path, output_suffix=""
):
    if processing_method not in process_dict:
        raise Exception(f"Unsupported processing method: {processing_method}")
    scene_library = {}
    required_bands = [1, 2, 3, 4, 5, 6, 7, 10]
    meta_bands = ["_EMIS.TIF", "_MTL.json"]

    for scene_folder in os.listdir(input_folder):
        full_path = os.path.join(input_folder, scene_folder)
        if os.path.isdir(full_path):
            print(f"Processing scene: {scene_folder}")
            band_paths = load_bands(full_path, required_bands, meta_bands)
            scene_library[full_path] = band_paths

    processed_scene_library = {}
    run_windowed = bool(process_dict[processing_method]["bulk_process"])
    if run_windowed:
        window, bounds = (
            get_common_window(scene_library)["window"],
            get_common_window(scene_library)["bounds"],
        )
    for scene in scene_library:
        processed_scene_library[scene] = process_dict[processing_method][
            "folder_process"
        ](
            scene_library[scene],
            window=(window if run_windowed else None),
            bounds=(bounds if run_windowed else None),
        )

    output_library = (
        process_dict[processing_method]["bulk_process"](processed_scene_library)
        if process_dict[processing_method]["bulk_process"]
        else processed_scene_library
    )

    write_outputs(output_path, output_suffix, output_library)


def main():
    parser = argparse.ArgumentParser(description="Process Landsat data.")
    parser.add_argument(
        "input_folder", help="Folder containing folders of Landsat scenes"
    )
    parser.add_argument(
        "processing_method", help="Processing methodology (e.g., surface temp, NDVI)"
    )
    parser.add_argument("output_path", help="Path where the output files will be saved")
    parser.add_argument(
        "-s",
        "--suffix",
        dest="output_suffix",
        help="Suffix for the output GeoTiffs",
        default="",
    )

    args = parser.parse_args()

    # Verify the input folder exists
    if not os.path.isdir(args.input_folder):
        print(f"Error: The input folder {args.input_folder} does not exist.")
        sys.exit(1)

    # Create output path if it doesn't exist
    if not os.path.exists(args.output_path):
        os.makedirs(args.output_path)

    process_landsat_data(
        args.input_folder, args.processing_method, args.output_path, args.output_suffix
    )


if __name__ == "__main__":
    main()
