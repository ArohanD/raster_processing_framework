# Python builtins
import base64
from getpass import getpass
from io import StringIO
import json
import os

# External requirements
import keyring
import matplotlib.pyplot as plt
import pandas as pd
import rasterio
import requests
from requests.auth import HTTPBasicAuth
import rioxarray as rx

PL_API_KEY = ""

# Test API Key
# Planet's Subscriptions API base URL for making restFUL requests
BASE_URL = "https://api.planet.com/subscriptions/v1"

auth = HTTPBasicAuth(PL_API_KEY, "")
response = requests.get(BASE_URL, auth=auth)
print(response)

# Create a new subscription JSON object
timeseries_payload = {
    "name": "Durham BBox - LST-AMSR2_V1.0_100",
    "source": {
        "type": "land_surface_temperature",
        "parameters": {
            "id": "LST-AMSR2_V1.0_100",
            "start_time": "2023-05-01T00:00:00Z",
            "end_time": "2023-09-02T00:00:00Z",
            "geometry": {
                "coordinates": [
                    [
                        [-79.016303759539142, 35.863217411268941],
                        [-78.699318347193724, 35.863217411268941],
                        [-78.699318347193724, 36.239327491793802],
                        [-79.016303759539142, 36.239327491793802],
                        [-79.016303759539142, 35.863217411268941],
                    ]
                ],
                "type": "Polygon",
            },
        },
    },
}

def create_subscription(subscription_payload, auth, headers):
    try:
        response = requests.post(BASE_URL, json=subscription_payload, auth=auth, headers=headers)
        response.raise_for_status()  # raises an error if the request was malformed
    except requests.exceptions.HTTPError:
        print(f"Request failed with {response.text}")  # show the reason why the request failed
    else:
        response_json = response.json()
        subscription_id = response_json["id"]
        print(f"Successful request with {subscription_id=}")
        return subscription_id

# set content type to json
headers = {'content-type': 'application/json'}

input("Press Enter to proceed or CTRL+C to abort...")

# create a subscription
print("Creating a subscription...")
timeseries_subscription_id = create_subscription(timeseries_payload, auth, headers)
print(timeseries_subscription_id)

input("Press Enter to verify subscription or CTRL+C to abort...")

def get_subscription_status(subscription_id, auth):
    subscription_url = f"{BASE_URL}/{subscription_id}"
    subscription_status = requests.get(subscription_url, auth=auth).json()['status']
    return subscription_status

status = get_subscription_status(timeseries_subscription_id, auth)
print(status)

input("Press Enter to retrieve data or CTRL+C to abort...")

# Retrieve the resulting data in CSV format
results_csv = requests.get(f"{BASE_URL}/{timeseries_subscription_id}/results?format=csv", auth=auth)

# Read CSV Data into a Pandas dataframe
csv_text = StringIO(results_csv.text)
df = pd.read_csv(csv_text, parse_dates=["item_datetime", "local_solar_time"], index_col="local_solar_time")

# Filter by valid data only
df = df[df["lst.band-1.valid_percent"].notnull()]
df = df[df["lst.band-1.valid_percent"] > 0]
df = df[df["status"] != "QUEUED"]

print(df.head())

# Plot the data
# Plot the Land Surface Temperature time-series for nighttime observations
df.between_time("1:15", "1:45")["lst.band-1.mean"].plot(
    grid=True, style=".", alpha=0.4, label="Night LST", figsize=(8, 4)
)

# Plot the Land Surface Temperature time-series for daytime observations
df.between_time("13:15", "13:45")["lst.band-1.mean"].plot(
    grid=True, style="r.", alpha=0.4, label="Day LST", figsize=(8, 4)
)

# Extra information for the visualization
plt.ylabel("Land Surface Temperature (K)", size = 10)
plt.xlabel("Date", size = 10)
plt.title("Average Land Surface Temperature of the AOI", size = 15)
plt.legend()

# Display the visualization
plt.show()