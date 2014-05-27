#! /usr/bin/python
#encoding: utf-8

"""

Projects configurations

"""

import pywikibot

from page_status import get_page_status

class ProjectParameters(object):
    """ Project parameters storage class, stores :
        * project name
        * parameters pages names : Announces, discussion pagename.
    """
    def __init__(self,
          project_name,
          wiki_basename,
          announce_pagename=None,
          discussion_pagename=None,
          portal_names=None,
          site=pywikibot.getSite("fr"),
          tasks=None,
          portal_option=None):

        self.wiki_basename = wiki_basename
        self.project_name = project_name
        self._announce_pagename = announce_pagename
        self._discussion_pagename = discussion_pagename

        self._discussion = None
        self._announce = None

        # HyuBot

        self._portals = {name: [] for name in (portal_names or []) }
        for key, val in (portal_option or []):
            self._portals[key] = val

        self._wiki = site

        # tasks list

        self._tasks = tasks or []

    @property
    def announce_pagename(self):
        """ Getter for announce pagename property """
        if self._announce_pagename:
            return self._announce_pagename
        else:
            return self.wiki_basename + "/Annonces"

    @property
    def discussion_pagename(self):
        """ get discussion pagename """
        if self._discussion_pagename:
            return self._discussion_pagename
        else:
            return "Discussion {}".format(self.wiki_basename)

    @property
    def discussion_page(self):
        """ get discussion page object (last version if we modified on the program) """
        if not self._discussion:
            self._discussion = get_page_status(self.discussion_pagename)
        return self._discussion

    @property
    def announce_page(self):
        """ get our announce_page object """

        if not self._announce:
            self._announce = get_page_status(self.announce_pagename)
        return self._announce

    @property
    def tasks(self):
        """ the list of tasks to handle for this project """
        return self._tasks

