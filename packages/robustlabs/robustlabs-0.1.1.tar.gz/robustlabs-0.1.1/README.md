# Robustlabs

**Assumption Mapping Toolkit (AMT)** and **Report Generator (RG)** for investment strategies.
A `risklabs` module that helps strategy developers map assumptions, evidence, and unknown to create robust decision memos.

## Key Features

- **Assumption Mapping**: Canonical map of what must be true for a strategy to work.
- **Report Generator**: Turns runs and artifacts into decision memos.
- **Explicit Unknowns**: Tracks assumptions with low confidence or missing evidence.

## Installation

```bash
pip install .
```

## Quick Start
See `demo.py` for a full example.

```python
from risklabs.amr import app
import uvicorn

# Run the API
uvicorn.run(app)
```
