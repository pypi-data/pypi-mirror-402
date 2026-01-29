# IntGate Python Client Library

Python client library for the [IntGate](https://license.intserver.com) license verification API.

## Installation

```bash
pip install -e .
```

Or install from requirements:

```bash
pip install -r requirements.txt
```

## Quick Start

```python
from intgate import IntGateClient

# Initialize the client with your team ID
client = IntGateClient(team_id="your-team-uuid-here")

# Verify a license
try:
    result = client.verify_license(
        license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
        hardware_identifier="unique-device-id",
        version="1.0.0"
    )
    
    if result['result']['valid']:
        print("License is valid!")
        print(f"License data: {result['data']}")
    else:
        print(f"License invalid: {result['result']['details']}")
        
except Exception as e:
    print(f"Error: {e}")
```

## API Reference

### Initialize Client

```python
from intgate import IntGateClient

client = IntGateClient(
    team_id="your-team-uuid",  # Required: Your team's UUID from IntGate dashboard
    base_url="https://license.intserver.com/api/v1"  # Optional: Custom API base URL
)
```

### Verify License

Validates a license key and returns license information, customer data, and product details.

```python
result = client.verify_license(
    license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",  # Required
    customer_id="customer-uuid",  # Optional: Required if strict customers enabled
    product_id="product-uuid",  # Optional: Required if strict products enabled
    challenge="random-string",  # Optional: For request signing
    version="1.0.0",  # Optional: Software version (3-255 chars)
    hardware_identifier="device-id",  # Optional: Unique device ID (10-1000 chars)
    branch="main"  # Optional: Product branch (2-255 chars)
)
```

### License Heartbeat

Send periodic heartbeats to determine if a device is still active. Should be called at regular intervals (e.g., every 30 minutes).

```python
result = client.license_heartbeat(
    license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",  # Required
    hardware_identifier="device-id",  # Required: Unique device ID (10-1000 chars)
    customer_id="customer-uuid",  # Optional
    product_id="product-uuid",  # Optional
    challenge="random-string",  # Optional
    version="1.0.0",  # Optional: Software version (3-255 chars)
    branch="main"  # Optional: Product branch (2-255 chars)
)
```

### Download Release

Download an encrypted release file. The file is encrypted using the provided session key.

```python
encrypted_file = client.download_release(
    license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",  # Required
    product_id="product-uuid",  # Required
    session_key="encrypted-session-key",  # Required: Encrypted with team's public key (10-1000 chars)
    hardware_identifier="device-id",  # Required: Unique device ID (10-1000 chars)
    version="1.0.0",  # Required: Software version (3-255 chars)
    customer_id="customer-uuid",  # Optional: Required if strict customers enabled
    branch="main"  # Optional: Product branch (2-255 chars)
)

# Save to file:
with open("release.encrypted", "wb") as f:
    f.write(encrypted_file)
```

## Automatic Heartbeat

Start automatic heartbeat in the background with customizable interval and callbacks.

```python
from intgate import IntGateClient

client = IntGateClient(team_id="your-team-uuid")

# Define callbacks
def on_success(result):
    print(f"✓ Heartbeat OK: {result['result']['valid']}")

def on_error(error):
    print(f"✗ Heartbeat failed: {error}")

# Start automatic heartbeat (runs in background thread)
client.start_automatic_heartbeat(
    license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
    hardware_identifier="device-12345",
    interval=1800,  # 30 minutes in seconds
    callback=on_success,
    error_callback=on_error,
    version="1.0.0"
)

# Your application continues running...
print("Application running with automatic heartbeat...")

# Get last heartbeat result anytime
last_result = client.get_last_heartbeat_result()
if last_result and last_result['result']['valid']:
    print("License is active")

# Check if heartbeat is running
if client.is_heartbeat_running():
    print("Automatic heartbeat is active")

# Stop when done
client.stop_automatic_heartbeat()
```

## Error Handling

The library provides specific exception types:

```python
from intgate import IntGateClient, IntGateAPIError, IntGateValidationError

client = IntGateClient(team_id="your-team-uuid")

try:
    result = client.verify_license(license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX")
except IntGateValidationError as e:
    # Input validation failed (missing required parameters, etc.)
    print(f"Validation error: {e}")
except IntGateAPIError as e:
    # API request failed (network error, HTTP error, etc.)
    print(f"API error: {e}")
    print(f"Status code: {e.status_code}")
    print(f"Response data: {e.response_data}")
except Exception as e:
    # Other errors
    print(f"Unexpected error: {e}")
```

## Complete Example

```python
from intgate import IntGateClient, IntGateAPIError

# Initialize client
client = IntGateClient(team_id="your-team-uuid-here")

# Verify license on startup
try:
    print("Verifying license...")
    result = client.verify_license(
        license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
        hardware_identifier="my-device-12345",
        version="1.0.0",
        product_id="your-product-uuid"
    )
    
    if not result['result']['valid']:
        print(f"License validation failed: {result['result']['details']}")
        exit(1)
    
    print("License verified successfully!")
    print(f"Expires: {result['data']['license'].get('expirationDate', 'Never')}")
    
    # Start automatic heartbeat
    print("\nStarting automatic heartbeat...")
    client.start_automatic_heartbeat(
        license_key="XXXXX-XXXXX-XXXXX-XXXXX-XXXXX",
        hardware_identifier="my-device-12345",
        interval=1800,  # Every 30 minutes
        version="1.0.0"
    )
    
    # Your application runs here...
    print("Application running...")
    
except IntGateAPIError as e:
    print(f"API Error: {e}")
    if e.status_code == 404:
        print("License not found")
    elif e.status_code == 401:
        print("Unauthorized - check your team ID")
    exit(1)
```

## License

MIT License

## Support

For API documentation, visit: https://license.intserver.com

For examples, see: [AUTOMATIC_HEARTBEAT.md](../AUTOMATIC_HEARTBEAT.md)
