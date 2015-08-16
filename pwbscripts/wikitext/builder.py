
# coding: utf-8


"""
module that builds wikitext object
"""

from mwparserfromhell.utils import parse_anything

import mwparserfromhell.nodes as mwnodes
import mwparserfromhell.wikicode as mwwikicode
from pwbscripts.wikitext.wikitext import Text, Link, Template, wikiconcat


def wikitext_from_node(node):
    """
    returns a wikitext object from a mwparserfromhell Node
    """
    if not isinstance(node, mwnodes.text.Text):
        return ValueError("{} object not a mwparserfromhell Text node",
                          node=node)

_buildMap = {
    mwnodes.wikilink.Wikilink: lambda x: Link(x.title,
                                              mwp_to_wikitext(x.text)),
    mwnodes.template.Template: lambda x: Template(x.name,
                                                  posargs=x.params),

    mwnodes.text.Text: lambda x: Text(x)
}


def mwp_to_wikitext(mwparsed):
    """Function that converts a mwparserfromhell Wikitext
    object to internal object"""
    if isinstance(mwparsed, mwwikicode.Wikicode):
        node = mwparsed.nodes[0]
        ntype = type(node)
        if len(mwparsed.nodes) > 1:
            return wikiconcat(
                [_buildMap[type(node)](node)
                 for node in mwparsed.nodes]
            )
        else:
            assert ntype in _buildMap
            return _buildMap[ntype](node)
    else:
        raise TypeError("{} object is not of type Wikicode".format(mwparsed),
                        param=mwparsed)


def build_wikitext(raw_text):
    """
    constructor Wikitext function
    """
    parsed = parse_anything(raw_text)
    wk_text = mwp_to_wikitext(parsed)
    return wk_text
