import os
import rasterio
from rasterio.enums import Resampling
import numpy as np
import json

LANDSAT_FOLDER = "./landsat_ARD"


# Parse folder to create list of tuple filepaths linking TIF to MTL json
# Should point to folder containing each Landsat 9 scene as separate folders containing TIF and MTL files
def parse_landsat_folder(folder):
    # Create list of tuples linking TIF to MTL json
    landsat_files = []
    for root, dirs, files in os.walk(folder):
        tif_path = None
        mtl_path = None
        for file in files:
            if file.endswith("_B10.TIF"):
                tif_path = os.path.join(root, file)
            elif file.endswith("_MTL.json"):
                mtl_path = os.path.join(root, file)
            elif file.endswith("_EMIS.TIF"):  
                emis_path = os.path.join(root, file)
        if tif_path and mtl_path and emis_path:
            landsat_files.append((tif_path, mtl_path, emis_path))
        else:
            print(f"Skipping {root} because it is missing a TIF or MTL file")
    return landsat_files


def process_landsat(tif_path, mtl_path, emis_path):
    # Open TIF file
    with rasterio.open(tif_path) as src:
        # Read TIF file
        b10 = src.read()  # Read Band 10
        meta = src.meta

    with rasterio.open(emis_path) as emis_src:
        emissivity = emis_src.read(1)  # Assuming single-band emissivity data

    # Open MTL file and convert to dict
    with open(mtl_path, "r") as f:
        mtl = json.load(f)

    # Return TIF and MTL data
    return b10, meta, mtl, emissivity


# Process each Landsat 9 scene
def process_landsat_folder(landsat_folder):
    # Parse folder to create list of tuple filepaths linking TIF to MTL json
    landsat_files = parse_landsat_folder(landsat_folder)
    # Process each Landsat 9 scene
    for tif_path, mtl_path, emis_path in landsat_files:
        b10, meta, mtl, emissivity = process_landsat(tif_path, mtl_path, emis_path)
        print(f"Processing {tif_path} with {mtl_path} and {emis_path}...")
        # Do something with the data
        toa_radiance = convert_toa_radiance(b10, meta, mtl)
        raw_kelvin = convert_to_kelvin(toa_radiance, mtl)
        corrected_kelvin = adjust_for_emissivity(raw_kelvin, emissivity)
        celsius = kelvin_to_celsius(corrected_kelvin)


# Convert Landsat 9 Band 10 to TOA Radiance
# Ll = MlQcal + Al
# where:
# Ll  = Top of Atmosphere (TOA) radiance in (Watts/m2*srad*um))
# Ml = Band-specific multiplicative rescaling factor from the metadata (RADIANCE_MULT_BAND_x, where x is the band number)
# Qcal = Quantized and calibrated standard product pixel values (DN)
# Al = Band-specific additive rescaling factor from the metadata (RADIANCE_ADD_BAND_x, where x is the band number)
def convert_toa_radiance(b10, meta, mtl):
    # Get Ml and Al from MTL file
    Ml = float(mtl["LANDSAT_METADATA_FILE"]["LEVEL1_RADIOMETRIC_RESCALING"]["RADIANCE_MULT_BAND_10"])
    Al = float(mtl["LANDSAT_METADATA_FILE"]["LEVEL1_RADIOMETRIC_RESCALING"]["RADIANCE_ADD_BAND_10"])
    # Convert to TOA Radiance
    toa_radiance = Ml * b10 + Al
    return toa_radiance

# At-Satellite Temperature of Landsat 4-5 thermal and Landsat 8 TIRS Bands:
# T = K2 / ln (K1/Ll +1)
# where:
# T = at-satellite brightness temperature in degrees Kelvin
# K2 = Band-specific thermal conversion constant from the metadata (K2_CONSTANT_BAND_x where x is band number 10 or 11)
# K1 = Band-specific thermal conversion constant from the metadata (K1_CONSTANT_BAND_x where x is band number 10 or 11)
# Ll = product of the Radiance formula
def convert_to_kelvin(toa_radiance, mtl):
    # Get K1 and K2 from MTL file
    K1 = float(mtl["LANDSAT_METADATA_FILE"]["LEVEL1_THERMAL_CONSTANTS"]["K1_CONSTANT_BAND_10"])
    K2 = float(mtl["LANDSAT_METADATA_FILE"]["LEVEL1_THERMAL_CONSTANTS"]["K2_CONSTANT_BAND_10"])
    # Convert to Kelvin
    kelvin = K2 / np.log((K1 / toa_radiance) + 1)
    return kelvin

def adjust_for_emissivity(kelvin, emissivity):
    emissivity_corrected = correct_emissivity(emissivity)
    # Constants for conversion
    wavelength = 10.8e-6  # meters
    h_c2 = 1.438e-2  # mK
    corrected_temp = kelvin / (1 + (wavelength * kelvin / h_c2) * np.log(emissivity_corrected))
    return corrected_temp

def correct_emissivity(emissivity):
    # Correct fill values and scale
    corrected = np.where(emissivity == -9999, 9999, emissivity)  # Use np.where for correct handling
    emissivity_corrected = corrected / 10000.0  # Scale emissivity to 0-1
    return emissivity_corrected


def kelvin_to_celsius(kelvin):
    return kelvin - 273.15

process_landsat_folder(LANDSAT_FOLDER)
