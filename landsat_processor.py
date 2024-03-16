import argparse
import os
import sys
import rasterio
from pprint import pprint


import os
import rasterio


def calc_surface_temp(scene):
    required_bands = ["B10", "EMIS", "MTL"]
    all_bands_exist = all(band in scene for band in required_bands)
    if not all_bands_exist:
        raise Exception(f"Required bands are {required_bands}, only {scene.keys()} were provided")
    pprint(scene)


process_dict = {"surface_temp": calc_surface_temp}


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


def process_landsat_data(
    input_folder, processing_method, output_path, output_prefix=""
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
        "-p",
        "--prefix",
        dest="output_prefix",
        help="Prefix for the output GeoTiffs",
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
        args.input_folder, args.processing_method, args.output_path, args.output_prefix
    )


if __name__ == "__main__":
    main()
