# -- import packages: ---------------------------------------------------------
import adata_query
import anndata
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
import voyager

# -- set type hints: ----------------------------------------------------------
from typing import List, Optional, Tuple, Union

# -- configure logger: --------------------------------------------------------
logger = logging.getLogger(__name__)

# -- metric mapping: ----------------------------------------------------------
METRIC_TO_SPACE = {
    "euclidean": voyager.Space.Euclidean,
    "cosine": voyager.Space.Cosine,
    "inner_product": voyager.Space.InnerProduct,
}


# -- operational class: -------------------------------------------------------
class kNN:
    """k-Nearest Neighbors container using voyager backend.
    
    This class provides a kNN graph interface for single-cell data stored in
    AnnData objects. It uses voyager (Spotify's HNSW implementation) for
    efficient approximate nearest neighbor search.
    
    Args:
        adata: AnnData object containing the data.
        use_key: Key to fetch data from adata (e.g., "X_pca"). Default: "X_pca".
        n_neighbors: Number of neighbors to return in queries. Default: 20.
        metric: Distance metric to use. One of "euclidean", "cosine", 
            "inner_product". Default: "euclidean".
        space: Alternative to metric - directly specify voyager.Space.
            If provided, overrides metric parameter.
    
    Attributes:
        adata: The AnnData object.
        use_key: Key used to fetch data.
        n_neighbors: Number of neighbors for queries.
        space: The voyager.Space used for distance computation.
    """
    
    _KNN_IDX_BUILT: bool = False

    def __init__(
        self,
        adata: anndata.AnnData,
        use_key: str = "X_pca",
        n_neighbors: int = 20,
        metric: str = "euclidean",
        space: Optional[voyager.Space] = None,
    ):
        self.adata = adata
        self.use_key = use_key
        self.n_neighbors = n_neighbors
        
        # Handle metric/space parameter
        if space is not None:
            self.space = space
        else:
            self.space = METRIC_TO_SPACE.get(metric, voyager.Space.Euclidean)
        
        self._metric = metric
        self._build()

    @property
    def X(self) -> np.ndarray:
        """Fetch the data array from adata."""
        if not hasattr(self, "_X"):
            self._X = adata_query.fetch(self.adata, self.use_key, torch=False)
        return self._X

    @property
    def n_dim(self) -> int:
        """Number of dimensions in the data."""
        return self.X.shape[1]

    @property
    def n_obs(self) -> int:
        """Number of observations (cells) in the index."""
        return len(self._build_indices)

    @property
    def index(self) -> voyager.Index:
        """The voyager Index object."""
        if not hasattr(self, "_index"):
            self._index = voyager.Index(space=self.space, num_dimensions=self.n_dim)
        return self._index

    def _build(self) -> None:
        """Build the kNN index by adding all items from the data."""
        self._build_indices = [self.index.add_item(x_cell) for x_cell in self.X]
        self._KNN_IDX_BUILT = True
        logger.info(f"Built kNN index with {len(self._build_indices)} items")

    def query(
        self,
        X_query: np.ndarray,
        n_neighbors: Optional[int] = None,
        include_distances: bool = False,
    ) -> Union[np.ndarray, Tuple[np.ndarray, np.ndarray]]:
        """Query the kNN index for nearest neighbors.
        
        Args:
            X_query: Query points of shape (n_queries, n_dim).
            n_neighbors: Number of neighbors to return. If None, uses self.n_neighbors.
            include_distances: If True, also return distances.
        
        Returns:
            If include_distances is False:
                neighbors: Array of shape (n_queries, n_neighbors) with neighbor indices.
            If include_distances is True:
                Tuple of (neighbors, distances) arrays.
        """
        if n_neighbors is None:
            n_neighbors = self.n_neighbors
        
        # Query k+1 neighbors to exclude self if query point is in the index
        k = int(n_neighbors + 1)
        
        results = [
            self.index.query(X_query[i], k)
            for i in range(X_query.shape[0])
        ]
        
        # voyager.Index.query returns (neighbor_ids, distances)
        neighbors = np.array([r[0] for r in results])
        distances = np.array([r[1] for r in results])
        
        # Exclude the first neighbor (self) - take indices 1:k
        neighbors = neighbors[:, 1:].astype(int)
        distances = distances[:, 1:]
        
        if include_distances:
            return neighbors, distances
        return neighbors

    def _count_values(self, col: pd.Series) -> dict:
        """Count value occurrences in a Series."""
        return col.value_counts().to_dict()

    def _max_count(self, col: pd.Series) -> str:
        """Get the most frequent value in a Series."""
        return col.value_counts().idxmax()

    def count(
        self,
        query_result: np.ndarray,
        obs_key: str,
        max_only: bool = False,
        n_neighbors: Optional[int] = None,
    ) -> Union[List[dict], List[str]]:
        """Count neighbor annotations from query results.
        
        Args:
            query_result: Array of neighbor indices from query().
            obs_key: Key in adata.obs to count.
            max_only: If True, return only the most frequent annotation per query.
            n_neighbors: Number of neighbors (for reshaping). If None, uses self.n_neighbors.
        
        Returns:
            If max_only is False:
                List of dicts mapping annotation values to counts.
            If max_only is True:
                List of most frequent annotation values.
        """
        if n_neighbors is None:
            n_neighbors = self.n_neighbors

        nn_adata = self.adata[query_result.flatten()]
        query_df = pd.DataFrame(
            nn_adata.obs[obs_key].to_numpy().reshape(-1, n_neighbors).T
        )
        del nn_adata

        if not max_only:
            return [
                self._count_values(query_df[i]) for i in query_df.columns
            ]  # list of dicts
        return [
            self._max_count(query_df[i]) for i in query_df.columns
        ]  # list of values

    def aggregate(
        self,
        X_query: np.ndarray,
        obs_key: str,
        max_only: bool = False,
        n_neighbors: Optional[int] = None,
    ) -> pd.DataFrame:
        """Query neighbors and aggregate annotation counts.
        
        Combines query() and count() into a single operation.
        
        Args:
            X_query: Query points of shape (n_queries, n_dim).
            obs_key: Key in adata.obs to aggregate.
            max_only: If True, return only the most frequent annotation per query.
            n_neighbors: Number of neighbors. If None, uses self.n_neighbors.
        
        Returns:
            DataFrame with aggregated counts or most frequent annotations.
        """
        _df = (
            pd.DataFrame(
                self.count(
                    query_result=self.query(X_query=X_query, n_neighbors=n_neighbors),
                    obs_key=obs_key,
                    max_only=max_only,
                    n_neighbors=n_neighbors,
                )
            )
            .fillna(0)
            .sort_index(axis=1)
        )
        if not max_only:
            return _df
        return _df.rename({0: obs_key}, axis=1)

    def multi_aggregate(
        self,
        X_query: np.ndarray,
        obs_key: str,
        max_only: bool = False,
        n_neighbors: Optional[int] = None,
    ) -> Union[List[pd.DataFrame], pd.DataFrame]:
        """Aggregate annotations for multiple query sets.
        
        Args:
            X_query: Multiple query sets of shape (n_sets, n_queries, n_dim).
            obs_key: Key in adata.obs to aggregate.
            max_only: If True, return only the most frequent annotation per query.
            n_neighbors: Number of neighbors. If None, uses self.n_neighbors.
        
        Returns:
            If max_only is False:
                List of DataFrames, one per query set.
            If max_only is True:
                Single DataFrame with columns for each query set.
        """
        _list_of_dfs = [
            self.aggregate(
                X_query=X_query[i],
                obs_key=obs_key,
                max_only=max_only,
                n_neighbors=n_neighbors,
            )
            for i in range(len(X_query))
        ]

        if max_only:
            concat_df = pd.concat(_list_of_dfs, axis=1)
            concat_df.columns = range(len(X_query))
            return concat_df

        return _list_of_dfs

    def save(self, path: Union[str, Path]) -> None:
        """Save the kNN index and metadata to disk.

        Saves two files:
        - {path}.index: The voyager index file
        - {path}.json: Metadata (use_key, n_neighbors, metric, build_indices)

        Args:
            path: Base path for saved files (without extension).

        Example:
            >>> knn.save("my_model/knn")
            # Creates my_model/knn.index and my_model/knn.json
        """
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save the voyager index
        index_path = str(path) + ".index"
        self.index.save(index_path)

        # Save metadata
        metadata = {
            "use_key": self.use_key,
            "n_neighbors": self.n_neighbors,
            "metric": self._metric,
            "n_dim": self.n_dim,
            "build_indices": self._build_indices,
        }
        metadata_path = str(path) + ".json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f)

        logger.info(f"Saved kNN index to {index_path}")

    @classmethod
    def load(
        cls,
        path: Union[str, Path],
        adata: anndata.AnnData,
    ) -> "kNN":
        """Load a saved kNN index from disk.

        Args:
            path: Base path of saved files (without extension).
            adata: AnnData object to associate with the loaded index.

        Returns:
            A new kNN instance with the loaded index.

        Example:
            >>> knn = kNN.load("my_model/knn", adata)
        """
        path = Path(path)

        # Load metadata
        metadata_path = str(path) + ".json"
        with open(metadata_path, "r") as f:
            metadata = json.load(f)

        # Create instance without building index
        instance = cls.__new__(cls)
        instance.adata = adata
        instance.use_key = metadata["use_key"]
        instance.n_neighbors = metadata["n_neighbors"]
        instance._metric = metadata["metric"]
        instance.space = METRIC_TO_SPACE.get(metadata["metric"], voyager.Space.Euclidean)
        instance._build_indices = metadata["build_indices"]
        instance._KNN_IDX_BUILT = True

        # Load the voyager index
        index_path = str(path) + ".index"
        instance._index = voyager.Index.load(index_path)

        logger.info(f"Loaded kNN index from {index_path} with {len(instance._build_indices)} items")
        return instance

    def __repr__(self) -> str:
        """String representation of the kNN instance."""
        attrs = {
            "built": self._KNN_IDX_BUILT,
            "n_obs": self.n_obs,
            "n_dim": self.n_dim,
            "n_neighbors": self.n_neighbors,
            "use_key": self.use_key,
        }
        repr_str = "k-nearest neighbor graph\n"
        for key, val in attrs.items():
            repr_str += f"\n  {key}: {val}"
        return repr_str
