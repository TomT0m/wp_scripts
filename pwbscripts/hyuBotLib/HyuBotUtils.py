
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
        for transliteration in dicOfRelatives.keys():
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
        'a': u'áàâäåāảãăạąặắǎấầ',  # 'а' dans l'alphabet cyrillique
        'e': u'éêèëěėễệęềếē', 'i': u'íîïīıìịǐĩ',
        'o': u'óôöōőøõòơồόŏờốṓởǫỗớ',  # les deux accents aigus sont différents
        'A': u'ÀÂÄÅÁĀ', 'E': u'ÉÊÈËĖ', 'I': u'ÎÏİÍ', 'O': u'ÔØÖŌÓÕ',
        'u': u'ùûüūúưứŭũửůűụ', 'y': u'ÿýỳ', 'U': u'ÙÛÜÚŪ',
        'ae': u'æ', 'AE': u'Æ', 'oe': u'œ', 'OE': u'Œ',
        'c': u'çćč', 'C': u'ÇČĈĆ', 'd': u'đð', 'D': u'ĐD̠',
        'g': u'ğġǧ', 'G': u'Ğ', 'h': u'ĥħ', 'H': u'ḤĦ', 'l': u'ḷłľℓļ', 'L': u'ŁĽ',
        'm': u'ṃ', 'n': u'ńñňṇņ', 'r': u'řṛṟ', 's': u'śšşs̩ṣș', 'S': u'ŠŞŚŜȘ',
        't': u'ţťt̠țṭ', 'T': u'T̩ŢȚ', 'z': u'žżź', 'Z': u'ŻŽ',
        'ss': u'ß', 'th': u'þ', 'Th': u'Þ', 'TM': u'™',
        'alpha': u'α', 'beta': u'β', 'gamma': u'γ', 'Gamma': u'Γ',
        'delta': u'δ', 'Delta': u'Δ', 'epsilon': u'ε', 'zeta': u'ζ',
        'eta': u'η', 'theta': u'θ', 'iota': u'ι', 'kappa': u'κ',
        'lambda': u'λ', 'Lambda': u'Λ', 'mu': u'μ', 'nu': u'ν',
        'xi': u'ξ', 'omicron': u'ο', 'pi': u'π', 'rho': u'ρ',
        'sigma': u'σ', 'Sigma': u'Σ', 'tau': u'τ', 'upsilon': u'υ',
        'phi': u'φϕ', 'Phi': u'Φ', 'chi': u'χ', 'psi': u'ψ', 'Psi': u'Ψ',
        'omega': u'ω', 'Omega': u'Ω',
        '1 2': u'½', '2': u'²', '3': u'³', 'micro': u'µ',  # symbole différent de la lettre mu
        ' ': u'’–−∞×÷≡«»°…—®⊥‐√ʼ§' + string.whitespace + string.punctuation,
        # à traiter : '‘´'
        # supprimé : 人
        '': u'·ʿ‘'  # diacritiques ou lettres négligées et caractère pour la coupure d'un mot
    },
    defaultValue=' '
)


def uppercase_first(text):
    """ returns a similar string with the first characters uppercased"""
    if text:
        return text[0].upper() + text[1:]
    else:
        return ''
