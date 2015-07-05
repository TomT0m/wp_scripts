
# coding: utf-8


"""
module that builds wikitext object
"""


from __future__ import unicode_literals

from mwparserfromhell.utils import parse_anything

import mwparserfromhell.nodes as mwnodes
import mwparserfromhell.wikicode as mwwikicode
from pwbscripts.wikitext.wikitext import Text, Link


def wikitext_from_node(node):
    """
    returns a wikitext object from a mwparserfromhell Node
    """
    if not isinstance(node, mwnodes.text.Text):
        return ValueError("{} object not a mwparserfromhell Text node",
                          node=node)

_buildMap = {mwnodes.Text: wikitext_from_node,
             mwnodes.wikilink.Wikilink: lambda x: Link(x.title, x.text),
             mwnodes.text.Text: lambda x: Text(x.value)}


def mwp_to_Wikitext(mwparsed):
    if isinstance(mwparsed, mwwikicode.Wikicode):
        return _buildMap[type(mwparsed)](mwparsed)
    else:
        raise TypeError("{} object is not of type Wikicode".format(mwparsed),
                        param=mwparsed)


def build_wikitext(raw_text):
    parsed = parse_anything(raw_text)
    wk_text = mwp_to_Wikitext(parsed)
    return wk_text
