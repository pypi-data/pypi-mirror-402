import pandas as pd
from matplotlib import pyplot as plt
from adjustText import adjust_text


def rank_genes_to_df(adata, n=50):
    result = adata.uns['rank_genes_groups']

    groups = result['names'].dtype.names

    df = pd.DataFrame(
        {group + '_' + key: result[key][group]
         for group in groups for key in ['names', 'scores']}).head(n)

    return df


def add_marker_feature(adata, marker, marker_name, clusters_name, thr = 0, figsize=(10, 4)):

    adata.obs[marker_name] = ''
    adata.obs.loc[adata.to_df().loc[:,marker] <= thr, marker_name] = f'{marker}-'
    adata.obs.loc[adata.to_df().loc[:,marker] > thr, marker_name] = f'{marker}+'

    df = pd.concat([
        adata.obs.groupby([marker_name,clusters_name]).size()[f'{marker}+'],
        adata.obs.groupby([marker_name,clusters_name]).size()[f'{marker}-']
    ],axis=1).rename(columns={0:f'{marker}+',1:f'{marker}-'})

    # Make some labels.
    labels = df[f'{marker}+'] / df.sum(axis=1) * 100
    labels = labels.round(decimals=1)
    labels.sort_values(ascending=False,inplace=True)
    df = df.loc[labels.index,]

    ax = df.plot.bar(stacked=True,rot=0,figsize=figsize)

    rects = ax.patches

    for rect, label in zip(rects, labels):
        height = rect.get_height()
        ax.text(
            rect.get_x() + rect.get_width() / 2, height + 5, str(label) + "%",
            ha="center", va="bottom", fontsize=8
        )

    ax.set_yscale('log')
    ax.set_ylabel('# of cells')
    return ax


def run_adjust_text(x, y, labels, ax=None, use_arrow=True, font_weight='bold', font_size=8):
    texts = [
        plt.text(
            x[i], y[i], 
            labels[i],
            fontdict={'weight': font_weight, 'size': font_size},
            ha='center', va='center'
        ) for i in range(len(x))
    ]
    
    if use_arrow:
        adjust_text(texts, arrowprops=dict(arrowstyle='->', color='red'), ax = ax)
    else:
        adjust_text(texts, ax = ax)
