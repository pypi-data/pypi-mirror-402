# OLA Plug DLL Helper

Python wrapper library for OLAPlug DLL, providing automation and hardware interaction capabilities on Windows.

## Installation

```bash
pip install ola_plug
```

## Quick Start

```python
from ola_plug import OLAPlugDLLHelper

# Create an instance
instance = OLAPlugDLLHelper.CreateCOLAPlugInterFace()

# Use the library
print(f"Version: {OLAPlugDLLHelper.Ver()}")

# Clean up
OLAPlugDLLHelper.DestroyCOLAPlugInterFace(instance)
```

## Features

- DLL function wrapper for OLA Plug hardware
- Window binding and automation
- Graph-based path planning
- GUI drawing capabilities
- Assembly code support
- Mouse and keyboard automation

## Requirements

- Windows operating system
- Python 3.7+
- OLAPlug_x64.dll (included with hardware)

## Documentation

For detailed API documentation, please refer to the [official documentation](link-to-docs).

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
