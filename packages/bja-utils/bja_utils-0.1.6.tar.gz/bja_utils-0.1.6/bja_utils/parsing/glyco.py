import re


def get_peptide_modification_locations(peptide_string):
    """
    Extracts amino acid positions and any modifications inside parentheses from a peptide string.

    The peptide string will include modifications in parentheses, e.g., "PEP(UniMod:35)TID(1234.5678)E".
    This function returns:
      - a dictionary mapping amino acid positions (1-indexed) to their modifications
      - a dictionary mapping amino acid positions to the amino acid letter

    Parameters:
        peptide_string (str): A peptide string potentially containing modifications in parentheses.

    Returns:
        tuple[dict[int, str], dict[int, str]]:
            - modifications: {aa_index: annotation_inside_parentheses}
            - residues: {aa_index: amino_acid_letter}
    """

    modifications = {}
    residues = {}
    i = 0  # character index in string
    aa_index = 1  # position in peptide sequence, start at 1 for natural counting of residue positions

    while i < len(peptide_string):
        if peptide_string[i] == '(':
            close_parentheses_index = peptide_string.find(')', i)
            if close_parentheses_index == -1:
                raise ValueError('Malformed peptide string')
            annotation = peptide_string[i + 1:close_parentheses_index]
            modifications[aa_index - 1] = annotation
            i = close_parentheses_index + 1
        else:
            residues[aa_index] = peptide_string[i]
            aa_index += 1
            i += 1

    return modifications, residues


def parse_glycan_formula(glycan_formula):
    """
    Parses a string like "Hex(2)HexNAc(1)" into a dictionary of {'monomer': count}.

    This glycan formula format is used in FragPipe's glyco module.
    """
    result = {}
    split = glycan_formula.split(')')
    for entry in split[:-1]:
        subset = entry.split('(')
        monomer = subset[0]
        count = subset[1]
        if monomer in result:
            result[monomer] += int(count)
        else:
            result[monomer] = int(count)

    return result






