import pandas as pd

def get_statsmodels_linear_model_results(fitted_model, terms_to_ignore=None):
    """
    Returns a DataFrame with 4 results from each linear model for each level of the covariates:
        1. Effect size
        2. p-value
        3. Confidence interval (2.5%, low)
        4. Confidence interval (97.5%, high)

    The returned df can be added to a list for concatenation into a final long-form dataframe of all features.
    """

    results = []
    for variable, value in fitted_model.params.items():
        if terms_to_ignore is not None and variable in terms_to_ignore:
            continue
        results.append({'type': 'effectsize', 'variable': variable, 'value': value})

    for variable, value in fitted_model.pvalues.items():
        if terms_to_ignore is not None and variable in terms_to_ignore:
            continue
        results.append({'type': 'pval', 'variable': variable, 'value': value})

    ci = fitted_model.conf_int()
    for variable, value in ci[0].items():
        if terms_to_ignore is not None and variable in terms_to_ignore:
            continue
        results.append({'type': 'ci_low', 'variable': variable, 'value': value})
    for variable, value in ci[1].items():
        if terms_to_ignore is not None and variable in terms_to_ignore:
            continue
        results.append({'type': 'ci_high', 'variable': variable, 'value': value})

    return pd.DataFrame(results)


def tau_specificity(x) -> float:
    """
    Compute the sample-specificity metric for a feature across samples.
    This metric is based on the following:
        https://pmc.ncbi.nlm.nih.gov/articles/PMC5444245
    Tau=0 indicates the feature is found across most samples, and doesn't vary much.
    Tau=1 means the feature is only found in a few samples, or has an extreme variance profile.
    Importantly, the score is scale-invariant and is normalized to relative values across tissues.
    Ignores missing values, and if no variation exists, returns NaN or 0.
    """
    import numpy as np

    x = np.asarray(x, float)

    # check whether values are real
    if np.all(~np.isfinite(x)):
        return np.nan
    # check whether there is any variance at all
    if np.nanmax(x) == np.nanmin(x):
        return np.nan

    x0 = x - np.nanmin(x)
    m = np.nanmax(x0)
    if m == 0:
        return 0.0
    return np.nanmean(1 - (x0 / m))
