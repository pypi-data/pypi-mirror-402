import numpy as np
import pandas as pd
from functools import partial
import re

from ..analysis import get_all_parent_go_terms


def parse_uniprot_mapping_results(
        uniprot_df: pd.DataFrame,
        protein_groups: list[str],
        special_column_aggregation_rules: dict = None,
        fill_in_go_hierarchy: bool = True,
):
    """
    params:
    uniprot_df: Dataframe of metadata from the UniProt ID mapper.
    protein_groups: List of strings, with protein groups, semicolon separated if they have multiple UniProt IDs in the group.

    returns:
    A new protein metadata table with rows combined according to the protein grouping.

    This function does not automatically retrieve UniProt metadata through an API,
        although this is an option if you trust their python code (see https://www.uniprot.org/help/id_mapping_prog).
    This function is only to simplify the process of combining rows when multiple UniProt IDs
        map to one protein group.

    First step is to parse out all UniProt IDs from the protein grouping results:
    Some will be semicolon separated, so treat each as individual uniprot.
    Example:

    uniprot_ids = set()
    for pg in YOUR_LIST_OF_PROTEIN_GROUPS:
        for uniprot_id in pg.split(';'):
            uniprot_ids.add(uniprot_id)
    # Write the UniProt IDs to your clipboard
    pd.Series(list(uniprot_ids)).to_clipboard(index=False)

    # Go to https://www.uniprot.org/id-mapping
    Let the mapping run (takes 1-2 minutes) and download all the results with the metadata columns you want.

    This code also includes the GO term hierarchy completion (see bja_utils.analysis.get_all_parent_go_terms)
        and puts all resulting GO terms in a column titled "all_GO_ids"
    """



    # The pandas groupby .agg() method expects a dictionary of {'column name': callable function or lambda}
    # Because this needs to be callable, we define the row_sep and out_sep using a functools partial
    column_agg_rules = {
        'Protein names': partial(deduplicate_across_rows, row_sep="; ", out_sep=";"),
        'Gene Names': partial(deduplicate_across_rows, row_sep=[";", " "], out_sep=";"),
        'Gene Ontology IDs': partial(deduplicate_across_rows, row_sep="; ", out_sep=";"),
        'Gene Names (primary)': partial(deduplicate_across_rows, row_sep="; ", out_sep=";"),
    }

    if special_column_aggregation_rules is not None:
        column_agg_rules = column_agg_rules.update(special_column_aggregation_rules)

    columns_to_keep = list(column_agg_rules.keys())

    newdf = pd.DataFrame(protein_groups, columns=['proteingroup'])
    newdf['uniprot_id'] = newdf['proteingroup'].str.split(';')
    newdf = newdf.explode('uniprot_id')

    # Do a check to see if any uniprot_id entries appear multiple times.
    # If any do, then that's a sign that protein grouping has the same UniProt ID found in multiple
    # protein groups, which might be unintended behavior by your data processing software
    uniprot_value_counts = newdf['uniprot_id'].value_counts()
    if any(uniprot_value_counts.loc[uniprot_value_counts > 1]):
        print('Warning: Some of your UniProt IDs were found in multiple groups, for example:')
        print(f"{uniprot_value_counts.index[0]} was found in {uniprot_value_counts.iloc[0]} protein groups")

    newdf = newdf.merge(uniprot_df, left_on='uniprot_id', right_on='From')
    newdf = newdf.groupby('proteingroup')[columns_to_keep].agg(column_agg_rules)

    if fill_in_go_hierarchy:
        all_go_ids = get_all_parent_go_terms(newdf, 'Gene Ontology IDs')
        newdf = newdf.join(all_go_ids)

    return newdf


def deduplicate_across_rows(values, row_sep: [str | list], out_sep: str):
    """
    Deduplicate words separated by `row_sep` across rows, then join the final list of de-duplicated
    words across the rows using `out_sep`.

    This is used for cleaning up results from UniProt when the protein group contains multiple
    UniProt IDs, and some info is duplicated across several UniProt ID rows.
    """
    if isinstance(row_sep, str):
        seps = [re.escape(row_sep)]
    else:
        seps = [re.escape(s) for s in row_sep]
    pattern = "|".join(seps)

    seen = set()
    tokens = []
    for val in values:
        if pd.isna(val):
            continue
        for part in re.split(pattern, val):
            if part and part not in seen:
                seen.add(part)
                tokens.append(part)
    joined = out_sep.join(tokens)
    if joined == "":
        joined = np.nan
    return joined
