from .lipids import (
    get_lipid_categories_with_goslin,
    parse_lipid_goslin,
    ParsedLipid,
    contains_odd_chain,
    is_saturated,
    is_unsaturated,
    is_polyunsaturated,
    get_lipid_class_abbreviations_dict,
    get_lipid_superclass_dict,
    get_fatty_acyls_per_lipid_class_dictionary,
    get_avg_unsaturations_group,
    get_avg_chain_length_group,
    get_lipid_categories_simple,
    get_num_fatty_acyls_in_lipid_class,
)

from .glyco import (
    get_peptide_modification_locations,
    parse_glycan_formula,
)

from .parse_uniprot import (
    parse_uniprot_mapping_results
)

