
# encoding: utf-8

"""
Utility module used to the transliteration of articles with non ascii unicode characters into ascii
"""

import string


class TranslationTable(object):
    """ Class regrouping method to handle unicode caracters in article names"""
    def __init__(self, dicOfRelatives,
                 defaultValue=None):
        self.unknown_char_list = []
        self.dict = {}
        for character in string.printable:
            self.dict[character] = character
        for transliteration in list(dicOfRelatives.keys()):
            for character in dicOfRelatives[transliteration]:
                self.dict[character] = transliteration

        if defaultValue is not None:
            self.dict[None] = defaultValue

    def translate(self, text):
        """ translate charset, logging unknown translations"""
        try:
            return "".join([self.dict[character] for character in text])
        except KeyError:
            for character in text:
                if character not in self.dict:
                    self.unknown_char_list.append((character, text))
            return "".join([self.dict.get(character, self.dict.get(None, character))
                            for character in text])

UTF2ASCII = TranslationTable(
    dicOfRelatives={
        'a': 'áàâäåāảãăạąặắǎấầ',  # 'а' dans l'alphabet cyrillique
        'e': 'éêèëěėễệęềếē', 'i': 'íîïīıìịǐĩ',
        'o': 'óôöōőøõòơồόŏờốṓởǫỗớ',  # les deux accents aigus sont différents
        'A': 'ÀÂÄÅÁĀ', 'E': 'ÉÊÈËĖ', 'I': 'ÎÏİÍ', 'O': 'ÔØÖŌÓÕ',
        'u': 'ùûüūúưứŭũửůűụ', 'y': 'ÿýỳ', 'U': 'ÙÛÜÚŪ',
        'ae': 'æ', 'AE': 'Æ', 'oe': 'œ', 'OE': 'Œ',
        'c': 'çćč', 'C': 'ÇČĈĆ', 'd': 'đð', 'D': 'ĐD̠',
        'g': 'ğġǧ', 'G': 'Ğ', 'h': 'ĥħ', 'H': 'ḤĦ', 'l': 'ḷłľℓļ', 'L': 'ŁĽ',
        'm': 'ṃ', 'n': 'ńñňṇņ', 'r': 'řṛṟ', 's': 'śšşs̩ṣș', 'S': 'ŠŞŚŜȘ',
        't': 'ţťt̠țṭ', 'T': 'T̩ŢȚ', 'z': 'žżź', 'Z': 'ŻŽ',
        'ss': 'ß', 'th': 'þ', 'Th': 'Þ', 'TM': '™',
        'alpha': 'α', 'beta': 'β', 'gamma': 'γ', 'Gamma': 'Γ',
        'delta': 'δ', 'Delta': 'Δ', 'epsilon': 'ε', 'zeta': 'ζ',
        'eta': 'η', 'theta': 'θ', 'iota': 'ι', 'kappa': 'κ',
        'lambda': 'λ', 'Lambda': 'Λ', 'mu': 'μ', 'nu': 'ν',
        'xi': 'ξ', 'omicron': 'ο', 'pi': 'π', 'rho': 'ρ',
        'sigma': 'σ', 'Sigma': 'Σ', 'tau': 'τ', 'upsilon': 'υ',
        'phi': 'φϕ', 'Phi': 'Φ', 'chi': 'χ', 'psi': 'ψ', 'Psi': 'Ψ',
        'omega': 'ω', 'Omega': 'Ω',
        '1 2': '½', '2': '²', '3': '³', 'micro': 'µ',  # symbole différent de la lettre mu
        ' ': '’–−∞×÷≡«»°…—®⊥‐√ʼ§' + string.whitespace + string.punctuation,
        # à traiter : '‘´'
        # supprimé : 人
        '': '·ʿ‘'  # diacritiques ou lettres négligées et caractère pour la coupure d'un mot
    },
    defaultValue=' '
)


def uppercase_first(text):
    """ returns a similar string with the first characters uppercased"""
    if text:
        return text.capitalize()
    else:
        return ''

def unique(l):
    """Given a list of hashable object, return an alphabetized unique list."""
    l = list(dict.fromkeys(l).keys())
    l.sort()
    return l
