import argparse
import os
import sys
import rasterio
from pprint import pprint


import os
import rasterio

# this is hella inefficient, fix
def load_bands(scene_folder, band_numbers, meta_bands):
    band_paths = {}
    for band_number in band_numbers:
        for file in os.listdir(scene_folder):
            if file.endswith(f"_B{band_number}.TIF"):  # Assuming the files follow "B{band_number}.TIF" naming convention
                band_paths[band_number] = os.path.join(scene_folder, file)
                break
    for meta_band in meta_bands:
        for file in os.listdir(scene_folder):
            if file.endswith(meta_band):
                band_paths[meta_band] = os.path.join(scene_folder, file)
                break
    return band_paths

def process_landsat_data(input_folder, processing_method, output_path, output_prefix=""):
    # Assuming the processing_method dictates which bands we need
    if processing_method == "surface_temp":
        required_bands = [4, 5, 10]
        meta_bands = ["_EMIS.TIF", "_MTL.json"]
    else:
        print(f"Unsupported processing method: {processing_method}")
        return
    
    for scene_folder in os.listdir(input_folder):
        full_path = os.path.join(input_folder, scene_folder)
        if os.path.isdir(full_path):
            print(f"Processing scene: {scene_folder}")
            band_paths = load_bands(full_path, required_bands, meta_bands)
            # Now you have the paths to the required band files
            # You can load them with rasterio and proceed with your calculations
            pprint(band_paths)

            # Example of loading a band with rasterio
            # for band_number, band_path in band_paths.items():
            #     with rasterio.open(band_path) as src:
            #         band_data = src.read(1)  # Reads the first (and only) band
            #         # Perform processing with band_data here
            #         print(f"Loaded band {band_number} from {band_path}")

            # Place your processing code here, and save output as needed




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
