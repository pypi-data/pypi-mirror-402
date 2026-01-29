import os
from itertools import combinations
from concurrent.futures import ProcessPoolExecutor
from functools import partial

import pandas as pd
import numpy as np
from scipy.stats import norm
from scipy.special import binom


def calculate_kendall_tau(x, y, indexes):
    """
    Calculates Kendall Tau correlation using the standard O(n2) implementation.

    Also includes data about the number of concordant and discordant pairs for each sample.
    """

    num_conc_pairs_per_sample = {idx: 0 for idx in indexes}

    concordant = 0
    discordant = 0
    binom_coef = binom(len(x), 2)
    n = len(x)

    for (i, j) in combinations(range(n), 2):
        # display(x)
        diff_x = x[i] - x[j]
        diff_y = y[i] - y[j]
        if diff_x * diff_y > 0:
            concordant += 1
            num_conc_pairs_per_sample[indexes[i]] += 1
            num_conc_pairs_per_sample[indexes[
                j]] += 1  ## Add both i and j indexes to the count dictionary to account for the triangle-shaped combinations of (i, j) that get generated
        elif diff_x * diff_y < 0:
            discordant += 1

    total_pairs = concordant + discordant
    prop_concordant = concordant / total_pairs if total_pairs else 0
    prop_discordant = discordant / total_pairs if total_pairs else 0

    kendall_corr_value = (((prop_concordant * binom_coef) - (prop_discordant * binom_coef)) / binom_coef)

    result = {
        'kendall corr': kendall_corr_value,
        'proportion concordant': prop_concordant,
        'proportion discordant': prop_discordant,
        'num concordant': prop_concordant * binom_coef,
        'num discordant': prop_discordant * binom_coef,
        'concordance per sample': num_conc_pairs_per_sample,
    }

    return result


def get_leverage_data(conc_per_sample_dict, groupsdf):
    """
    Each unique value in each column of groupsdf will be a column output in the result
    So make a mapping of ColumnName[T.{columnValue}] like how Statsmodels does
    """

    n_samples = len(conc_per_sample_dict)

    group_columns = groupsdf.columns

    temp_groupsdf = groupsdf.copy()

    temp_groupsdf['num concordant'] = temp_groupsdf.index.map(conc_per_sample_dict)

    all_grouped_stats = []

    for column in group_columns:
        grouped_stats = temp_groupsdf.groupby(column)['num concordant'].mean() / n_samples
        grouped_stats.index = [f'{column}[T.{index_value}]' for index_value in grouped_stats.index]
        all_grouped_stats.append(grouped_stats)

    all_grouped_stats = pd.concat(all_grouped_stats)

    return all_grouped_stats.to_dict()


def calculate_kendall_sample_influence(
        qdf1: pd.DataFrame,
        qdf2: pd.DataFrame,
        groupsdf: pd.DataFrame,
        display_progress=False):
    """
    Calculates the influence of each sample on the resulting Kendall correlation value, and gives
    group-wise influence as well from the groupsdf.

    Input:
    3 dataframes with the same indexes. Samples on the index, and features on the columns.
    All features will have their kendall correlation calculated.

    """

    if not (qdf1.index.identical(qdf2.index) and qdf1.index.identical(groupsdf.index)):
        raise ValueError('Indexes do not match between dataframes. Ensure that samples, not features, are ' +
                         'on the indexes and all are the same indexes without repeats.')

    n_samples = len(qdf1)
    sample_indexes = qdf1.index

    # Ensure all are indexed the same way and same order
    qdf2 = qdf2.loc[sample_indexes]
    groupsdf = groupsdf.loc[sample_indexes]

    res = []

    for feature_idx1 in qdf1.columns:
        if display_progress:
            print(feature_idx1)
        for feature_idx2 in qdf2.columns:
            kendall_res = calculate_kendall_tau(qdf1[feature_idx1].values, qdf2[feature_idx2].values, sample_indexes)
            res.append({'index1': feature_idx1, 'index2': feature_idx2, **kendall_res})

    rdf = pd.DataFrame(res)

    v_naught = n_samples * (n_samples - 1) * (2 * n_samples + 5)
    z_statistic_denominator = np.sqrt((1 / 18) * v_naught)
    z_statistics = (rdf['num concordant'] - rdf['num discordant']) / z_statistic_denominator
    rdf['p-value'] = z_statistics.abs().apply(norm.sf) * 2  # multiply by 2 to get two-tailed p-value.
    # Confirmed that this p-value calculation gives the same p-value as scipy.stats.kendalltau, when there are no ties in the data

    means = pd.DataFrame(rdf['concordance per sample'].apply(lambda x: get_leverage_data(x, groupsdf)).to_list())

    influence = 2 * means - 1

    return rdf, influence


def multiprocess_kendall_sample_influence(
        qdf1: pd.DataFrame,
        qdf2: pd.DataFrame,
        groupsdf: pd.DataFrame,
        n_processes: int = -1):
    """
    Calculates the influence of each sample on the resulting Kendall correlation value, and gives
    group-wise influence as well from the groupsdf.

    Input:
    3 dataframes with the same indexes. Samples on the index, and features on the columns.
    All features will have their kendall correlation calculated.


    """

    if n_processes == -1:
        n_processes = max(1, os.cpu_count() - 1)

    print(f'Using {n_processes} CPU cores.')

    qdf2split = np.array_split(qdf2, indices_or_sections=n_processes, axis=1)

    inputs = []

    for i, qdf2_subset in zip(range(n_processes), qdf2split):
        inputs.append([qdf1.copy(), qdf2_subset.copy(), groupsdf.copy()])

    with ProcessPoolExecutor(max_workers=n_processes) as executor:
        partial_func = partial(calculate_kendall_sample_influence)

        results = list(
            executor.map(partial_func, *zip(*inputs)))

    result_dfs = [result[0] for result in results]
    influence_dfs = [result[1] for result in results]

    all_results = pd.concat([pd.DataFrame(result_df) for result_df in result_dfs])
    all_influences = pd.concat([pd.DataFrame(influence_df) for influence_df in influence_dfs])

    return {'results': all_results, 'influences': all_influences}

