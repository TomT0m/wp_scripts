
#coding: utf-8

from __future__ import unicode_literals


from mwparserfromhell.utils import parse_anything
from wikitext import Text, Link

import mwparserfromhell.nodes as mwnodes
import mwparserfromhell.wikicode as mwwikicode


def build_wikitext(raw_text):
    parsed = parse_anything(raw_text)
    return parsed


def WikitextFromNode(node):
    if not isinstance(node, mwnodes.text.Text):
        return ValueError("{} object not a mwparserfromhell Text node",
                          node=node)

_buildMap = {mwnodes.Text: Text,
             mwnodes.Wikilink: Link}


def mwp_to_Wikitext(mwparsed):
    if isinstance(mwparsed, mwwikicode.Wikicode):
        pass
    else:
        raise TypeError("{} object is nor Wikicode Object".format(mwparsed),
                        param=mwparsed)
