# Landsat Data Processor

Enclosed are some scripts to process Landsat data. The idea being a framework to process data according to a host of different common analysis needs. The scripts are written in Python and are designed to be run from the command line. 

## Getting Started
Copy down the repo, and make sure that [pipenv](https://pypi.org/project/pipenv/) is installed. Then install the dependencies with:
    
```bash 
pipenv install
```

Once completed, run the following command to enter the virtual environment:

```bash
pipenv shell
```

## Usage
The scripts are designed to be run from the command line. The following is an example of how to run the `landsat_processor.py` script, there are currently four arguments that can be passed to the script:

### Positional Arguments
- `input_folder`: The path to the landsat data, organized in folders where each folder contains the data for a single scene.
- `processing_method` : The type of analysis to be performed on the data. Currently, the only analysis types are `surface_temp` (kelvin) and `surface_temp_celsius`.
- `output_path`: The path to the folder where the processed data will be saved.

### Optional Arguments
- `-s` or `--suffix`: A suffix to be appended to the output file names. This is useful for keeping track of the processing method used. The default is a trailing `_`, anything you specify will be added after.

See an example command here:

```bash
python landsat_processor.py ./landsat surface_temp_celsius ./outputs -s qgis_test_return_deflate^C
```

## Helper Methods
There are a couple of helper scripts I used to debug my data, they are included here as `compare_rasters.py` and `compare_metadata.py`. The first script compares pixel values of two rasters and the second script compares some predetermined metadata (currently the stat summaries).

Both follow the following format:

```bash
python compare_rasters.py ./raster1.tif ./raster2.tif
```

## Motivation
These scripts come out of a project I'm working on as part of coursework at the NCSU Center for Geospatial Analytics. The idea is to create a framework that I can add to over time. 