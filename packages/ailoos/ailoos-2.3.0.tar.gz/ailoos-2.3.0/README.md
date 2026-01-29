# AILOOS SDK

AILOOS is a robust Python library for participating in decentralized federated learning networks. This SDK enables nodes to join training sessions, contribute processing power, and interact with the Ailoos ecosystem securely.

## Features

- **Federated Learning**: Participate in distributed model training sessions using FedAvg and other advanced algorithms.
- **Privacy First**: Secure key management and encrypted P2P communication (ECDSA + ECDH).
- **Decentralized Marketplace**: Interact with the data marketplace to list or purchase datasets.
- **Hardware Integration**: Smart capabilities detection for optimal workload assignment.

## Installation

```bash
pip install ailoos
```

## Quick Start

### Initialize a Node

```python
import asyncio
from ailoos.sdk.node_sdk import NodeSDK

async def main():
    # Initialize the node
    node = NodeSDK(node_id="my-ai-node-01")
    
    # Connect and start participating
    await node.initialize()
    await node.start()
    
    # Keep running
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
```

### Advanced Usage

For granular control over components:

```python
from ailoos.sdk.advanced_client import create_ailoos_node

async def run_advanced():
    # Create node with specific capabilities
    node = await create_ailoos_node(
        node_id="advanced-node-01",
        enable_marketplace=True,
        enable_federated=True
    )
    
    # Search for datasets
    datasets = await node.search_datasets(query="satellite imagery")
    print(f"Found {len(datasets)} datasets")

    # Join a training session
    await node.join_training_session("session_v1_xyz")
```

## Requirements

- Python 3.8+
- Network connectivity for P2P and Federation

## License

MIT License. See [LICENSE](LICENSE) for details.
