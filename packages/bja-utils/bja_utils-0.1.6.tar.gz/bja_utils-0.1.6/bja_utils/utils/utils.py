from scipy.stats import ttest_1samp, ttest_rel
import numpy as np
from collections import OrderedDict


def significance_size(row, cutoff=1, pval_col='p-value', l2fc_col='Log2 fold change', pval_cutoff=0.05):
    if row[pval_col] > pval_cutoff:
        return 1
    elif abs(row[l2fc_col]) < cutoff:
        return 2
    else:
        return 3


def add_suffix_to_dupes(df, colname, first_part=' [#', second_part=']'):
    """
    Adds a ` [#1]`, ` [#2] etc. to the end of a string column if duplicates are found.

    Define the format of the added string with `first_part` and `second_part`

    Returns a new Series.
    """
    return df[colname].where(~df[colname].duplicated(keep=False),
                             df[colname].astype('str') +
                             first_part +
                             (df.groupby(colname).cumcount() + 1).astype(str) +
                             second_part)


def calc_ttest_paired(
        leftquants=None,
        rightquants=None,
        quantsdf=None,
        leftsamples=None,
        rightsamples=None,
        calculate_conf_int=True,
    ):

    if quantsdf is not None:
        if leftsamples is None or rightsamples is None:
            raise ValueError("Must provide both leftsamples and rightsamples when using quantsdf.")
        try:
            leftquants = quantsdf[leftsamples]
            rightquants = quantsdf[rightsamples]
        except KeyError as e:
            raise KeyError(f"Sample not found in quantsdf columns: {e}")

    if leftquants is None or rightquants is None:
        raise ValueError("Must provide either quantsdf+samples or both leftquants and rightquants.")

    leftquants = np.asarray(leftquants, dtype=float)
    rightquants = np.asarray(rightquants, dtype=float)

    if leftquants.shape != rightquants.shape:
        raise ValueError("For paired t-test, left and right arrays must have identical shapes.")

    diffmeans = np.mean(rightquants - leftquants)
    tt = ttest_rel(rightquants, leftquants, nan_policy="omit")

    if calculate_conf_int:
        conf_int = tt.confidence_interval(confidence_level=0.95)
        return {'diffmeans': diffmeans, 'pval': tt.pvalue,
                'ci_low': conf_int.low, 'ci_high': conf_int.high}

    return {'diffmeans': diffmeans, 'pval': tt.pvalue}


def calc_ttest_ind(
        leftquants=None,
        rightquants=None,
        quantsdf=None,
        leftsamples=None,
        rightsamples=None,
        equal_var=True,
        calculate_conf_int=True,
        ):

    # Infer quants from dataframe if provided
    if quantsdf is not None:
        if leftsamples is None or rightsamples is None:
            raise ValueError("Must provide both leftsamples and rightsamples when using quantsdf.")
        try:
            leftquants = quantsdf[leftsamples]
            rightquants = quantsdf[rightsamples]
        except KeyError as e:
            raise KeyError(f"Sample not found in quantsdf columns: {e}")

    # Check required arrays are available
    if leftquants is None or rightquants is None:
        raise ValueError("Must provide either quantsdf+samples or both leftquants and rightquants.")

    # Ensure inputs are numeric arrays
    leftquants = np.asarray(leftquants, dtype=float)
    rightquants = np.asarray(rightquants, dtype=float)

    if leftquants.size == 0 or rightquants.size == 0:
        raise ValueError("Empty input arrays are not allowed.")

    # Compute mean difference and t-test
    diffmeans = np.mean(rightquants) - np.mean(leftquants)
    tt = ttest_ind(rightquants, leftquants, equal_var=equal_var, nan_policy="omit")

    if calculate_conf_int:
        conf_int = tt.confidence_interval(confidence_level=0.95)
        return {'diffmeans': diffmeans, 'pval': tt.pvalue,
                'ci_low': conf_int.low, 'ci_high': conf_int.high}

    return {'diffmeans': diffmeans, 'pval': tt.pvalue}


class SimpleLRUCache:
    """
    A thin wrapper around an Ordered Dictionary that discards the
    Least Recently Used (LRU) object after the capacity is reached.

    So after 11 items have been put in, it removes the 11th item.
    """
    def __init__(self, capacity=10):
        self.capacity = capacity
        self.store = OrderedDict()

    def __getitem__(self, key):
        if key in self.store:
            self.store.move_to_end(key)
            return self.store[key]
        raise KeyError(key)

    def __setitem__(self, key, value):
        if key in self.store:
            self.store.move_to_end(key)
        self.store[key] = value
        if len(self.store) > self.capacity:
            print('popped item from cache')
            self.store.popitem(last=False)

    def __contains__(self, key):
        return key in self.store
