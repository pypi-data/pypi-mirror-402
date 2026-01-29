# AgredaDB Python SDK

Official Python client for AgredaDB v2.0 - The Limitless Database.

## Installation

```bash
pip install agredadb
```

## Quick Start

```python
from agredadb import AgredaDBClient

# Connect to AgredaDB
client = AgredaDBClient("localhost:19999")

# Insert data
client.insert("users", {
    "id": 1,
    "name": "John Doe",
    "email": "john@example.com",
    "vector": [0.1, 0.2, 0.3, 0.4],
    "metadata": {"type": "user"}
})

# Get data
user = client.get("users", "id", 1)
print(user)

# Vector search
results = client.search("users", 
    vector=[0.1, 0.2, 0.3, 0.4], 
    limit=10
)

# Close connection
client.close()
```

## Features

- ✅ Simple and intuitive API
- ✅ Vector similarity search
- ✅ Batch operations
- ✅ PyTorch/NumPy integration
- ✅ Context manager support
- ✅ Type hints

## Documentation

Full documentation available at: https://github.com/luisagreda-aidev/agredadb

## License

GNU Affero General Public License v3 (AGPLv3)

## Author

Luis Eduardo Agreda Gonzalez
- Email: luisagreda.ai@gmail.com
- LinkedIn: [luis-agreda-artificial-intelligence-engineer](https://www.linkedin.com/in/luis-agreda-artificial-intelligence-engineer)
