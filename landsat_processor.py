import argparse
import os
import sys
import rasterio
import json
from pprint import pprint
import numpy as np

import os
import rasterio


def calc_surface_temp(scene, celsius=False):
    required_bands = ["B10", "EMIS", "MTL"]
    all_bands_exist = all(band in scene for band in required_bands)
    if not all_bands_exist:
        raise Exception(
            f"Required bands are {required_bands}, only {scene.keys()} were provided"
        )
    path_band_10 = scene["B10"]
    path_mtl = scene["MTL"]

    with rasterio.open(path_band_10) as src:
        b10 = src.read(1)
        meta = src.meta

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
        'compress': 'deflate'
    })
    return {"band": new_band, "meta": new_meta}


process_dict = {
    "surface_temp": calc_surface_temp,
    "surface_temp_celsius": lambda scene, celsius=True: calc_surface_temp(
        scene, celsius
    ),
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
    for scene_key in output_library:
        current_scene = output_library[scene_key]
        modified_scene_key = scene_key.replace("./landsat", "", 1)
        file_path = f"{output_path}{modified_scene_key}_{output_suffix}.tif"
        print(file_path)
        with rasterio.open(file_path, "w", **current_scene["meta"]) as destination:
            band_data = current_scene["band"]
            destination.write(band_data, 1)
            
            # Mask no-data values if specified, else use the data as is
            if 'nodata' in current_scene['meta']:
                mask = band_data != current_scene['meta']['nodata']
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
            destination.update_tags(1, STATISTICS_MINIMUM=stats_minimum, STATISTICS_MAXIMUM=stats_maximum, STATISTICS_MEAN=stats_mean, STATISTICS_STDDEV=stats_stddev, STATISTICS_VALID_PERCENT=stats_valid_percent)



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

    output_library = {}
    for scene in scene_library:
        output_library[scene] = process_dict[processing_method](scene_library[scene])

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
