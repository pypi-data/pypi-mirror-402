import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
import anndata as ad

from pydeseq2.dds import DeseqDataSet
from pydeseq2.default_inference import DefaultInference
from pydeseq2.ds import DeseqStats
from .utils import run_adjust_text
from adpbulk import ADPBulk


def pseudobulk_by_clusters(adt, condition, cluster_col='leiden', method="mean"):
    # initialize the object
    adpb = ADPBulk(adt, [cluster_col, condition], method=method)

    # perform the pseudobulking
    pseudobulk_matrix = adpb.fit_transform()

    # retrieve the sample metadata (useful for easy incorporation with edgeR)
    sample_meta = adpb.get_meta()

    out = ad.AnnData(
        X=pseudobulk_matrix,
        obs=sample_meta.set_index('SampleName')
    )

    return out


def run_deseq(adata, design, tested_level, ref_level, n_cpus=8):

    inference = DefaultInference(n_cpus=n_cpus)
    
    dds = DeseqDataSet(
        counts=adata.to_df().astype(int),
        metadata=adata.obs,
        design_factors=design,  # compare samples based on the "condition"
        refit_cooks=True,
        inference=inference,
    )

    dds.deseq2()

    stat_res = DeseqStats(
        dds, 
        contrast=[design, tested_level, ref_level], 
        inference=inference
    )
    stat_res.summary()

    df = stat_res.results_df

    return df


def plot_volcano(df, title=None, labels=None, n_genes=False, side='both', 
                 font_scale=1, dot_size = 5,
                 color = '#1f77b4', color_highlight = '#FFA500',
                 ax = None, **kwargs):
    dot_size_highlight = dot_size * 1.1
    annotate_font_size = 5 * font_scale
    scatter_font_size = 8 * font_scale
    label_font_size = 9 * font_scale
    title_font_size = 10 * font_scale

    if 'name' not in df.columns: df['name'] = df.index.to_list()
    df['-log10(pvalue)'] = - np.log10(df.pvalue)

    if not ax: fig, ax = plt.subplots(figsize=(3, 3))

    # Scatter plot
    ax.scatter(
        df['log2FoldChange'],
        df['-log10(pvalue)'],
        alpha=0.9, s=dot_size, c=color,
        **kwargs
    )

    # Set background color to transparent
    ax.set_facecolor('none')

    # Set smaller font size
    ax.tick_params(axis='both', which='both', labelsize=scatter_font_size)

    # Set labels
    ax.set_xlabel('log2FoldChange', fontsize=label_font_size)
    ax.set_ylabel('-log10(pvalue)', fontsize=label_font_size)

    # Set plot title
    if not title:
        ax.set_title('Volcano Plot', fontsize=title_font_size)
    else:
        ax.set_title(title, fontsize=title_font_size)

    ax.grid(False)

    # check if `labels` is provided or set that based on `n_genes` and `side`
    if labels and n_genes:
        # error message if both labels and n_genes are provided and say one of them is allowed
        raise ValueError('Provide either labels or n_genes, not both!')

    elif n_genes and side == 'positive':
        # Highlight top genes
        top_genes = df.query('log2FoldChange > 0').nlargest(n_genes, '-log10(pvalue)')
        labels = [row['name'] for _, row in top_genes.iterrows()]

    elif n_genes and side == 'negative':
        # Highlight top genes
        top_genes = df.query('log2FoldChange < 0').nlargest(n_genes, '-log10(pvalue)')
        labels = [row['name'] for _, row in top_genes.iterrows()]

    elif n_genes and side == 'both':
        # Highlight top genes
        top_genes = df.nlargest(n_genes, '-log10(pvalue)')
        labels = [row['name'] for _, row in top_genes.iterrows()]

    # Highlight the points from given labels
    if labels:
        for label in labels:
            ax.scatter(
                df.loc[label, 'log2FoldChange'],
                df.loc[label, '-log10(pvalue)'],
                s=dot_size_highlight, c=color_highlight
            )
        run_adjust_text(
            df.loc[labels, 'log2FoldChange'], 
            df.loc[labels, '-log10(pvalue)'], 
            labels, 
            font_size=annotate_font_size, ax=ax, use_arrow=False
        )

    if not ax: 
        plt.tight_layout()
        plt.show()


def plot_top_DEG_violinplot(adata, df, layer=None, title=None, labels=None, n_genes=False, side='both', font_scale=1, figsize=(10, 4), **kwargs):
    
    label_font_size = 9 * font_scale
    title_font_size = 10 * font_scale

    if 'name' not in df.columns: df['name'] = df.index.to_list()

    if labels and n_genes:
        # error message if both labels and n_genes are provided and say one of them is allowed
        raise ValueError('Provide either labels or n_genes, not both!')

    if not labels and not n_genes:
        # error message if neither labels nor n_genes are provided
        raise ValueError('Provide either labels or n_genes!')

    if labels:
        # Highlight the points from given list
        selected_genes = df.loc[labels]

    elif n_genes and side == 'positive':
        # Highlight top genes
        selected_genes = df.query('log2FoldChange > 0').nlargest(n_genes, '-log10(pvalue)')

    elif n_genes and side == 'negative':
        # Highlight top genes
        selected_genes = df.query('log2FoldChange < 0').nlargest(n_genes, '-log10(pvalue)')

    elif n_genes and side == 'both':
        # Highlight top genes
        selected_genes = df.nlargest(n_genes, '-log10(pvalue)')

    # Filter the single-cell dataset for the selected genes
    subset_adata = adata[:, selected_genes.index].copy()
    subset_adata.var.index = subset_adata.var.index.str.split('_').str[0]

    # Convert the subset of adata to a DataFrame
    subset_df = subset_adata.to_df(layer=layer)

    # Merge the DataFrame with .obs to include the 'sample' information
    merged_df = pd.merge(subset_df, adata.obs[['sample']], left_index=True, right_index=True)

    # Melt the DataFrame to prepare for violin plot
    melted_df = pd.melt(merged_df, id_vars='sample', var_name='Gene', value_name='Counts')

    # Create a violin plot
    plt.figure(figsize=figsize)
    sns.violinplot(x='Gene', y='Counts', hue='sample', data=melted_df, split=True, inner='quartile', palette='Set2', **kwargs)
    sns.stripplot(x='Gene', y='Counts', hue='sample', data=melted_df, dodge=True, jitter=True, color='black', size=1, alpha=0.3, **kwargs)

    plt.xticks(rotation=45, ha='right', fontsize=label_font_size)
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left', fontsize=label_font_size)

    if not title:
        plt.title('Top Differentially Expressed Genes', fontsize=title_font_size)
    else:
        plt.title(title, fontsize=title_font_size)
    plt.show()


def write_top_DEGs(df, sample_id, result_dir='.', n_hits=200):
    df['-log10(pvalue)'] = - np.log10(df.pvalue)
    df.nlargest(n_hits, '-log10(pvalue)').to_csv(f'{result_dir}/{sample_id}_top_{n_hits}.csv')  # Adjust the number as needed
