# -- import packages: ---------------------------------------------------------
import adata_query
import cell_neighbors
import scanpy

# -- load data: ---------------------------------------------------------------
adata = scanpy.datasets.pbmc3k_processed()
print(adata)


X_umap = adata.obsm["X_umap"]
full_idx = adata.obs.index

train_idx = adata.obs.sample(frac=0.9).index
test_idx = [idx for idx in full_idx if not idx in train_idx]
adata_train = adata[train_idx].copy()
adata_test = adata[test_idx].copy()

X_train = adata_query.fetch(adata_train, key="X_pca")
X_test = adata_query.fetch(adata_test, key="X_pca")

# -- build kNN index: --------------------------------------------------------
knn = cell_neighbors.kNN(adata_train, use_key="X_pca")
print(knn)