# cell-neighbors

Neighbor graphs for single-cell data (`AnnData`)

This repository provides a Python package for building k-nearest neighbor (`kNN`) graphs from `AnnData` objects.

The package is built on the `Voyager` library from Spotify.

## Features
- Efficient kNN Graph Construction from `Voyager`.
- Direct `AnnData` integration
- Flexible querying of neighbors in the constructed `kNN` graph index.

## Installation

Install the latest release from PyPI:

```bash
pip install cell-neighbors
```

or, if you use `uv`:

```bash
uv pip install cell-neighbors
# or, to add it to your pyproject.toml
uv add cell-neighbors
```

## Example

```python
import cell_neighbors

# Initialize kNN graph builder
knn_graph = cell_neighbors.kNN(adata), use_key="X_pca")

# Query neighbors
X_query = [...]  # Your query points as numpy array
neighbors = knn_graph.query(X_query)
```

## Documentation

For real examples, detailed usage instructions, and API reference, please refer to the documentation [coming soon].
