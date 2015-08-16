#!/usr/bin/python
# encoding:utf-8


from functools import total_ordering
import re


@total_ordering
class Date(object):
    """ A french (very) simple date object, comparable and that's it,
    assumes dates are corrects

    >>> a = Date('1', 'janvier', 2013)
    >>> b = Date('1', 'janvier', 2014)
    >>> a < b
    True
    """
    MOIS = " janvier février mars avril mai juin juillet août septembre octobre novembre décembre".split(" ")
    REV_MOIS = None

    def __init__(self, jour, mois, annee):
        if not Date.REV_MOIS:
            Date.REV_MOIS = {self.MOIS[x]: x
                             for x in range(1, 13)}
        self._jour = int(jour)
        self._mois = self.REV_MOIS[mois]
        self._annee = int(annee)

    def __eq__(self, other):
        return self.jour == other.jour and self.mois == other.mois and self.annee == other.annee

    def __lt__(self, other):
        return self.annee < other.annee or (
            self.annee == other.annee and self.mois < other.mois or (
                self.mois == other.mois and self.jour < other.jour))

    def __str__(self):
        res = "{:2d} {} {:4d}".format(self.jour, self.MOIS[self.mois], self.annee)
        return res

    def __repr__(self):
        res = "{:2d} {} {:4d}".format(self.jour, self.MOIS[self.mois], self.annee)
        return res

    @property
    def mois(self):
        """ Mois """
        return self._mois

    @property
    def annee(self):
        """ année """
        return self._annee

    @property
    def jour(self):
        """ jour """
        return self._jour


def extract_date(text):
    """ Returns a date object if text seems to countain a date textual description,
    None otherwide


    >>> extract_date("ZRezsdfsertzer")

    >>> extract_date("10 janvier 2042")
    10 janvier 2042

"""
    for line in text.split("\n"):
        mois = Date.MOIS
        re_mois = "{}".format("|".join(mois))
        match = re.search("({jour}) ({mois}) ({annee})"
                          .format(
                              mois=re_mois,
                              jour="[0-9]{1,2}",
                              annee="[0-9]{4}"
                          ),
                          line)
        if match:
            return Date(match.group(1), match.group(2), match.group(3))
    return None
