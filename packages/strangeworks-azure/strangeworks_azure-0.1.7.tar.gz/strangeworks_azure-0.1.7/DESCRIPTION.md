[![PyPI version](https://img.shields.io/pypi/v/strangeworks-azure.svg)](https://pypi.org/project/strangeworks-azure/)
[![Python version](https://img.shields.io/pypi/pyversions/strangeworks-azure.svg)](https://pypi.org/project/strangeworks-azure/)
[![Documentation](https://img.shields.io/badge/docs-strangeworks.com-blue)](https://docs.strangeworks.com/quantum/azure-quantum/)

# Strangeworks Azure Quantum

The **Strangeworks Azure Quantum SDK** provides seamless access to Microsoft Azure
Quantum services through the Strangeworks platform. It enables you to run Qiskit
circuits on Azure Quantum backends with a simple, unified interface.

## Features

- **Qiskit integration** for building and executing quantum circuits
- **Azure Quantum backend access** through the Strangeworks platform
- **Job management** with status tracking and result retrieval
- **Support for multiple circuit formats** including Qiskit QuantumCircuit and OpenQASM
  strings
- **Unified interface** that simplifies Azure Quantum access

## Installation

```bash
pip install strangeworks-azure
```

## Quick Start

```python
import strangeworks as sw
from qiskit import QuantumCircuit
from strangeworks_azure import StrangeworksBackend

# Authenticate with your API key
sw.authenticate("your-api-key")

# List available Azure Quantum backends
backends = StrangeworksBackend.get_backends()
print("Available backends:")
for backend in backends:
    print(f"  - {backend.name} ({backend.status})")

# Create a quantum circuit
circuit = QuantumCircuit(2, 2)
circuit.name = "GenerateRandomBit"
circuit.h(0)
circuit.cx(0, 1)
circuit.measure([0, 1], [0, 1])

# Choose a backend (e.g., IonQ simulator)
ionq = StrangeworksBackend(name="ionq.simulator")

# Execute the circuit
job = ionq.run(circuit, shots=100)

# Get results
result = job.result()
print(f"Counts: {result.get('counts')}")
```

## Documentation

Comprehensive documentation is available at
[docs.strangeworks.com](https://docs.strangeworks.com/).

The documentation includes:

- Getting started guides
- API reference
- Supported backends and providers
- Circuit format specifications
- Examples and tutorials

## Supported Backends

The SDK provides access to Azure Quantum backends including:

- **IonQ** simulators and hardware
- **Rigetti** quantum devices
- Other Azure Quantum providers

For a complete list of available backends, use `StrangeworksBackend.get_backends()` or
check the [documentation](https://docs.strangeworks.com/).

## Requirements

- Python 3.11 or higher
- A Strangeworks account and API key ([Get started](https://portal.strangeworks.com))
- Qiskit for circuit construction

## License

This project is licensed under the Apache License 2.0.

## Support

For support, questions, or feature requests, please visit:

- [Documentation](https://docs.strangeworks.com/)
- [Strangeworks Portal](https://portal.strangeworks.com)
