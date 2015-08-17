#!/usr/bin/python
# -*- coding:utf-8 -*-


"""
Yaml parser & ProjectParameters objects test
"""

import pkgutil
import unittest
import yaml


from project_parameters import ProjectParameters

# import pwbscripts.projects
# import pwbscripts.scripts
# from StringIO import StringIO
SAMPLEYAML = """
Informatique:
        page:  Projet:Informatique
        tasks: [announces]

Mathématiques:
    page: Projet:Mathématiques
    tasks: [Hyubot]
    portals: ["Portail:Algèbre"]
    tasks: [announces, hyubot]
"""


class TestParser(unittest.TestCase):

    """ Preliminary & API tests """

    def assertInList(self, elem, tlist):
        """ custom test : elem in list"""
        self.assertTrue(elem in tlist)

    def testParse(self):
        """ yaml parser object loading and structure """
        obj = yaml.load(SAMPLEYAML)

        self.assertEqual(obj["Informatique"]["page"], "Projet:Informatique")
        self.assertInList("announces", obj["Informatique"]["tasks"])

        self.assertInList("Portail:Algèbre", obj["Mathématiques"]["portals"])


class TestConfigObj(unittest.TestCase):

    """ ProjectParameters Test """

    def testObj(self):
        """ test of a sample ProjectParameters Object """

        obj = yaml.load(SAMPLEYAML)
        proj = ProjectParameters("Informatique", obj["Informatique"])

        self.assertTrue(proj.has_task("announces"))


class TestConfigFile(unittest.TestCase):

    """ test our real config file """

    def testConfigLoad(self):
        """ the truth on the conffile loading and parsing """

        actual_config = (pkgutil.get_data("datas", "projects.yaml")).decode("utf-8")
        #  print(type(actual_config))

        self.assertEqual(type(actual_config), type("ààeiu"))

        obj = yaml.load(actual_config)

        self.assertNotEqual(obj, None)


#        loaded OK
