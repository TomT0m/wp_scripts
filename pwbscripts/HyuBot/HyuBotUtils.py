
#coding: utf-8


import string

class TranslationTable:
    def __init__(self, dicOfRelatives,
                 defaultValue=None):
        self.unknownCharList = []
        self.dict = {}
        for c in string.printable:
            self.dict[c] = c
        for s in dicOfRelatives.keys():
            for c in dicOfRelatives[s]:
                self.dict[c] = s

        if defaultValue is not None:
            self.dict[None] = defaultValue

    def translate(self, text):
        try:
            return "".join([self.dict[c] for c in text])
        except KeyError:
            for c in text:
                if c not in self.dict:
                    self.unknownCharList.append((c, text))
            return "".join([self.dict.get(c, self.dict.get(None, c))
                            for c in text])

utf2ascii = TranslationTable(
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
