import re
import json
from importlib.resources import files

import pygoslin.domain.LipidAdduct
from pygoslin.domain.Element import Element
from pygoslin.parser.Parser import LipidParser
lipid_parser = None

fas_per_lipid_dictionary = None


# Make a regex pattern to remove extra text for sphingo, phytosphingo,
# and ether lipids from a fatty acyl split.
strings_to_remove = ['d', 'd-', 't', 't-', 'O-', 'P-']
regex_pattern = r"|".join(re.escape(s) for s in strings_to_remove)


def contains_odd_chain(lipid_str: str, num_fa_carbons=None):
    # Check whether number of carbons is odd
    if num_fa_carbons is not None and num_fa_carbons % 2 == 1:
        return True

    # Check individual fatty acids
    split = lipid_str.split(' ', maxsplit=1)
    if len(split) <= 1:
        return False  # something is weird with the lipid if only one split so we don't know
    fas = split[1].split('_')
    for fa in fas:
        try:
            fa_split = fa.split(':')
            fa_split_carbon_number = fa_split[0]
            fa_split_carbon_number = re.sub(regex_pattern, "", fa_split_carbon_number)
            fa_split_carbon_number = int(fa_split_carbon_number)
            if fa_split_carbon_number % 2 == 1:
                return True
        except:
            continue
    return False


class ParsedLipid:
    def __init__(self, original_lipid_string: str, parsed: pygoslin.domain.LipidAdduct.LipidAdduct):
        self.lipid_str = original_lipid_string
        self.lipid_class = original_lipid_string.split(' ', maxsplit=1)[0]

        self.parsed_goslin_obj = parsed
        self.lipid_class_goslin = parsed.get_extended_class()
        self.adduct_goslin = parsed.adduct
        self.lipid_str_goslin = parsed.get_lipid_string()
        self.num_fa_unsat = parsed.lipid.info.get_double_bonds()
        fa_elements_count = parsed.lipid.info.get_elements()
        self.num_fa_carbons = fa_elements_count[Element.C] + fa_elements_count[Element.C13]
        self.num_fa_moieties = parsed.lipid.info.poss_fa

        # poss_fa is the number of FAs that should be in the lipid class
        # num_specified_fa is the number of FAs that you gave
        self.is_sum_comp = parsed.lipid.info.num_specified_fa < parsed.lipid.info.poss_fa

    def __repr__(self):
        return f'Original: {self.lipid_str}\nGoslin parsed: {self.lipid_str_goslin}'


def parse_lipid_goslin(lipidstr):
    global lipid_parser
    if lipid_parser is None:
        lipid_parser = LipidParser()

    return ParsedLipid(lipidstr, lipid_parser.parse(lipidstr))


def get_lipid_categories_simple(lipidstr):
    """
    Uses simple regex parsing to determine the number of carbons and unsaturations in each fatty acyl.

    Does not use Goslin

    """

    lipid_class = lipidstr.split(' ')[0]

    fatty_acyls = lipidstr.split(' ', maxsplit=1)[1]  # split off the headgroup from the FAs

    fas_list = get_fatty_acyls_list_regex(fatty_acyls)

    num_fas_in_lipid_class = get_num_fatty_acyls_in_lipid_class(lipid_class)

    lipid_contains_odd_chain = contains_odd_chain(lipidstr)

    total_fa_unsats = sum([x['unsats'] for x in fas_list])
    total_fa_carbons = sum([x['carbons'] for x in fas_list])

    avg_fa_carbons = total_fa_carbons / num_fas_in_lipid_class
    avg_unsat_per_fa = total_fa_unsats / num_fas_in_lipid_class

    unsat_0 = avg_unsat_per_fa == 0
    unsat_0_1 = 0 < avg_unsat_per_fa <= 1
    unsat_1_2 = 1 < avg_unsat_per_fa <= 2
    unsat_2_3 = 2 < avg_unsat_per_fa <= 3
    unsat_3_4 = 3 < avg_unsat_per_fa <= 4
    unsat_4plus = 4 < avg_unsat_per_fa

    if unsat_0:
        unsat_group = 'saturated [0]'
    elif unsat_0_1:
        unsat_group = 'very low unsaturations (0-1]'
    elif unsat_1_2:
        unsat_group = 'low unsaturations (1-2]'
    elif unsat_2_3:
        unsat_group = 'medium unsaturations (2-3]'
    elif unsat_3_4:
        unsat_group = 'high unsaturations (3-4]'
    elif unsat_4plus:
        unsat_group = 'very high unsaturations (>4)'

    carbons_short = avg_fa_carbons <= 7
    carbons_med =  7 < avg_fa_carbons <= 13
    carbons_long =  13 < avg_fa_carbons <= 19
    carbons_very_long = avg_fa_carbons > 19

    if carbons_short:
        carbon_group = 'short chain (0-7]'
    elif carbons_med:
        carbon_group = 'med chain (7-13]'
    elif carbons_long:
        carbon_group = 'long chain (13-19]'
    elif carbons_very_long:
        carbon_group = 'very long chain (>19)'


    result = {
        'lipid_class': lipid_class,

        'average_fatty_acyl_chain_length': carbon_group,
        'average_fatty_acyl_unsats': unsat_group,

        'is_sat': total_fa_unsats == 0,
        'is_unsat': total_fa_unsats > 0,
        'is_monounsat': total_fa_unsats == 1,
        'is_polyunsat': total_fa_unsats >= 2,

        'avg_fa_carbons': avg_fa_carbons,
        'avg_fa_unsats': avg_unsat_per_fa,

        'contains_odd_chain_fa': lipid_contains_odd_chain,

        'is_short_chain_on_average_[0-7]': carbons_short,
        'is_med_chain_on_average_(7-13]': carbons_med,
        'is_long_chain_on_average_(13-19]': carbons_long,
        'is_very_long_chain_on_average_(>19)': carbons_very_long,

        'avg_[0]_unsat_per_FA': unsat_0,
        'avg_(0-1]_unsat_per_FA': unsat_0_1,
        'avg_(1-2]_unsat_per_FA': unsat_1_2,
        'avg_(2-3]_unsat_per_FA': unsat_2_3,
        'avg_(3-4]_unsat_per_FA': unsat_3_4,
        'avg_(>4)_unsat_per_FA': unsat_4plus,
    }

    return result




def get_lipid_categories_with_goslin(lipidstr):
    """
    Define categories the lipid belongs to, such as lipid class, whether it is saturated, polyunsaturated, whether it is short chain or long chain, etc.

    Useful for calculating enrichment of lipid categories.
    """

    raise NotImplementedError("The logic isn't working correct with the double nested try-except blocks.")

    global fas_per_lipid_dictionary

    if fas_per_lipid_dictionary is None:
        fas_per_lipid_dictionary = get_fatty_acyls_per_lipid_class_dictionary()

    used_workaround_1 = False  # whether we had to use CL as a workaround to ensure Goslin can parse the lipid FAs
    used_workaround_2 = False

    try:
        parsed = parse_lipid_goslin(lipidstr)
    except:
        # If you can't parse the lipid class with Goslin (for example, Cer[NDS] is an unknown lipid class that causes an error)
        #     then we can still use it, just replace the lipid class with "CL" (because it has 4 FAs, and it can handle
        #     even lipids with high FA counts.
        #     Next, let Goslin parse the fatty acids, but we know that it's another lipid class.
        used_workaround_1 = True
        fatty_acyls = lipidstr.split(' ', maxsplit=1)[1]  # split off the headgroup from the FAs

        try:

            workaround_modified_lipid = 'CL ' + fatty_acyls  # Add CL as a generic lipid class to the FAs
            # This ensures that the lipid FAs can be parsed with a maximum size lipid, CL, with 4 FAs
            print(workaround_modified_lipid)
            parsed = parse_lipid_goslin(workaround_modified_lipid)
        except:
            # Goslin still doesn't work, so don't mess with it and use the brute force regex parsing of the fatty acyls
            get_fatty_acyls_list_regex(fatty_acyls)

    # Get the original_lipid_class, to distinguish it from the Goslin-parsed lipid class which might be an error,
    # or might be CL if it doesn't know the lipid class and we used the CL workaround.
    original_lipid_class = lipidstr.split(' ', maxsplit=1)[0]

    if used_workaround_2:
        pass


    elif used_workaround_1:
        num_fas = fas_per_lipid_dictionary[original_lipid_class]
    else:
        num_fas = parsed.num_fa_moieties

    u = parsed.num_fa_unsat
    c = parsed.num_fa_carbons

    avg_fa_carbons = c / num_fas
    avg_unsat_per_fa = u / num_fas

    unsat_0 = avg_unsat_per_fa == 0
    unsat_0_1 = 0 < avg_unsat_per_fa <= 1
    unsat_1_2 = 1 < avg_unsat_per_fa <= 2
    unsat_2_3 = 2 < avg_unsat_per_fa <= 3
    unsat_3_4 = 3 < avg_unsat_per_fa <= 4
    unsat_4plus = 4 < avg_unsat_per_fa


    lipid_contains_odd_chain = contains_odd_chain(lipidstr)

    result = {
        'lipid_class': original_lipid_class,
        'is_short_chain_on_average': avg_fa_carbons <= 7,
        'is_med_chain_on_average': 7 < avg_fa_carbons <= 13,
        'is_long_chain_on_average': 13 < avg_fa_carbons <= 19,
        'is_very_long_chain_on_average': avg_fa_carbons > 19,
        'avg_fa_carbons': avg_fa_carbons,
        'avg_fa_unsats': avg_unsat_per_fa,
        'contains_odd_chain_fa': lipid_contains_odd_chain,
        'is_sat': u == 0,
        'is_unsat': u > 0,
        'is_monounsat': u == 1,
        'is_polyunsat': u >= 2,
        'avg_[0]_unsat_per_FA': unsat_0,
        'avg_(0-1]_unsat_per_FA': unsat_0_1,
        'avg_(1-2]_unsat_per_FA': unsat_1_2,
        'avg_(2-3]_unsat_per_FA': unsat_2_3,
        'avg_(3-4]_unsat_per_FA': unsat_3_4,
        'avg_(4plus)_unsat_per_FA': unsat_4plus,
    }

    return result


def get_fatty_acyls_list_regex(fatty_acyls_string: str):
    pattern = r'\d+:\d+(?:;O\d?)?'

    matches = re.findall(pattern, fatty_acyls_string)

    parsed = []
    for match in matches:
        carbons = int(match.split(':')[0])
        unsats_and_oxys_split = match.split(':')[1].split(';')
        unsats = int(unsats_and_oxys_split[0])
        if len(unsats_and_oxys_split) == 1:
            oxys = 0
        else:
            oxys = unsats_and_oxys_split[1]

            if oxys == 'O':
                oxys = 1
            else:
                oxys = int(oxys.replace('O', ''))

        parsed.append({'carbons': carbons, 'unsats': unsats, 'oxygens': oxys})

    return parsed


def get_avg_chain_length_group(avg_carbons_per_fa):
    if avg_carbons_per_fa <= 7:
        return 'short'
    if avg_carbons_per_fa <= 13:
        return 'medium'
    if avg_carbons_per_fa <= 19:
        return 'long'
    return 'very long'

def get_avg_unsaturations_group(avg_unsats_per_fa):
    if avg_unsats_per_fa == 0:
        return 'saturated'
    if avg_unsats_per_fa <= 1:
        return 'monounsaturated'
    if avg_unsats_per_fa <= 3:
        return 'polyunsaturated'
    return 'very polyunsaturated'


def is_saturated(num_unsaturations):
    return num_unsaturations == 0


def is_unsaturated(num_unsaturations):
    return num_unsaturations > 0


def is_polyunsaturated(num_unsaturations):
    return num_unsaturations > 1


def get_lipid_class_abbreviations_dict():
    class_abbrevs_path = files(package="bja_utils").joinpath("resources", "molec_class_abbrev.json")
    class_abbrevs = json.load(open(class_abbrevs_path, 'r'))
    return class_abbrevs


def get_lipid_superclass_dict():
    superclasses_path = files(package="bja_utils").joinpath("resources", "compound_superclasses.json")
    superclasses = json.load(open(superclasses_path, 'r'))
    return superclasses


def get_fatty_acyls_per_lipid_class_dictionary():
    global fas_per_lipid_dictionary

    if fas_per_lipid_dictionary is None:
        path = files(package='bja_utils').joinpath('resources', 'fatty_acyls_per_lipid_class.json')
        fas_per_lipid_dictionary = json.load(open(path, 'r'))

    return fas_per_lipid_dictionary


def get_num_fatty_acyls_in_lipid_class(lipidclass: str):
    fas_dict = get_fatty_acyls_per_lipid_class_dictionary()

    if lipidclass in fas_dict:
        return fas_dict[lipidclass]

    raise KeyError(f'Lipid class: {lipidclass} does not exist in the bja_utils database.')

