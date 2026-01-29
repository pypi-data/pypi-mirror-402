# FSTDB - File System Database

A simple file-based database library for Python.

## Installation

```bash
pip install fstdb
```

## Usage

```python
from fstdb import FSTDB

# Initialize database
db = FSTDB("my_database")

# Set a value
db.set("user:1", {"name": "John", "age": 30})

# Get a value
user = db.get("user:1")
print(user)  # {'name': 'John', 'age': 30}

# Check if key exists
if db.exists("user:1"):
    print("User exists!")

# Get all keys
all_keys = db.keys()

# Delete a key
db.delete("user:1")

# Clear all data
db.clear()
```

## Features

- Simple key-value storage
- JSON-based storage
- Thread-safe file operations
- Easy to use API

## License

MIT License
