import numpy as np
import pandas as pd
import scipy

from concurrent.futures import ProcessPoolExecutor
from functools import partial
import os


def multiprocess_corr(df1, df2, n_processes=-1, method='kendall'):
    """
    Input two dataframes with the same order on the index, and the vectors you want to correlate on the columns.

    if n_processes = -1, uses your number of CPU cores - 1, otherwise use the number specified
    """
    if method == 'kendall':
        corr_func = scipy.stats.kendalltau
    elif method == 'pearson':
        corr_func = scipy.stats.pearsonr
    elif method == 'spearman':
        corr_func = scipy.stats.spearmanr
    else:
        raise ValueError('Method must be one of `pearson`, `spearman` or `kendall`')

    if n_processes == -1:
        n_processes = max(1, os.cpu_count() - 1)

    print(f'Using {n_processes} CPU cores.')

    df2split = np.array_split(df2, indices_or_sections=n_processes, axis=1)

    inputs = []
    for i, df2_subset in zip(range(n_processes), df2split):
        inputs.append([df1.copy(), df2_subset.copy()])

    # Partial in the functional programming sense, not a statistical sense
    partial_corr = partial(_corr, corr_func=corr_func)

    with ProcessPoolExecutor(max_workers=n_processes) as executor:
        results = list(executor.map(partial_corr, inputs))

    coefs = [result[0] for result in results]
    pvalues = [result[1] for result in results]

    # rebuild the results into a whole dataframe
    allcoefdf = pd.concat([pd.DataFrame(coef) for coef in coefs])
    allpvaluesdf = pd.concat([pd.DataFrame(pval) for pval in pvalues])

    return {'corrs': allcoefdf, 'pvals': allpvaluesdf}

def _corr(dfs: list, corr_func):

    df1 = dfs[0]
    df2 = dfs[1]

    corr_coef_results = {}
    corr_pvalue_results = {}

    for i1, values1 in df1.items():
        corr_coef_results[i1] = {}
        corr_pvalue_results[i1] = {}

        for i2, values2 in df2.items():
            c = corr_func(values1, values2)
            corr_coef_results[i1][i2] = c.statistic
            corr_pvalue_results[i1][i2] = c.pvalue

    return (corr_coef_results, corr_pvalue_results)





