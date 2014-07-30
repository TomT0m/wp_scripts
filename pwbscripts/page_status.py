#! /usr/bin/python
# encoding:utf-8

from __future__ import unicode_literals

"""
A Project page information state
"""
import pywikibot
import mwparserfromhell

import re


def get_page(name, namespace=None):
    """ get a Page in frwiki """
    site = pywikibot.getSite("fr")

    if namespace:
        return pywikibot.Page(site, name, defaultNamespace=namespace)

    return pywikibot.Page(site, name)


class PageStatus(object):

    """ Status object """

    def __init__(self, page):
        self.page = page
        self._cached_content = None
        self.edit_comment = u""
        self._original_content = None
        self.modified = False
        self._redirected_to = None

    @property
    def redirected_to(self):
        return self._redirected_to

    def get_content(self):
        """ cached access to page content """
        if not self._cached_content:
            self._cached_content = self.page.get(get_redirect=True)
            self._original_content = self._cached_content

        return self._cached_content

    def is_redirect_page(self):

        try:
            self.page.get()
        except pywikibot.IsRedirectPage:
            print("!!!!!!!!! {}".format(self.page.getRedirectTarget().title()))
            self._redirected_to = self.page.getRedirectTarget().title()
            return True

        except pywikibot.NoPage:
            pass
        return False

    def is_deleted(self):
        try:
            self.page.get()
        except pywikibot.NoPage:
            return True
        finally:
            return False

    def set_content(self, new_text, comment):
        """ setter for content, without writing"""

        modif = not(unicode(new_text) == unicode(self._cached_content))
        self.modified = self.modified or modif

        if modif:
            if len(self.edit_comment) > 0:
                self.edit_comment += u"; " + comment
            else:
                self.edit_comment = comment

        self._cached_content = new_text

    def save(self):
        """ saves the current content on server """
        self.page.put(self._cached_content, comment=self.edit_comment)

    def is_proposed_to_deletion(self):
        """ try to guess if there is a deletion proposition related to this page"""

        re_bandeau = re.compile(u"{{(suppression|à supprimer)}}", re.IGNORECASE)
        re_pas_closed = re.compile(u"{{Article (supprimé|conservé)", re.IGNORECASE)

        if self.page.exists():

            nom_discussion_suppression = "Discussion:" + self.page.title() + "/Suppression"

            content = self.get_content()
            has_status = re_bandeau.search(content)

            if not has_status:
                discussion_suppression = get_page(nom_discussion_suppression)
                res = re_pas_closed.search(discussion_suppression.get(get_redirect=True))

                if not res:
                    # inconsistent state : probably merged
                    if self.is_redirect_page():
                        return False
                    else:
                        pywikibot.output("État incohérent entre la page et la page de suppression")

                    return True
                else:
                    return False
            return True
        return False

    def is_proposed_to_fusion(self):
        """ try to guess if there is a deletion proposition related to this page"""

        return u'{{à fusionner|' in self.get_content()

    def fusion_with(self):
        """get the list of article titles which are supposed to be fusioned with this one"""
        parsed = mwparserfromhell.parse(self.get_content())
        for tmpl in parsed.filter_template():
            if tmpl.name == u"à fusionner":
                print(tmpl)

    def show_diff(self):
        """ show our changes """
        if self._cached_content:
            pywikibot.showDiff(self._original_content, self._cached_content)

    def __str__(self):
        return "Status object of page {}. Modified : {}".format(self.page, self.modified)

    def __unicode__(self):
        return u"Status object of page {}. Modified : {}".format(self.page, self.modified)


def get_page_status(pagename):
    """ Returns a page status object
    >>> get_page_status("Plop").page
    Page{[[fr:Plop]]}

    may thow InvalidPage

    """
    site = pywikibot.getSite("fr")
    regtitle = re.compile("{}.*{}".format(re.escape("[["),
                                          re.escape("]]"))
                          )

    if regtitle.match(pagename):
        pagename = pagename[2:-2]

    page = pywikibot.Page(site, pagename)

    return PageStatus(page)
