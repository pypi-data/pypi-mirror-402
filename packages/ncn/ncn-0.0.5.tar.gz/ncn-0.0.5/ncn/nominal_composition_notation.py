import re
from periodictable import elements
from typing import Optional



ptn1 = re.compile(r'\b((?:He|Li|Be|Ne|Na|Mg|Al|Si|Cl|Ar|Ca|Sc|Ti|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og|H|B|C|N|O|F|P|S|K|V|Y|I|W|U)(?:-?\d+(?:\.\d+)?(?:He|Li|Be|Ne|Na|Mg|Al|Si|Cl|Ar|Ca|Sc|Ti|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og|H|B|C|N|O|F|P|S|K|V|Y|I|W|U))+)\b')


ptn2 = re.compile(r'^(He|Li|Be|Ne|Na|Mg|Al|Si|Cl|Ar|Ca|Sc|Ti|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og|H|B|C|N|O|F|P|S|K|V|Y|I|W|U)((?:-?\d+(?:\.\d+)?(?:He|Li|Be|Ne|Na|Mg|Al|Si|Cl|Ar|Ca|Sc|Ti|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og|H|B|C|N|O|F|P|S|K|V|Y|I|W|U))+)$')


ptn3 = re.compile(r'(\d+(?:\.\d+)?)(He|Li|Be|Ne|Na|Mg|Al|Si|Cl|Ar|Ca|Sc|Ti|Cr|Mn|Fe|Co|Ni|Cu|Zn|Ga|Ge|As|Se|Br|Kr|Rb|Sr|Zr|Nb|Mo|Tc|Ru|Rh|Pd|Ag|Cd|In|Sn|Sb|Te|Xe|Cs|Ba|La|Ce|Pr|Nd|Pm|Sm|Eu|Gd|Tb|Dy|Ho|Er|Tm|Yb|Lu|Hf|Ta|Re|Os|Ir|Pt|Au|Hg|Tl|Pb|Bi|Po|At|Rn|Fr|Ra|Ac|Th|Pa|Np|Pu|Am|Cm|Bk|Cf|Es|Fm|Md|No|Lr|Rf|Db|Sg|Bh|Hs|Mt|Ds|Rg|Cn|Nh|Fl|Mc|Lv|Ts|Og|H|B|C|N|O|F|P|S|K|V|Y|I|W|U)')


def find(text: str) -> list[str]:
    """
    Find all nominal composition notation in the string.
    If it is not found, an empty list is returned.
    :param text: Input string.
    :return: List of nominal composition notation found in the string.
    """
    return ptn1.findall(text)


def parse(text: str, balance: bool = False) -> Optional[dict]:
    """
    Parse nominal composition notation string into a dictionary.
    If balance is True, the balance element's composition is calculated automatically.
    If the input string is not a valid nominal composition notation, None is returned.
    :param text: Input nominal composition notation string.
    :param balance: Whether to calculate the balance element's composition automatically.
    :return: Dictionary of element symbols and their compositions or None.
    """
    match = ptn2.match(text)
    if match:
        parse_rst = {elem: float(wf) for wf, elem in ptn3.findall(match.group(2))}
        parse_rst[match.group(1)] = 100.0 - sum(parse_rst.values()) if balance else 'balance'
        return parse_rst
    else:
        return None


def name(hyphen: bool = False, precision: int = 3, **kwargs) -> str:
    """
    Generate nominal composition notation string from given compositions.
    If hyphen is True, elements are separated by hyphens.
    Compositions are formatted to the given precision, trailing zeros and decimal points are removed.
    :param hyphen: Whether to separate elements by hyphens.
    :param precision: Number of decimal places for formatting compositions.
    :param kwargs: Element symbols and their compositions as keyword arguments.
                   The balance element should have the value 'balance'.
    :return: Nominal composition notation string.
    """
    # Kwargs are sorted by elemental concentration, with the balance element having the highest priority.
    if len(kwargs) < 1:
        raise ValueError('At least one element composition must be provided.')
    balance_count = 0
    total_weight_fraction = 0
    def sort_key(item):
        nonlocal balance_count
        nonlocal total_weight_fraction
        symbol, composition = item
        atomic_number = elements.symbol(symbol).number
        if composition == 'balance':
            balance, composition = 1, None
            balance_count += 1
        else:
            balance, composition = 0, float(composition)
            if composition < 0 or composition > 100:
                raise ValueError(f'Invalid composition for {symbol}: {composition}. Must be between 0 and 100.')
            total_weight_fraction += composition
        return balance, composition, atomic_number
    sorted_kwargs = list(sorted(kwargs.items(), key=sort_key, reverse=True))
    if balance_count > 1:
        raise ValueError('Only one balance element is allowed.')
    if total_weight_fraction > 100:
        raise ValueError(f'Total composition exceeds 100: {total_weight_fraction}.')
    substrs = [sorted_kwargs[0][0]] + \
              [f'{float(composition):.{precision}f}'.rstrip('0').rstrip('.') + symbol
               for symbol, composition in sorted_kwargs[1:]]
    return '-'.join(substrs) if hyphen else ''.join(substrs)
