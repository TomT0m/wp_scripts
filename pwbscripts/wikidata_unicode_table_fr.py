#! /usr/bin/python
# encoding: utf-8

"""
Serie formatting in wikidata

TODO: Handle serie season redirects not associated to any particular article
"""


# import pywikibot
# create a site object, here for en-wiki

import re

from wd_lib import set_for_lang, make_sequence, item_by_title

SOURCE = """<strong class="selflink">10000 – 10FFF</strong></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(11000-11FFF)" title="Table des caractères Unicode (11000-11FFF)">11000 – 11FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(12000-12FFF)" title="">12000 – 12FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(13000-13FFF)" title="">13000 – 13FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(14000-14FFF)" title="">14000 – 14FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(15000-15FFF)" title="">15000 – 15FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(16000-16FFF)" title="">16000 – 16FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(17000-17FFF)" title="">17000 – 17FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(18000-18FFF)" title="">18000 – 18FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(19000-19FFF)" title="">19000 – 19FFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1A000-1AFFF)" title="">1A000 – 1AFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1B000-1BFFF)" title="Table des caractères Unicode (1B000-1BFFF)">1B000 – 1BFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1C000-1CFFF)" title="">1C000 – 1CFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1D000-1DFFF)" title="">1D000 – 1DFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1E000-1EFFF)" title="">1E000 – 1EFFF</a></li>
<li><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(1F000-1FFFF)" title="">1F000 – 1FFFF</a></li>
</ul>
</div>
</td>
</tr>
<tr>
<th colspan="2" style="text-align:center;background-color:#CEE0F2;color:#000000"><b>Autres plans Unicode</b></th>
</tr>
<tr>
<td></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(0000-0FFF)" title="">0000 – 0FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(0000-FFFF)" title="">plan 0 (BMP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><strong class="selflink">10000 – 10FFF</strong></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(10000-1FFFF)" title="">plan 1 (SMP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(20000-20FFF)" title="">20000 – 20FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(20000-2FFFF)" title="Table des caractères Unicode (20000-2FFFF)">plan 2 (SIP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(30000-DFFFF)" title="">30000 – DFFFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(30000-DFFFF)" title=""><i>plans 3–13 (réservés)</i></a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(E0000-E0FFF)" title="">E0000 – E0FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(E0000-EFFFF)" title="Table des caractères Unicode (E0000-EFFFF)">plan 14 (SSP)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(F0000-F0FFF)" title="Table des caractères Unicode (F0000-F0FFF)">F0000 – F0FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(F0000-FFFFF)" title="">plan 15 (privé - A)</a></span></td>
</tr>
<tr>
<td style="background:#;" align="center"><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(100000-100FFF)" title="Table des caractères Unicode (100000-100FFF)">100000 – 100FFF</a></span></td>
<td><span class="nowrap"><a href="/wiki/Table_des_caract%C3%A8res_Unicode_(100000-10FFFF)" title="">plan 16 (privé - B)</a>
"""

MAINS = [
    "Table des caractères Unicode (0000-FFFF)",
    "Table des caractères Unicode (10000-1FFFF)",
    "Table des caractères Unicode (20000-2FFFF)",
    "Table des caractères Unicode (30000-DFFFF)",
    "Table des caractères Unicode (E0000-EFFFF)",
    "Table des caractères Unicode (F0000-FFFFF)",
    "Table des caractères Unicode (100000-10FFFF)"
]

LESSER = """0000 0FFF
1000 1FFF
2000 2FFF
3000 3FFF
4000 4FFF
5000 5FFF
6000 6FFF
7000 7FFF
8000 8FFF
9000 9FFF
A000 AFFF
B000 BFFF
C000 CFFF
D000 DFFF
E000 EFFF
F000 FFFF"""


def label(mi_, ma_):
    """ returns a calculated label from a range """
    return "caractères Unicode des points de code {} à {}".format(mi_, ma_)


def enlabel(mi_, ma_):
    """ returns a calculated label from a range """
    return "Unicode characters from {} to {} codepoints".format(mi_, ma_)


def frtitle(mi_, ma_):
    """returns formated title """
    return "Table des caractères Unicode ({}-{})".format(mi_, ma_)


def main():
    """ main script function """
    def extr_mini_maxi(titl):
        """ extract bounds from title"""
        res = re.split("[()-]", titl)
        return res[1], res[2]

    items = [item_by_title("fr", title)
             for title in MAINS]
    ranges = [extr_mini_maxi(title)
              for title in MAINS]

    # items : the main articles, 7 main ranges, separated into subranges each

    all_items = items
    all_ranges = ranges

    make_sequence(items)

    for (item, rang_) in zip(items, ranges):
        (min_, max_) = rang_
        prefix = min_[0:-4]
        print(("====================='{}'========================".format(prefix)))

        def gen_title(lrange):
            """ title gen"""
            mi_ = ('{}{}'.format(prefix, lrange.split(" ")[0]))
            ma_ = ('{}{}'.format(prefix, lrange.split(" ")[1]))
            # import pdb ; pdb.set_trace()
            return frtitle(mi_, ma_)

        titles = [gen_title(lrange) for lrange in LESSER.split("\n")]
        items = [item_by_title("fr", title) for title in titles]
        ranges = [extr_mini_maxi(title) for title in titles]

        make_sequence(items)
        # suboptimal
        all_items = all_items + items
        all_ranges = all_ranges + ranges

    for (item, (min_, max_)) in zip(all_items, all_ranges):
        set_for_lang(item, "Table des caractères Unicode", "fr", label(min_, max_), "ambiguity and label correction")
        set_for_lang(item, "", "en", enlabel(min_, max_), "ambiguity and label correction")

        # correction of previous bug as it seems
        set_for_lang(item, "Unicode characters from 100000 to 10FFFF codepoints",
                     "en", enlabel(min_, max_), "ambiguity and label correction")

if __name__ == "__main__":
    main()
