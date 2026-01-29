from typing import Iterable

import pandas as pd
import numpy as np
from scipy.stats import t as t_dist


def calculate_pearson_spearman_pvalue():
    raise NotImplementedError


def _calculate_correlation_matrix(
    omic_dfs: Iterable[pd.DataFrame],
    method='pearson',
    do_self_correlation=False
    ) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Arguments
    ---------
    omic_dfs:
        List of pandas DataFrames with the features on the columns and samples on the rows.
        All sample indexes must be identical between each dataframe.

    method:
        Correlation method, choose from 'pearson', 'spearman', or 'kendall'

    do_self_correlation:
        Whether to include the within-ome correlation in the final results, for example,
        caLculate correlations for protein feature to protein feature

    Returns
    -------
    A 2-tuple of DataFrames with the correlation matrix and the associated p-value matrix
    """
    if len(omic_dfs) != 2:
        raise ValueError('Must have 2 omics dataframes in omic_dfs.')

    df1 = omic_dfs[0]
    df2 = omic_dfs[1]

    if len(set(df1)) != len(df1) or len(set(df2)) != len(df2):
        raise ValueError('Some entries in the sample index are not unique. Ensure all indexes are unique.')

    # Check whether the indexes are all equal
    if set(df1.index) != set(df2.index) or len(df1) != len(df2):
        raise ValueError('Ome dataframes do not have identical indexes.')

    if method not in ['pearson', 'spearman', 'kendall']:
        raise ValueError('Method must be one of `pearson`, `spearman` or `kendall`.')

    if method == 'kendall':
        raise NotImplementedError('kendall tau not implemented')

    # Concatenate along the samples on rows and do the correlation
    cdf = pd.concat(omic_dfs).corr(method=method)

    # Remove the within-ome correlation values, if needed.
    if do_self_correlation == False:
        cdf = cdf.loc[df1.columns, df2.columns]

    n_samples = len(df1)

    if method == 'pearson' or method == 'spearman':
        t_stats = (cdf * np.sqrt(n_samples - 2)) / (np.sqrt(1 - (cdf**2)))
        pvals = 2 * t_stats.apply(lambda x: t_dist.sf(np.abs(x), df=(n_samples - 2)))

    if method == 'kendall':
        raise NotImplementedError('kendall tau not implemented')

    return cdf, pvals


def _calculate_ideal_cluster_numbers():
    """
    Use the Silhouette score or the Calinski-Harabasz method to create an elbow plot to assess
    the ideal number of clusters in the hierarchical clustering.
    """
    raise NotImplementedError





