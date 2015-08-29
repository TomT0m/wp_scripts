#! /usr/bin/python
# encoding: utf-8

"""

Projects configurations object

"""

from logging import warn

from page_status import get_page_status
import pywikibot as pwb


class ProjectParameters(object):

    """ Project parameters storage class, stores :
        * project name
        * parameters pages names : Announces, discussion pagename.
        ...

        init from a config obejct (result of the conf file parsing typically
    """

    def __init__(
        self, name,
        config_obj, site="fr"
    ):

        self._config_obj = config_obj

        self._name = name
        self._discussion_pagename = None
        # hyubot
        self._wiki = pwb.Site(site)

        # Pages objects attributes
        self._discussion = None
        self._announce = None

        self._insite = None

    def get(self, prop, default):
        """ getter : config obj key or default value """
        if prop in self._config_obj:
            return self._config_obj[prop]
        return default

    @property
    def name(self):
        """ returns the string name of the project """
        return self._name

    @property
    def site(self):
        """ returns the site object of the project """
        return self._wiki

    @property
    def announce_pagename(self):
        """ Getter for announce pagename property """
        return self.get("announce_page", self.wiki_basename + "/Annonces")

    @property
    def wiki_basename(self):
        """ returns the base page name of the project """
        return "Projet:{}".format(self.name)

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
        test = self.get("tasks", [])

        if test == []:
            warn("/!\\ no task for project {}".format(self.name))

        return test

    @property
    def insite(self):
        # TODO: document usage (mysterious)
        return self.get("insite", None)

    @property
    def portals(self):
        """ Returns the a list of couples of the portals
        attached to the project with theirs options
        """

        def options(self, portal):
            array_opt = self.get("option", [])

            if portal in array_opt:
                return array_opt[portal]
            return []

        portals = [(portal, options(self, portal))
                   for portal in self.get("portal_names", [])
                   ]

        if portals == []:
            warn("/!\\ no portals for project {}".format(self.name))

        return portals

    def has_task(self, task):
        """
        accessor : returns true if the project is candidate to run some task
        """
        return task in self.tasks
