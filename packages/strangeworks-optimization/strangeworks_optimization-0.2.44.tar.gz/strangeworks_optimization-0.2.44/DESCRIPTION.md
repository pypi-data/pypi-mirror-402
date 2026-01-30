[![PyPI version](https://img.shields.io/pypi/v/strangeworks-optimization.svg)](https://pypi.org/project/strangeworks-optimization/)
[![Python version](https://img.shields.io/pypi/pyversions/strangeworks-optimization.svg)](https://pypi.org/project/strangeworks-optimization/)
[![Documentation](https://img.shields.io/badge/docs-strangeworks.com-blue)](https://docs.strangeworks.com/optimization/)

# Strangeworks Optimization

The **Strangeworks Optimization SDK** provides an abstraction layer for solving optimization problems using classical, quantum-inspired, and quantum solvers. It enables you to seamlessly switch between different optimization backends while maintaining a consistent interface.

## Features

- **Unified API** for multiple optimization solvers (quantum, quantum-inspired, and classical)
- **Support for multiple problem formats** including QUBO, MPS, LP, and more
- **Solver-agnostic interface** that allows easy switching between providers
- **Job management** with status tracking and result retrieval

## Installation

```bash
pip install strangeworks-optimization
```

## Quick Start

```python
import strangeworks as sw
from dimod import BinaryQuadraticModel
from strangeworks_optimization import StrangeworksOptimizer

# Authenticate with your API key
sw.authenticate("your-api-key")

# Create a QUBO model
linear = {1: -2, 2: -2, 3: -3, 4: -3, 5: -2}
quadratic = {(1, 2): 2, (1, 3): 2, (2, 4): 2, (3, 4): 2, (3, 5): 2, (4, 5): 2}
model = BinaryQuadraticModel(linear, quadratic, "BINARY")

# Create and run the optimizer with Quantagonia
optimizer = StrangeworksOptimizer(model=model, solver="quantagonia.qubo")
job = optimizer.run()

# Get results
results = optimizer.results(job.slug)
print(results.solution)
```

## Documentation

Comprehensive documentation is available at [docs.strangeworks.com/optimization](https://docs.strangeworks.com/optimization/).

The documentation includes:
- Getting started guides
- API reference
- Supported solvers and providers
- Problem format specifications
- Examples and tutorials

## Supported Solvers

The SDK supports a wide range of optimization solvers including:

- **Classical solvers**: Gurobi, Quantagonia
- **Quantum annealers**: D-Wave Leap, D-Wave Sampler
- **Quantum-inspired**: Hitachi, NEC, Toshiba
- **Hybrid solvers**: D-Wave Hybrid, Strangeworks Hybrid

For a complete list and solver-specific configuration options, see the [documentation](https://docs.strangeworks.com/optimization/).

## Requirements

- Python 3.11 or higher
- A Strangeworks account and API key ([Get started](https://portal.strangeworks.com))

## License

This project is licensed under the Apache License 2.0.

## Support

For support, questions, or feature requests, please visit:
- [Documentation](https://docs.strangeworks.com/optimization/)
- [Strangeworks Portal](https://portal.strangeworks.com)
