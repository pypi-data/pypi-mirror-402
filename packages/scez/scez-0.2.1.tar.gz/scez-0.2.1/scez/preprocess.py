import pandas as pd
import scanpy as sc
import scar


def normalization(adata, target_sum=1e4, max_value=10, final_layer='scaled', keep_initial_layer=True):
    if keep_initial_layer == True:
        adata.layers['raw_counts'] = adata.X.copy()
    elif type(keep_initial_layer) == str:
        adata.layers[keep_initial_layer] = adata.X.copy()
    
    # normalize counts to target_sum (default 1e4)
    counts = sc.pp.normalize_total(adata, target_sum=target_sum, inplace=False)
    # log1p transform
    adata.layers["log1p_norm"] = sc.pp.log1p(counts["X"], copy=True)
    # scale counts
    adata.layers['scaled'] = sc.pp.scale(adata, max_value=max_value, copy=True).X
    # set the final layer
    adata.X = adata.layers[final_layer]


def remove_ambient_rna(adata_filtered_feature_bc, adata_raw_feature_bc):
    scar.setup_anndata(
        adata = adata_filtered_feature_bc,
        raw_adata = adata_raw_feature_bc,
        prob = 0.995,
        kneeplot = True
    )

    adata_scar = scar.model(
        raw_count=adata_filtered_feature_bc.to_df(), # In the case of Anndata object, scar will automatically use the estimated ambient_profile present in adata.uns.
        # ambient_profile=adata_filtered_feature_bc.uns['ambient_profile_Gene Expression'],
        feature_type='mRNA',
        sparsity=1,
        # device=device # Both cpu and cuda are supported.
    )

    adata_scar.train(
        epochs=200,
        batch_size=64,
        verbose=True
    )

    # After training, we can infer the native true signal
    adata_scar.inference(batch_size=256)  # by defaut, batch_size = None, set a batch_size if getting a memory issue

    denoised_count = pd.DataFrame(
        adata_scar.native_counts, 
        index=adata_filtered_feature_bc.obs_names, 
        columns=adata_filtered_feature_bc.var_names
    )

    adata = adata_filtered_feature_bc.copy()
    adata.layers['raw_counts'] = adata.X
    adata.layers['scar_denoised_counts'] = denoised_count.to_numpy()

    return adata


def clustering(
        adata
        ):
    pass
    # , n_pcs=50, n_neighbors=30, use_highly_variable='Yes',
    #     use_rep=None, resolution=None
    
    # if use_highly_variable == 'Yes':
    #     sc.pp.highly_variable_genes(adata, min_mean=0.0125, max_mean=3, min_disp=0.5)
    #     sc.tl.pca(adata, svd_solver='arpack', use_highly_variable=True)
    # else:
    #     sc.pp.pca(adata, n_comps=n_pcs)
    # sc.pp.neighbors(adata, use_rep=use_rep, n_neighbors=n_neighbors)#, n_pcs=n_pcs)
    # sc.tl.umap(adata)
    # sc.tl.leiden(adata, resolution=resolution)
