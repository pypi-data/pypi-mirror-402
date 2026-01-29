# 🚗 Analytics Ingest Client

A lightweight Python library to batch and send automotive telemetry — like signals, DTCs, GPS, and network stats — to a GraphQL backend.

---

## Features

* Python 3.11+ support
* Clean, single-class interface: `IcsAnalytics`
* In-memory caching for resolved IDs
* Smart batching (by time, count, or signal limit)
* Async-safe request queuing (1 request at a time)
* Minimal dependencies
* Easy to integrate and test
* Supports Signals, DTCs, GPS, and Network Stats ingestion

---

## Installation

```bash
pip install ics-wivi-analytics-ingest
```
---

## Setting Endpoint via Environment Variables

You can avoid hardcoding sensitive values like GraphQL endpoints by using environment variables.

### Example (Linux / macOS)

```bash
export GRAPHQL_ENDPOINT="https://graph.{server}.wlnv.srv:8080/graphql" # example endpoint = https://graph.a7f1.wlnv.srv:8080/graphql
```

## Quick Usage

```python
from analytics_ingest import IcsAnalytics

client = IcsAnalytics(
    device_id=123,
    vehicle_id=456,
    fleet_id=789,
    org_id=1011,
    graphql_endpoint="https://graph.{server}.wlnv.srv:8080/graphql", # example endpoint = https://graph.a7f1.wlnv.srv:8080/graphql
    batch_size=100,
    batch_interval_seconds=10,
    max_signal_count=100
)

# Add a signal
client.add_signal({
    'name': 'VehicleIdentificationNumber',
    'unit': '',
    'messageName': 'BusQuery_IDDecoding_F190_VSSAL', 
    'networkName': 'Cluster_6_TestTool',
    'ecuName': '',
    'arbId': '',
    'fileId': '1234',
    'paramType': 'TEXT',
    'signalType': 'DID',
    'messageDate': '2025-07-15T01:40:00.000000',
    'paramId': 'F190',
    'data': [{
        'value': 0.04,
        'time': '1970-01-07T18:28:54Z',
        'svalue':''
    }, # more data objects
    ]
})

# Add DTCs
client.add_dtc({
    'messageName': 'DTC Message99B049',
    'name': 'DTC Message99B049',
    'networkName': 'Cluster_6_TestTool',
    'ecuName': 'VCU_Android_GAS',
    'ecuId': '14DA80F1',
    'messageDate': '2025-07-15T01:42:20.385429',
    'fileId': '1234',
    'data': [{
        'dtcId': 'B19B0-49',
        'description': 'Head-Up Display - Internal Electronic Failure',
        'status': '2F',
        'time': '2025-07-15T01:42:15.979524'
        'extended':[{'bytes':'3214"31241234123412'} # more bytes
        ]
        'snapshot':[{'bytes':'3214"31241234123412'} # more bytes
        ]
    }, # more data objects. 
    ]
})

# Add GPS
client.add_gps({
    "time": "2025-07-28T12:34:56.789Z",
    "latitude": 37.7749,
    "longitude": -122.4194,
    "accuracy": 10.5,
    "altitude": 120.3,
    "speed": 45.2,
    "bearing": 75.0,
    "available": {
        "accuracy": True,
        "altitude": True,
        "bearing": False,
        "speed": True,
        "time": True
    }
})

# Add Network Stats

client.add_network_stats({
    'name': 'jacobs',
    'vehicleId': 9539366,
    'uploadId': 4255,
    'totalMessages': 222,
    'matchedMessages': 139,
    'unmatchedMessages': 0,
    'errorMessages': 27,
    'longMessageParts': 21,
    'maxTime': '2025-08-01T11:06:53.947Z',
    'minTime': '2025-08-01T11:06:53.947Z',
    'rate': 59.44
})

# Flush remaining data before exit
client.flush()
client.close()
```

---

## Config Options

| Param                    | Description                                 | Default  |
| ------------------------ | ------------------------------------------- | -------- |
| `device_id`              | Device ID (required)                        | –        |
| `vehicle_id`             | Vehicle ID (required)                       | –        |
| `fleet_id`               | Fleet ID (required)                         | –        |
| `org_id`                 | Organization ID (required)                  | –        |
| `graphql_endpoint`       | GraphQL endpoint (overrides `.env` if set)  | Optional |
| `batch_size`             | Maximum number of items per batch           | 100      |
| `batch_interval_seconds` | Time-based auto flush interval (in seconds) | 10       |
| `max_signal_count`       | Maximum number of signals before flush      | 100      |


---

### Payload Reference

#### `add_signal` Payload

| Key           | Description                        | Required / Optional |
| ------------- | ---------------------------------- | ------------------- |
| `name`        | Signal name                        | **Required**        |
| `unit`        | Measurement unit (e.g. °C, km/h)   | **Required**        |
| `messageName` | Message name in DB                 | **Required**        |
| `networkName` | Network name                       | **Required**        |
| `ecuName`     | ECU name                           | Optional            |
| `arbId`       | Arbitration ID                     | Optional            |
| `fileId`      | File ID for trace reference        | Optional        |
| `paramType`   | Parameter type (`TEXT`, `NUMBER`, `ENCODED`, `RAW`, `STRING`) | Optional            |
| `signalType`  | Signal type (`DID`, `PID`, `DMR`, `SIGNAL`)| Optional    |
| `messageDate` | Message timestamp (ISO 8601)       | **Required**        |
| `paramId`     | Parameter ID (DID identifier)      | Optional            |
| `data`        | List of data objects               | **Required**        |

**Inside `data`:**

| Key      | Description               | Required / Optional |
| -------- | ------------------------- | ------------------- |
| `value`  | Numeric value             | Optional            |
| `time`   | Timestamp (ISO 8601)      | **Required**        |
| `svalue` | String value (if textual) | Optional            |

---

#### `add_dtc` Payload

| Key           | Description                  | Required / Optional |
| ------------- | ---------------------------- | ------------------- |
| `messageName` | DTC message name             | **Required**        |
| `name`        | DTC display name             | Optional            |
| `networkName` | Network name                 | **Required**        |
| `ecuName`     | ECU name                     | Optional            |
| `ecuId`       | ECU ID                       | Optional            |
| `messageDate` | Message timestamp (ISO 8601) | Optional            |
| `fileId`      | File ID for trace reference  | Optional            |
| `data`        | List of DTC data objects     | Optional            |

**Inside `data`:**

| Key           | Description                | Required / Optional |
| ------------- | -------------------------- | ------------------- |
| `dtcId`       | DTC identifier             | **Required**        |
| `description` | Human-readable description | **Required**        |
| `status`      | Status code                | **Required**        |
| `time`        | Timestamp (ISO 8601)       | **Required**        |
| `extended`    | List of bytes's objects    | Optional            |
| `snapshot`    | List of bytes's objects    | Optional            |

---

#### `add_gps` Payload

| Key         | Description                        | Required / Optional |
| ----------- | ---------------------------------- | ------------------- |
| `time`      | Timestamp (ISO 8601)               | **Required**        |
| `latitude`  | Latitude                           | Optional            |
| `longitude` | Longitude                          | Optional            |
| `accuracy`  | GPS accuracy (meters)              | Optional            |
| `altitude`  | Altitude (meters)                  | Optional            |
| `speed`     | Speed (m/s or chosen unit)         | Optional            |
| `bearing`   | Bearing (degrees)                  | Optional            |
| `available` | Object describing available fields, all of them are optional | Optional |

---

#### `add_network_stats` Payload

| Key                 | Description              | Required / Optional |
| ------------------- | ------------------------ | ------------------- |
| `name`              | Network name             | **Required**        |
| `vehicleId`         | Vehicle ID               | **Required**        |
| `uploadId`          | Upload session ID        | **Required**        |
| `totalMessages`     | Total number of messages | **Required**        |
| `matchedMessages`   | Number of matched msgs   | **Required**        |
| `unmatchedMessages` | Number of unmatched msgs | **Required**        |
| `errorMessages`     | Number of errors         | **Required**        |
| `longMessageParts`  | Number of long msgs      | **Required**        |
| `rate`              | Message rate             | **Required**        |
| `maxTime`           | Max timestamp (ISO 8601) | Optional            |
| `minTime`           | Min timestamp (ISO 8601) | Optional            |

---

## Error Handling & Logging

* Raises exceptions for bad input or backend failures
* Use logging instead of print in production
* Automatically retries failed batches on next interval

---

## Testing

Run all tests:

```bash
PYTHONPATH=src python3 -m unittest discover -s tests -v
```

Build and publish:

```bash
# change version and description in .toml file
rm -rf dist/
python3 -m build
python -m twine upload dist/*
```

---

## Improvements & Roadmap

* Full async API support
* Runtime config updates
* More usage examples
* Metrics & monitoring hooks
* Linting/type-checking in CI

---

## Contributing

We welcome PRs and issues! Please follow PEP8 and include tests with any changes.

### One-Time Setup

```bash
pip install pre-commit
pre-commit install
```

---

## Dev Quick Start

```bash
git clone http://lustra.intrepidcs.corp/ics/wivi/ipa-py-library.git
cd analytics-ingest

# Setup virtual environment
python3.11 -m venv venv3.11
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
# Uses pyproject.toml – no requirements.txt
pip install -e .[dev]

# Create a .env file in the project root
export GRAPHQL_SERVER="develop"

```

Test ingestion logic:

```bash
PYTHONPATH=src python3 integeration_test.py
```

---

## License

MIT License
Readme.txt
4 KB
