[![PyPI version](https://img.shields.io/pypi/v/strangeworks-qaoa.svg)](https://pypi.org/project/strangeworks-qaoa/)
[![Python version](https://img.shields.io/pypi/pyversions/strangeworks-qaoa.svg)](https://pypi.org/project/strangeworks-qaoa/)
[![Documentation](https://img.shields.io/badge/docs-strangeworks.com-blue)](https://docs.strangeworks.com/algorithms/qaoa/)

# Strangeworks QAOA SDK Extension

The **strangeworks-qaoa** package allows users to construct and solve problems with the Quantum Approximate Optimization Algorithm (QAOA) on multiple hardware providers through the Strangeworks Platform.

The package implements **StrangeworksQAOA**, an enhanced version of QAOA that tracks and reports the best individual bitstring solution found throughout the optimization process, rather than only using the average cost over all measurements.

## Installation

```bash
pip install -U pip strangeworks-qaoa
```

## Requirements

- Python version (see badge above)
- A Strangeworks account and API key ([Get started](https://portal.strangeworks.com))
- Quantum Resources enabled in your workspace

## Quick Start

```python
import strangeworks as sw
from strangeworks_qaoa.sdk import StrangeworksQAOA
import strangeworks_qaoa.utils as utils

sw.authenticate(api_key)
sw_qaoa = StrangeworksQAOA()

# Create problem
problem = utils.get_nReg_MaxCut_QUBO(3, 4, 0)

# Define parameters
problem_params = {
    "nqubits": 4,
    "maxiter": 50,
    "shotsin": 1000,
}

# Run job
sw_job = sw_qaoa.run("SV1", problem, problem_params)
result = sw_qaoa.get_results(sw_job)
```

## Documentation

Comprehensive documentation including problem formats, algorithm variants, parameters, and examples is available at [docs.strangeworks.com/algorithms/qaoa](https://docs.strangeworks.com/algorithms/qaoa/).

## Support

For support, questions, or feature requests:

- [Documentation](https://docs.strangeworks.com/algorithms/qaoa/)
- [Strangeworks Portal](https://portal.strangeworks.com)
- support@strangeworks.com
