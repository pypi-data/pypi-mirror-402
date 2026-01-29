# Vestel ECV04 Client

A Python client library for interacting with the Vestel ECV04 electric vehicle charger web interface.

## Installation

Install from PyPI:

```bash
pip install vestel-ecv04-client
```

Or install with CLI support:

```bash
pip install vestel-ecv04-client[cli]
```

## Usage

### As a Library

```python
import asyncio
from vestel_ecv04_client import VestelEVC04Client, Config

async def main():
    config = Config(host="192.168.1.100", username="admin", password="password")
    client = VestelEVC04Client(config)
    
    # Get current phases and current setting
    state = await client.get_phases_and_current()
    print(f"Phases: {state.num_phases}, Current: {state.current}")
    
    # Set new settings
    await client.set_phases_and_current(phases=3, current=16)

asyncio.run(main())
```

### Command Line Interface

If installed with CLI support:

```bash
vestel-ecv04-cli --host 192.168.1.100 --username admin --password password get-state
vestel-ecv04-cli --host 192.168.1.100 --username admin --password password set-current --phases 3 --current 16
```

## License

MIT License