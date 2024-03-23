import rasterio
from rasterio.windows import from_bounds
from rasterio.warp import reproject, Resampling
import numpy as np


def peek(scene_library, target_band=10):
    print("Peeking at scene library...")
    print(f"Number of scenes: {len(scene_library)}")
    first_scene = list(scene_library.keys())[0]

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
    reprojected_data = np.empty(
        (src.count, dst["height"], dst["width"]), dtype=src.dtypes[0]
    )

    for i in range(src.count):
        reproject(
            source=rasterio.band(src, i + 1),
            destination=reprojected_data[i],
            src_transform=src.transform,
            src_crs=src.crs,
            dst_transform=dst["transform"],
            dst_crs=dst["crs"],
            resampling=Resampling.bilinear,
        )
    return reprojected_data
