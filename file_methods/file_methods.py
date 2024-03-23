import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
import numpy as np

def peek(scene_library, target_band=10):
    print("Peeking at scene library...")
    print(f"Number of scenes: {len(scene_library)}")
    print(f"Scenes: {list(scene_library.keys())}")
    first_scene = list(scene_library.keys())[0]
    print(f"First scene: {first_scene}")
    with rasterio.open(scene_library[first_scene][f"B{target_band}"]) as first_scene:
        sample_crs = first_scene.crs
        sample_transform = first_scene.transform
        sample_width = first_scene.width
        sample_height = first_scene.height
        sample_shape = first_scene.shape
    
    return {
        "crs": sample_crs,
        "transform": sample_transform,
        "width": sample_width,
        "height": sample_height,
        "shape": sample_shape,
    }

def test_reprojections(src, dst):
    reprojected_data = np.empty((src.count, dst["height"], dst["width"]), dtype=src.dtypes[0])

    # Reproject each band
    for i in range(src.count):
        reproject(
            source=rasterio.band(src, i + 1),
            destination=reprojected_data[i],
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst["transform"],
            dst_crs=dst["crs"],
            resampling=Resampling.bilinear
        )
    return reprojected_data

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

