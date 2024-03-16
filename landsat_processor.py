import argparse
import os
import sys


def process_landsat_data(input_folder, processing_method, output_path, output_prefix):
    # Placeholder for the processing function
    print(
        f"Processing scenes in {input_folder} using {processing_method}, output will be saved in {output_path} with prefix {output_prefix}"
    )
    # TODO: Implement the processing functionality here


def main():
    parser = argparse.ArgumentParser(description="Process Landsat data.")
    parser.add_argument(
        "input_folder", help="Folder containing folders of Landsat scenes"
    )
    parser.add_argument(
        "processing_method", help="Processing methodology (e.g., surface temp, NDVI)"
    )
    parser.add_argument("output_path", help="Path where the output files will be saved")
    parser.add_argument("output_prefix", help="Prefix for the output GeoTiffs")

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
