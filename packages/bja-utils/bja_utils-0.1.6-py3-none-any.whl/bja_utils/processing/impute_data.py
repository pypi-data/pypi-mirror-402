import pandas as pd
import numpy as np

def impute_data(df, width=0.3, downshift=1.8, min_num_non_missing=3, method='feature'):
    """
    Returns
    -------
    Returns 3 dataframes:
        1. The original DataFrame, minus columns that don't pass the `min_num_non_missing` filter.
        2. DataFrame with imputed values.
        3. DataFrame with booleans indicating whether a value was imputed.

    Parameters
    ----------
    df : DataFrame
        Input DataFrame with features as columns. Only Log2-transformed resources should be used.
    width : float
        The width to multiply the standard deviation of the non-missing values by, to get the imputed values' standard deviation.
    downshift : float
        The number of standard deviations below the mean of the non-missing values to use as the imputed values' mean.
    min_num_non_missing : int
        The minimum number of non-missing values required for a feature to be retained. Features below this cutoff will be dropped from the results.
    method: str
        One of 'feature', or 'all'. If feature, then calculate a distribution for each feature.
        If 'all', calculate the distribution across all features.

    Notes
    -----
    This imputation assumes missing resources in each column follows a normal distribution that is modeled with 2 assumptions:

        1. Missing resources has a narrower standard deviation "width" than the observed resources distribution.
        2. Missing resources has a lower mean, with a "downshift" by a factor of the standard deviation.

    Set `width` to a value less than 1, and `downshift` to the number of standard deviations subtracted from the mean.
    """

    np.random.seed(43)
    
    # Make a copy to avoid changing the original pandas dataframe
    df = df.copy()
    
    # Get a boolean vector of feature columns to keep based on the 'min number non missing' parameter
    features_to_keep = df.notnull().sum(axis=0)
    features_to_keep = features_to_keep >= min_num_non_missing

    num_features_removed = len(df.columns) - len(features_to_keep.loc[features_to_keep])
    print(f'Number of biomolecule features removed using min_num_non_missing={min_num_non_missing} filter: {num_features_removed} features removed.')

    num_na = df.isna().sum().sum()
    num_not_na = df.notna().sum().sum()
    percent_missing = round(num_na / (num_na + num_not_na) * 100, 2)
    print(f'Percent missing BEFORE filtering features: {percent_missing}%')


    # Filter the dataframe to have only the features that pass the filter
    df = df.loc[:, features_to_keep].copy()


    num_na = df.isna().sum().sum()
    num_not_na = df.notna().sum().sum()
    percent_missing = round(num_na / (num_na + num_not_na) * 100, 2)
    print(f'Percent missing AFTER filtering features: {percent_missing}%')

    if method == 'feature':
        # Create an empty dataframe that will hold the columns with imputed values
        imputed_df = pd.DataFrame([], index=df.index, columns=df.columns)

        # Create boolean dataframe indicating whether the values are imputed
        is_imputed_df = df.isnull()

        # Imputation on each column
        for col in df.columns:

            col_values = df[col].copy()  # copy the column to avoid changing the original

            missing_values_bool = col_values.isna()
            n_missing = missing_values_bool.sum()
            if n_missing == 0:
                # If no values are missing, just copy the same column over and continue
                imputed_df[col] = col_values
                continue

            found_values_sd = col_values.std(ddof=1)

            imputed_values_sd = width * found_values_sd # shrink sd width

            imputed_values_mean = col_values.mean() - (downshift * found_values_sd) # shift mean of imputed values

            random_values = np.random.normal(loc=imputed_values_mean, scale=imputed_values_sd, size=n_missing)
            col_values[missing_values_bool] = random_values

            # if random_values[random_values <= 0].any():
                # If any of the values are somehow <= 0, throw an exception because that's weirdly small values
                # raise ValueError("A value was found less than 0.")

            imputed_df[col] = col_values

        return (df, imputed_df, is_imputed_df)

    elif method == 'all':
        unique_index_name = '47f3640c-0dac-4bda-9088-5115ae3740ca'  # avoid accidentally overwriting a column name by using this randomly generated GUID

        df[unique_index_name] = df.index
        melt = df.melt(id_vars=unique_index_name)
        melt['is_imputed'] = melt['value'].isna()
        melt['imputed_value'] = melt['value']

        found_values_mean = np.nanmean(melt['value'])
        found_values_std = np.nanstd(melt['value'])

        imp_mean = found_values_mean - (found_values_std * downshift)
        imp_std = found_values_std * width

        random_imputed_values = np.random.normal(loc=imp_mean, scale=imp_std, size=len(melt.loc[melt['is_imputed']]))
        random_imputed_values

        melt.loc[melt['is_imputed'], 'imputed_value'] = random_imputed_values
        
        melt = melt.rename({unique_index_name: 'sample_id'}, axis=1)

        filtered_and_not_imputed = melt.pivot(index='sample_id', columns='variable', values='value')
        is_imputed_df = melt.pivot(index='sample_id', columns='variable', values='is_imputed')
        imputed_results = melt.pivot(index='sample_id', columns='variable', values='imputed_value')

        return (filtered_and_not_imputed, imputed_results, is_imputed_df)


    else:
        raise ValueError('Invalid imputation method.')