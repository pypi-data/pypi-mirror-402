import typing
from functools import partial
from typing import Union, Iterable
from scipy.stats import fisher_exact, boschloo_exact
import pandas as pd
import numpy as np
import itertools
from scipy.spatial.distance import squareform
from scipy.cluster.hierarchy import linkage, fcluster

go_term_to_description_map = None
go_dag = None

def calculate_enrichment(
        data: pd.DataFrame,
        is_in_term_colname: str,
        is_de_colname: str,
        exact_test='fisher') -> dict:
    """
    Calculates a single enrichment test, useful for lipids where a lipid's group membership is
    easy to calculate. Takes in two boolean columns that get cross-tabulated into a
    2x2 contingency matrix, then the specified exact test is applied.

    Returns
    -------

    Results dictionary for the exact test, giving p-values for enrichment, depletion and two-sided alternatives.

    Parameters
    ----------
    data: a long-form pandas DataFrame that has your molecular feature's unique identifier on the index,
    and two boolean columns for the contingency table. It must contain all features,
    including all background features.

    is_in_term_colname: the column name for a bool column of whether the feature belongs to a GO term,
    or perhaps for a lipid enrichment, whether the feature is in that lipid class, or has a certain
    unsaturation count, etc.

    is_de_colname: the column name for a bool column whether the feature is de (Differentially Expressed)
    This could also be, for example, whether the feature belongs to a given group in the cross-ome
    hierarchical cluster.

    exact_test: select from 'fisher' or 'boschloo'. Fisher is fast, but not as good for low N.
    Boschloo is better for low N, but slower.


    """

    if is_in_term_colname not in data:
        raise ValueError

    if is_de_colname not in data:
        raise ValueError

    if exact_test not in ['fisher', 'boschloo']:
        raise ValueError

    if exact_test == 'fisher':
        exact_test = fisher_exact
    elif exact_test == 'boschloo':
        exact_test = partial(boschloo_exact, n=32)

    # To avoid errors with getting True/False in the correct order, change True to 1, and False to 0
    data = data.copy()
    data.replace(True, 1).replace(False, 0)

    crosstab = pd.crosstab(index=data[is_in_term_colname], columns=data[is_de_colname])

    result_twosided = exact_test(crosstab, alternative='two-sided')
    result_depletion = exact_test(crosstab, alternative='less')
    result_enrichment = exact_test(crosstab, alternative='greater')

    return {
        'two-sided': result_twosided.pvalue,
        'depletion': result_depletion.pvalue,
        'enrichment': result_enrichment.pvalue}


def protein_enrichment(
        data: pd.DataFrame,
        go_terms_colname: str,
        signif_change_colname: str = None,
        pvals_colname: str = None,
        pval_cutoff: float = 0.05,
        gene_colname: str = None,
        minimum_gene_count: int = 2
) -> pd.DataFrame:
    """
    Reads in a dataframe with common formatting to do GO term enrichment.

    Parameters
    ----------
    data: DataFrame with
        1. unique label for each feature in the index
        2. column with semicolon-separated GO terms for the feature
        3. (optional) p-values column
    Ensure that the resources contains all features detected, to define the background gene set.

    go_terms_colname: a column name for a column of semicolon-separated GO terms

    gene_colname: (optional) a column name for the column of gene names. Generates a column that
    lists the gene names found to be significantly changing.

    signif_change_colname: a string column name or iterable of bools indicating which features are significantly changing.

    pval_cutoff: if pvals_col is a column name, it uses this cutoff to determine significantly changing features.

    minimum_gene_count: The minimum Overlap denominator in the output to be included.
    """
    import json
    import numpy as np
    import gseapy as gp
    from scipy.stats import false_discovery_control
    from importlib.resources import files

    if go_terms_colname not in data:
        raise ValueError(f'go_terms_colname {go_terms_colname} not found')

    if gene_colname is not None and gene_colname not in data:
        raise ValueError(f'gene_colname {gene_colname} not found')

    if signif_change_colname is not None and pvals_colname is not None:
        raise ValueError('Use only one of `signif_change_colname` or `pvals_colname`'
                         'to select the significantly changing features.')

    if signif_change_colname is not None and \
            any([isinstance(value, bool) == False for value in data[signif_change_colname]]):
        raise ValueError('Not all values are boolean in signif_change_colname')

    if pvals_colname is not None and \
            any([isinstance(value, float) == False for value in data[pvals_colname]]):
        raise ValueError('Not all values are floats in pvals_colname')

    # if isinstance(signif_change_colname, str) and signif_change_colname not in data:
    #     raise ValueError(f'pvals_col {signif_change_colname} not found')
    # # if isinstance(pvals_col, str) and pvals_col not in resources or \
    # #         any([isinstance(value, float) == False for value in resources[pvals_col]]):
    # #     raise ValueError('pvals_col error')
    # else:
    #     # check that it is an equal length boolean column
    #     if len(data) != len(signif_change_colname) or any([isinstance(value, bool) == False for value in signif_change_colname]):
    #         raise ValueError

    if signif_change_colname is not None:
        signif_change_features = data.loc[data[signif_change_colname]].index.to_list()
    elif pvals_colname is not None:
        signif_change_features = data.loc[data[pvals_colname] < pval_cutoff].index.to_list()

    global go_term_to_description_map
    if go_term_to_description_map is None:
        map_path = files(package="bja_utils").joinpath("resources", "GO_term_description_map.json")
        go_term_to_description_map = json.load(open(map_path, 'r'))

    go_terms_to_features = get_goterm_to_features_dict(df=data, go_terms_colname=go_terms_colname)

    resultdf = gp.enrichr(
        gene_list=signif_change_features,
        gene_sets=go_terms_to_features,
        background=data.index
    ).results

    resultdf['num_significant'] = resultdf['Overlap'].str.split('/').str[0].astype('int')
    resultdf['num_in_go_term'] = resultdf['Overlap'].str.split('/').str[1].astype('int')
    resultdf = resultdf.loc[resultdf['num_significant'] >= minimum_gene_count]
    # Overwrite the existing Adjusted P-value column with new corrected values after filtering
    resultdf['Adjusted P-value'] = false_discovery_control(resultdf['P-value'], method='bh')
    resultdf.insert(5, '-log10(P-value)', -np.log10(resultdf['P-value']))
    resultdf.insert(5, '-log10(Adjusted P-value)', -np.log10(resultdf['Adjusted P-value']))
    resultdf.insert(2, 'Description', resultdf['Term'].map(go_term_to_description_map))
    resultdf = resultdf.sort_values('P-value')
    resultdf.rename({'Genes': 'Feature list'}, axis=1, inplace=True)

    if gene_colname is not None:
        feature_to_gene_map = {feature: gene for feature, gene in zip(data.index, data[gene_colname])}
        resultdf.insert(
            10,
            'Genes',
            resultdf['Feature list'].apply(
                lambda feature_list: _get_gene_list_from_features(feature_list, feature_to_gene_map))
        )

    return resultdf


def calculate_gsea(
    data: pd.DataFrame,
    quant_colnames: list[str],
    sample_groups: list[str],
    go_terms_colname: str,
    gene_colname: str = None,
    minimum_gene_count: int = 5,
    gsea_method: str = 'log2_ratio_of_classes',
    threads=20,
    **gsea_kwargs,
) -> pd.DataFrame:
    """
    Uses the GSEA method from the gseapy library.

    Available gsea methods:
    1. 'signal_to_noise'
    You must have at least three samples for each phenotype to use this metric.
    The larger the signal-to-noise ratio, the larger the differences of the means
    (scaled by the standard deviations); that is, the more distinct
    the gene expression is in each phenotype and the more the gene acts as a “class marker.”

    2. 't_test'
    Uses the difference of means scaled by the standard deviation and number of samples.
    Note: You must have at least three samples for each phenotype to use this metric.
    The larger the tTest ratio, the more distinct the gene expression is in each phenotype
    and the more the gene acts as a “class marker.”

    3. 'ratio_of_classes' (also referred to as fold change).
    Uses the ratio of class means to calculate fold change for natural scale data.

    4. 'diff_of_classes'
    Uses the difference of class means to calculate fold change for nature scale data


    5. 'log2_ratio_of_classes'
    Uses the log2 ratio of class means to calculate fold change for natural scale data.
    This is the recommended statistic for calculating fold change for log scale data.


    NOTES FOR DEVELOPMENT:
    the GSEA method in gseapy package has 3 required arguments:
    1. data: a dataframe with protein features on rows and samples on columns.
        Data are the quant values, typically log2, but it could be anything quantitative
        that you want to put into GSEA, for example, log2FC * -log10(p-value)
    2. gene_sets: this is the same as the gene_sets argument for the gp.enrichr() method in the
        GO term enrichment code (vide infra).
        It is a dictionary of {"GO:term12345": [Feature10, Feature99, ...]}
    3. cls: A list of strings, where each entry is the group that the sample column in data
        belongs to. It has to be in the same order as the data columns. And it must have 2 unique
        strings in the whole list, because GSEA only works on two different groups.


    """
    import numpy as np
    import gseapy as gp
    from scipy.stats import false_discovery_control
    from importlib.resources import files
    import json

    # if len(data) != len(metadata):
    #     raise ValueError('Data and metadata tables are not the same length.')
    # if sorted(list(data.index)) != sorted(list(metadata.index)):
    #     raise ValueError('Data index and metadata index are not identical.')

    global go_term_to_description_map
    if go_term_to_description_map is None:
        map_path = files(package="bja_utils").joinpath("resources", "GO_term_description_map.json")
        go_term_to_description_map = json.load(open(map_path, 'r'))

    go_term_to_features_map = get_goterm_to_features_dict(df=data, go_terms_colname=go_terms_colname)
    print('len go term to feature map dict: ', len(go_term_to_features_map))
    print('shape data with quant cols: ', data[quant_colnames].shape)

    gsea_obj = gp.gsea(
        data=data[quant_colnames],
        gene_sets=go_term_to_features_map,
        cls=sample_groups,
        no_plot=True,
        seed=43,
        min_size=minimum_gene_count,
        method=gsea_method,
        threads=threads,
        **gsea_kwargs,
    )

    resultdf = gsea_obj.res2d

    resultdf['num_significant'] = resultdf['Tag %'].str.split('/').str[0].astype('int')
    resultdf['num_in_go_term'] = resultdf['Tag %'].str.split('/').str[1].astype('int')
    resultdf = resultdf.loc[resultdf['num_significant'] >= minimum_gene_count]
    # Overwrite the existing Adjusted P-value column with new corrected values after filtering
    resultdf = resultdf.rename({'NOM p-val': 'P-value'}, axis=1)

    # for some reason, numeric columns are Object type, not a numeric type
    # so change to float to ensure that scipy false_discovery_control does not fail
    resultdf['P-value'] = resultdf['P-value'].astype(float)

    resultdf.insert(5, 'Adjusted P-value', false_discovery_control(resultdf['P-value'], method='bh'))
    resultdf.insert(5, '-log10(P-value)', -np.log10(resultdf['P-value']))
    resultdf.insert(5, '-log10(Adjusted P-value)', -np.log10(resultdf['Adjusted P-value']))
    resultdf.insert(2, 'Description', resultdf['Term'].map(go_term_to_description_map))
    resultdf = resultdf.sort_values('P-value')
    resultdf.rename({'Lead_genes': 'Feature list'}, axis=1, inplace=True)
    if 'FDR q-val' in resultdf.columns:
        resultdf = resultdf.drop('FDR q-val', axis=1)
    if 'FWER p-val' in resultdf.columns:
        resultdf = resultdf.drop('FWER p-val', axis=1)

    if gene_colname is not None:
        feature_to_gene_map = {feature: gene for feature, gene in zip(data.index, data[gene_colname])}
        resultdf.insert(
            10,
            'Genes',
            resultdf['Feature list'].apply(
                lambda feature_list: _get_gene_list_from_features(feature_list, feature_to_gene_map))
        )

    resultdf = resultdf.reset_index(drop=True)

    return resultdf, gsea_obj


def _parse_go_terms_string(entry):
    if not isinstance(entry, str):
        return []
    split = entry.split(';')
    split = [go_term.strip() for go_term in split]  # Remove white space
    return split


def get_goterm_to_features_dict(df, go_terms_colname):
    """
    Make a dictionary that maps each GO term like "GO:0001234" to list of features
    Used for both the GO term enrichment (gp.enrichr) and GSEA (gp.gsea) pipelines.
    """
    df['go_term_list'] = df[go_terms_colname].apply(_parse_go_terms_string)

    features_to_go_terms = {
        feature: go_term_list for feature, go_term_list in zip(df.index, df['go_term_list'])
    }

    if '' in features_to_go_terms:
        features_to_go_terms.pop('')

    go_terms_to_features = {}
    for feature, go_term_list in features_to_go_terms.items():
        for go_term in go_term_list:
            if go_term not in go_terms_to_features:
                go_terms_to_features[go_term] = []
            go_terms_to_features[go_term].append(feature)

    return go_terms_to_features


def _get_gene_list_from_features(feature_list, feature_to_gene_map):
    result = []
    for feature in feature_list.split(';'):
        result.append(str(feature_to_gene_map[feature]))
    return ';'.join(result)


def _old_version_download_go_term_graph():
    """
    Previous method for downloading the GO graph using the old API of goatools.

    Downloads and returns the directed acyclic graph (DAG) of all GO terms from a website with up-to-date
    annotations.
    """
    from goatools.base import download_go_basic_obo
    from goatools.obo_parser import GODag

    # Download GO terms
    obo_file = download_go_basic_obo()

    # Parse GO terms
    goterms = GODag(obo_file)

    return goterms


def download_go_term_graph(go_obo_file_url='https://current.geneontology.org/ontology/go-basic.obo'):
    """
    Downloads the .obo file from the GO website, and constructs a directed acyclic graph
    (DAG) object using goatools.obo_parser.
    """
    import urllib.request
    import tempfile
    from goatools.obo_parser import GODag
    import os

    # Use a temporary directory to automatically delete the .obo file after downloading from the URL
    with tempfile.TemporaryDirectory() as tmpdir:
        obo_path = os.path.join(tmpdir, "go-basic.obo")
        urllib.request.urlretrieve(go_obo_file_url, obo_path)
        go_dag = GODag(obo_path, load_obsolete=True)

        return go_dag


def get_all_parent_go_terms(df, go_terms_colname):
    """
    Finds all parent GO term IDs given a dataframe with semicolon separated GO terms.

    Useful for populating your UniProt-derived GO term lists with the whole hierarchy,
    because the point where UniProt stops listing parent GO terms is arbitrary,
    and therefore you might be missing annotations for higher-level GO terms.
    """
    gograph = download_go_term_graph()

    feature_go_ids = {}
    for i, gos in df[go_terms_colname].items():
        if pd.isna(gos):
            continue
        gos = gos.split(';')
        gos = [x.strip() for x in gos]
        all_go_ids = []
        for go in gos:
            go_node = gograph.get(go)
            if go_node is None:
                continue
            go_ids = _get_go_ids_recursively(go_node, ids=[go])
            all_go_ids.extend(go_ids)

        # Add in the list of GO terms from the uniprot list, because sometimes they get missed for unknown reason
        feature_go_ids[i] = ';'.join(sorted(list(set(list(all_go_ids) + list(gos)))))

    all_go_ids = pd.Series(feature_go_ids, name='all_GO_ids')

    return all_go_ids


def get_protein_counts_in_children_of_go_id(parent_go_id, df, go_terms_colname):
    """
    Input a parent GO ID, and your metadata table with a string of GO IDs in one column.

    Returns a dataframe with the number of features that match one of the children GO IDs of that parent GO ID.

    For reference, the three high-level GO terms:
        Molecular function: GO:0003674
        Cellular compartment: GO:0110165
        Biological process: GO:0008150

    Use code like this to make the plot:

        pltdf = resultdf.copy(); title = 'biological process (BP)'; alttitle = 'biological process'; shorttitle = 'biological_process_prot_counts'; cutoff_num = 10
        remainingrows = pltdf.loc[~(pltdf['num'] > cutoff_num), 'num']
        num_other_go_terms = remainingrows.shape[0]
        remainingcount = remainingrows.sum()
        pltdf = pltdf.loc[pltdf['num'] > cutoff_num]
        pltdf.loc['remaining'] = {'id': '-', 'name': f'{num_other_go_terms} other GO terms', 'Features': None, 'num': remainingcount}
        pltdf = pltdf.replace('Num without go term', f'No GO {alttitle} annotation')
        pltdf = pd.concat([pltdf.iloc[:-2], pltdf.iloc[[-1]], pltdf.iloc[[-2]]])  # re-arrange the rows to put the Num Without row last
        pltdf['pos'] = range(len(pltdf))
        fig, ax = plt.subplots(figsize=(1.5, 3), dpi=200)
        ax.barh(pltdf['pos'], pltdf['num'])
        ticklabels = [x.replace('biological process involved in', '') + ('' if (not y or y == '-') else ' [' + y + ']') for x, y in zip(pltdf['name'], pltdf['id'])]
        for i, row in pltdf.iterrows():
            ax.text(s=row['num'], x=row['num'] + 3, y=row['pos'], ha='left', va='center', fontsize=6.5)
        ax.set_xticks([])
        ax.tick_params(length=0)
        ax.set_yticks(pltdf['pos'], ticklabels, rotation=0)
        ax.invert_yaxis()
        ax.margins(x=0, y=0.02)
        ax.set_title(f'Number of proteins identified in\nGO {title} sub-categories')
        sns.despine(bottom=True)
    """
    gograph = download_go_term_graph()

    children_ids = [[x.id, x.name] for x in gograph.get(parent_go_id).children]

    go_id_to_prots = []
    for go_id, go_term_name in children_ids:
        features_with_go_term = list(df.loc[df[go_terms_colname].str.contains(go_id, na=False)].index)
        go_id_to_prots.append(
            {'id': go_id, 'name': go_term_name, 'features': features_with_go_term, 'num': len(features_with_go_term)})

    resultdf = pd.DataFrame(go_id_to_prots).sort_values('num', ascending=False)
    resultdf = resultdf.reset_index(drop=True)

    all_features_with_any_child_go_term = set()
    for i, row in resultdf.iterrows():
        for feature in row['features']:
            all_features_with_any_child_go_term.add(feature)
    num_with_go_term = len(all_features_with_any_child_go_term)
    num_without_go_term = len(df) - num_with_go_term

    resultdf.loc['Num without go term'] = {
        'id': None,
        'name': 'Num without go term',
        'features': None,
        'num': num_without_go_term}

    return resultdf


def _get_go_ids_recursively(go_node, ids=None):
    """
    Iterate through parents of the GO hierarchy to get every GO term ID in the hierarchy.
    Returns the list of all GO terms.
    """
    if ids is None:
        ids = []

    # Add the current node's id to the list
    ids.append(go_node.id)

    # Recursively process each child
    for parent in go_node.parents:
        _get_go_ids_recursively(parent, ids)

    return ids


def find_minimum_set_of_go_terms(
        features_to_go_terms_dict,
        min_features: int,
        max_features: int,
        target_coverage: float,
        required_go_terms: list = None,
        go_terms_to_leave_out: list = None,
        max_overlap=3,
        include_bp=True,
        include_cc=True,
        include_mf=True,
):
    """
    This method answers the question, What is the smallest set of GO terms that will cover some percent
        of your proteins, while avoiding using the overly broad, high-level GO terms with hundreds to thousands
        of genes in them?

    Method is useful for making a high-level overview of your proteins by separating them into groups that have minimal overlap.
    Also useful for selecting the best set of GO terms to plot after doing GSEA or other enrichment.

    Uses a greedy algorithm that checks for the next GO term that will include the largest number of features not yet included.

    Returns:
    A 4-Tuple of (
        The list of GO terms selected,
        The set of features covered by these GO terms,
        The intersection of features each combo of GO terms,
        The size of the intersection for each combo,
    )

    params:

    features_to_go_terms_dict: A dictionary of unique feature ID to a list (or a semicolon-separated string) of GO terms.

    min/max_features: Only include GO terms between these numbers of features

    target_coverage: float between (0.0, 1.0] indicating % of coverage it will aim to reach

    required_go_terms, go_terms_to_leave_out: force inclusion/exclusion of certain GO terms

    max_overlap: The maximum number of features that are allowed to overlap when a new GO term is added.
    Setting this to 0 means that each GO term will be totally in the features it covers, but you likely cannot reach your target_coverage percentage this way.

    include_bp/cc/mf: Whether to use terms if they fall under one of the 3 high-level namespaces:
        Biological Process, Cellular Component, Molecular Function.
    """
    from collections import defaultdict

    gograph = download_go_term_graph()

    # Count features associated with each GO term
    go_to_features = {}
    for feature, go_terms in features_to_go_terms_dict.items():
        if go_terms is None:
            continue
        if isinstance(go_terms, str):
            go_terms = go_terms.split(';')
        for go in go_terms:
            if go not in go_to_features:
                go_to_features[go] = []
            go_to_features[go].append(feature)

    # Filter GO terms to ensure it has the right number of features in it
    filtered_go_terms = {go: features for go, features in go_to_features.items()
                         if (len(features) >= min_features) and (len(features) <= max_features)}
    if go_terms_to_leave_out is not None:
        for go_term_to_leave_out in go_terms_to_leave_out:
            try:
                filtered_go_terms.pop(go_term_to_leave_out)
            except KeyError:
                pass

    # Filter out terms that don't match the high-level namespace
    go_terms_to_remove = []
    for go_term in filtered_go_terms:
        entry = gograph.get(go_term)
        if entry is None:
            # I guess we skip this GO term if it doesn't have an entry? Seems safer.
            continue
        namespace = entry.namespace
        if namespace == 'biological_process' and include_bp is False:
            go_terms_to_remove.append(go_term)
        elif namespace == 'cellular_component' and include_cc is False:
            go_terms_to_remove.append(go_term)
        elif namespace == 'molecular_function' and include_mf is False:
            go_terms_to_remove.append(go_term)
    for go_term in go_terms_to_remove:
        filtered_go_terms.pop(go_term)

    if len(filtered_go_terms) == 0:
        raise ValueError('Zero GO terms remaining after filtering.')

    covered_features = set()
    required_features = int(len(features_to_go_terms_dict) * target_coverage)
    selected_go_terms = []

    if required_go_terms is not None:
        for required_go_term in required_go_terms:
            covered_features.update(
                go_to_features[required_go_term])  # Add the features from the required GO term to the covered features
            selected_go_terms.append(required_go_term)

    # Greedy algorithm that gets the GO term with the highest coverage
    while len(covered_features) < required_features and len(filtered_go_terms) > 0:

        filtered_go_terms = {go: features for go, features in filtered_go_terms.items()
                             if len(set(features) & covered_features) <= max_overlap}

        if not filtered_go_terms:
            print("No more GO terms satisfy the max_overlap constraint.")
            break

        # Select the GO term that covers the greatest number of features not yet included
        best_go = max(filtered_go_terms,
                      key=lambda go: len(set.difference(set(filtered_go_terms[go]), covered_features)))
        selected_go_terms.append(best_go)
        covered_features.update(filtered_go_terms[best_go])
        # Remove the selected GO term from the pool
        del filtered_go_terms[best_go]

    # Count the number of intersections between each of the GO terms
    intersections = {}
    intersections_sizes = {}
    for go_term1 in selected_go_terms:
        intersections[go_term1] = {}
        intersections_sizes[go_term1] = {}
        for go_term2 in selected_go_terms:
            intersection = set.intersection(set(go_to_features[go_term1]), set(go_to_features[go_term2]))
            intersection_size = len(intersection)
            intersections[go_term1][go_term2] = intersection
            intersections_sizes[go_term1][go_term2] = intersection_size

    return selected_go_terms, covered_features, intersections, intersections_sizes


def get_go_data_table():
    # example code for parsing the DAG into a tabular data format
    godb = []

    go_dag = download_go_term_graph()

    for key, g in go_dag.items():
        godb.append({
            'id': g.id,
            'name': g.name,
            'namespace': g.namespace,
            'parent_ids': ';'.join(g._parents),
            'parent_names': ';'.join([value.name for value in g.parents]),
            'children_ids': ';'.join([value.id for value in g.children]),
            'children_names': ';'.join([value.name for value in g.children]),
            'is_obsolete': g.is_obsolete,
            'alt_ids': ';'.join(g.alt_ids)
        })

    godb = pd.DataFrame(godb)
    godb = godb.drop_duplicates('id')
    godb = godb.set_index('id')

    return godb


def prune_by_overlap(term_to_feature_ids: dict, threshold=0.2):
    """
    Prune terms based on gene set overlap using a Jaccard similarity threshold.
    Note that this method is O(n^2) or even O(logn n^2), so try to limit to below 1000 GO terms.

    Method works by evaluating pairwise Jaccard similarities between all GO terms with their
    similarity, clustering them based on the similarity, and selecting one
    representative term per cluster with the largest associated gene set.

    Parameters
    ----------
    term_to_feature_ids : dict[str, set]
        Map of GO terms to the set of unique feature IDs that you detected.
        Generate this list using method `get_goterm_to_features_dict`

    threshold : float
        A cutoff value (between 0 and 1)
        NOTE: Lower threshold is stricter and reduces the number of resulting GO terms.

    Returns
    -------
    list
        A list of representative terms, one for each cluster, chosen based
        on the largest gene set within each cluster.
    """
    terms = list(term_to_feature_ids.keys())
    n = len(terms)
    jaccard = np.zeros((n, n))
    for i, j in itertools.combinations(range(n), 2):
        A, B = set(term_to_feature_ids[terms[i]]), set(term_to_feature_ids[terms[j]])
        jaccard[i, j] = jaccard[j, i] = len(A & B) / len(A | B)
    dist = 1 - jaccard
    np.fill_diagonal(dist, 0)
    clusters = fcluster(
        Z=linkage(squareform(dist), method='average'), t=1-threshold, criterion='distance')

    keep = []
    for cluster_id in np.unique(clusters):
        members = [terms[i] for i, c in enumerate(clusters) if c == cluster_id]
        # pick the one with the largest gene set
        best = max(members, key=lambda t: len(term_to_feature_ids[t]))
        keep.append(best)
    return keep


def prune_redundant_terms(go_terms: typing.Iterable) -> list:
    """
    Prunes redundant Gene Ontology (GO) terms by removing parent terms whose
     descendent GO terms are already in the input.
    The list tends to retain only the most specific GO terms deep in the hierarchy.
    To retain more high-level GO terms, you could pre-filter your list before this function:
     For example, a pre-filter could be to define a GO term depth as a
      distance from the top-level CC/MF/BP, then retain only
      GO terms that have at most some depth.

    Parameters:
    go_terms : Iterable
        List of GO terms to be filtered for redundancy.

    Returns:
    list
        A list of non-redundant GO terms. Parent terms are removed if their
        child terms are also present in the input collection.
    """
    global go_dag
    if go_dag is None:
        go_dag = download_go_term_graph()

    keep = set(go_terms)
    for term in go_terms:
        for descendant in go_dag[term].get_all_children():
            if descendant in go_terms:
                keep.discard(go_dag[term].id)  # drop parent if child also significant
                break
    return list(keep)
