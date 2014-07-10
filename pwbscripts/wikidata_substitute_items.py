#!/usr/bin/python
# coding:utf-8
"""
#Description: substitutes an item in a page with another one (unfinished)
"""
# Experimental: probably

# TODO: finish or delete if useless


import pywikibot as pwb
import wd_lib
from command import cmds

REPO = None


def get_database():
    """
    returns the standard Wikidata repo
    """
    if not REPO:
        site = pwb.Site("wikidata", "wikidata")
        repo = site.data_repository()
        return repo
    return REPO


def get_itempage(qid, database=get_database()):
    """ Returns a datapage from a 'Q...' string in the standard wikidata repo"""
    item = pwb.ItemPage(database, qid)
    print(item)

    return item


def test():
    """
    test (with sample datas)
    """
    from datas import whatlinks_page

    pages = whatlinks_page.whatlinks

    for qid in extract_linked_items(pages):
        page = get_itempage(qid)
        try:
            page.get()
            substitute_item_in_dataset(page, get_itempage("Q1660508"), get_itempage("Q1622272"))

        except Exception as exc:
            print('wow : <{}> ({}) something is wrong.'.format(exc, type(exc)))


def extract_linked_items(pages):
    """ From an iterable of pages string code, returns Qids of linked items
    """
    for page in pages:
        for iterate in iterate_on_items(page):
            yield((iterate[1:])[:-1])


def substitute_item_in_dataset(subject, old_item, new_item):
    """
    subject : DataPage
    old : DataPage
    data : DataPage
    """

    try:
        for (prop, val) in wd_lib.get_claim_pairs(subject):
            print(">>>>>>>>>>>>>>>>>>>>>>>>>>>> Value in claim : {}, to subst {} (property {})"
                  .format(val, old_item, prop))
            if val == old_item:
                print (">>>>>>>>>>>>>>>>>> subst in claim by {} <<<<<<<<<<<<<<<<<<<<<<<<<<<<<<<".format(new_item))
                substitute_item_in_claims(subject, old_item, new_item)

    except KeyError:
        print ("Key Error")


def substitute_item_in_claims(subject, old, new):
    """ plop
    """
    claims_set = subject.get()["claims"]
    for claims in claims_set:
        for cla in claims_set[claims]:
            if cla.target == old:
                print("#######   {}".format(cla))
                cla.changeTarget(new)

from lxml import etree
from StringIO import StringIO as StringIO


def iterate_on_items(pagecode):
    """extracts items listed on pages, and iterates on them """
    parser = etree.HTMLParser()

    tree = etree.parse(StringIO(pagecode), parser)

    # xpath = "/html/body/div[3]/div[3]/div[3]/ul/li[83]/a/span/span[2]"
    span_class = "wb-itemlink-id"
    request = tree.xpath('//span[@class="{}"]'.format(span_class))
    for span in request:
        yield span.text


def create_option_parser():
    """ arguments : 'commands' standard, old item, new item """

    args = cmds.create_argument_parser("substitutes items")
    args.add_argument('--old', '-o', dest='old')
    args.add_argument('--new', '-n', dest='new')

    return args


def main():
    """ main function : process command line and analyses options """
    par = create_option_parser()
    args = par.parse_args()

    print(args)

    test()
if __name__ == "__main__":
    main()
