# Slurpit SDK

The Slurpit SDK is a Python package for interacting with the Slurpit API, enabling developers to easily manage devices and planning resources. It is designed for simplicity and flexibility, offering methods for listing devices, retrieving planning data, and exporting information to CSV format.

## Installation

Install the SDK:

```bash
pip install slurpit_sdk
```

To run the examples, install dependencies using Poetry (recommended):

```bash
poetry install
```

Alternatively, use pip:

```bash
pip install -r requirements.txt
```

To build from source:

```bash
cd src
python setup.py install
```

## Quick Start

To quickly test the examples, copy `.env.example` to `.env` (includes default sandbox credentials):

```bash
# From the examples/ folder run:
cp .env.example .env
```

## Working with Devices

Retrieve and print the hostnames of all devices:

```python
devices = api.device.get_devices()
for device in devices:
    print(device.hostname)
```

## Exporting Data to CSV

To export planning data to a CSV file:

```python
plannings_csvdata = api.planning.get_plannings(export_csv=True)
result = api.device.save_csv_bytes(plannings_csvdata, "csv/plannings.csv")
```
## Exporting Data as Pandas DataFrame

To export planning data as a pandas dataframe

```python
plannings_df = api.planning.get_plannings(export_df=True)
```

## Pagination

Handle large sets of devices with pagination:

```python
devices = api.device.get_devices(offset=100, limit=1000)
for device in devices:
    print(device.hostname)
```