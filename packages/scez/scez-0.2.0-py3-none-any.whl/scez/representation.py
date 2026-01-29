from itertools import product
import matplotlib.pyplot as plt
import scanpy as sc
import numpy as np


def optimising_umap_layout(adata, cluster_key='leiden',MIN_DISTS = [0.1, 1, 2], SPREADS = [0.5, 1, 5]):
    # https://scanpy-tutorials.readthedocs.io/en/latest/plotting/advanced.html
    # Copy adata not to modify UMAP in the original adata object
    adata_temp = adata.copy()
    
    # Create grid of plots, with a little extra room for the legends
    fig, axes = plt.subplots(
        len(MIN_DISTS), len(SPREADS), figsize=(len(SPREADS) * 3 + 2, len(MIN_DISTS) * 3)
    )

    # Loop through different umap parameters, recomputting and replotting UMAP for each of them
    for (i, min_dist), (j, spread) in product(enumerate(MIN_DISTS), enumerate(SPREADS)):
        ax = axes[i][j]
        param_str = " ".join(["min_dist =", str(min_dist), "and spread =", str(spread)])
        # Recompute UMAP with new parameters
        sc.tl.umap(adata_temp, min_dist=min_dist, spread=spread)
        # Create plot, placing it in grid
        sc.pl.umap(
            adata_temp,
            color=[cluster_key],
            title=param_str,
            s=40,
            ax=ax,
            show=False,
        )
    plt.tight_layout()
    plt.show()
    plt.close()
    del adata_temp


def random_ordering(adata):
    # Randomly order cells by making a random index and subsetting AnnData based on it
    # Set a random seed to ensure that the cell ordering will be reproducible
    np.random.seed(0)
    random_indices = np.random.permutation(list(range(adata.shape[0])))

    return random_indices