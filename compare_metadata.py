import argparse
import rasterio

def compare_metadata(original_path, output_path):
    with rasterio.open(original_path) as orig, rasterio.open(output_path) as out:
        orig_meta = orig.meta
        out_meta = out.meta

        # Compare main metadata
        print("Comparing main metadata...")
        for key in orig_meta:
            if orig_meta[key] != out_meta.get(key, None):
                print(f"Discrepancy found in '{key}':")
                print(f"  Original: {orig_meta[key]}")
                print(f"  Output: {out_meta.get(key, None)}")

        # Compare band-specific metadata (like nodata values, scales, and offsets)
        print("\nComparing band-specific metadata...")
        for i in range(1, orig_meta['count'] + 1):
            orig_band_meta = orig.tags(i)
            out_band_meta = out.tags(i)
            for key in orig_band_meta:
                if orig_band_meta[key] != out_band_meta.get(key, None):
                    print(f"Discrepancy found in band {i} for '{key}':")
                    print(f"  Original: {orig_band_meta[key]}")
                    print(f"  Output: {out_band_meta.get(key, None)}")

        # Compare color interpretation
        print("\nComparing color interpretation...")
        for i in range(1, orig_meta['count'] + 1):
            if orig.colorinterp[i-1] != out.colorinterp[i-1]:
                print(f"Color interpretation difference in band {i}:")
                print(f"  Original: {orig.colorinterp[i-1]}")
                print(f"  Output: {out.colorinterp[i-1]}")

def main():
    parser = argparse.ArgumentParser(description="Compare metadata of two raster files.")
    parser.add_argument('original', help="Path to the original raster file")
    parser.add_argument('output', help="Path to the output raster file")

    args = parser.parse_args()

    compare_metadata(args.original, args.output)

if __name__ == "__main__":
    main()
