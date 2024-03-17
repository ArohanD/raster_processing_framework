import argparse
import rasterio
import numpy as np

def compare_rasters(original_path, output_path):
    with rasterio.open(original_path) as orig, rasterio.open(output_path) as rast_out:
        orig_data = orig.read()  # Read all bands
        rast_out_data = rast_out.read()  # Read all bands

    # Check if all data points are exactly the same across all bands
    data_matches = np.array_equal(orig_data, rast_out_data)
    print(f"Data matches across all bands: {data_matches}")

def main():
    parser = argparse.ArgumentParser(description="Compare pixel values of two raster files.")
    parser.add_argument('original', help="Path to the original raster file")
    parser.add_argument('output', help="Path to the output raster file")

    args = parser.parse_args()

    compare_rasters(args.original, args.output)

if __name__ == "__main__":
    main()
