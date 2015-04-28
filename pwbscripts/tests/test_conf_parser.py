#!/usr/bin/python
# -*- coding:utf-8 -*-


u"""
Yaml parser & ProjectParameters objects test
"""

import pkgutil
import unittest
import yaml

from pwbscripts.project_parameters import ProjectParameters
import pwbscripts.projects as projects
# import pwbscripts.projects
# import pwbscripts.scripts
# from StringIO import StringIO
SAMPLEYAML = u"""
Informatique:
        page:  Projet:Informatique
        tasks: [announces]

Mathématiques:
    page: Projet:Mathématiques
    tasks: [Hyubot]
    portals: ["Portail:Algèbre"]
    tasks: [announces, hyuBotLib]
"""


class TestParser(unittest.TestCase):

    """ Preliminary & API tests """

    def assertIn(self, elem, tlist):
        """ custom test : elem in list"""
        self.assertTrue(elem in tlist)

    def testParse(self):
        """ yaml parser object loading and structure """
        obj = yaml.load(SAMPLEYAML)
        print(obj)

        self.assertEqual(obj["Informatique"]["page"], "Projet:Informatique")
        self.assertIn("announces", obj["Informatique"]["tasks"])

        self.assertIn(u"Portail:Algèbre", obj[u"Mathématiques"][u"portals"])


class TestConfigObj(unittest.TestCase):

    """ ProjectParameters Test """

    def testObj(self):
        """ test of a sample ProjectParameters Object """

        obj = yaml.load(SAMPLEYAML)
        proj = ProjectParameters("Informatique", obj["Informatique"])

        self.assertTrue(proj.has_task(u"announces"))


class TestConfigFile(unittest.TestCase):

    """ test our real config file """

    def testConfigLoad(self):
        """ the truth on the conffile loading and parsing """

        actual_config = (pkgutil.get_data("pwbscripts", "projects.yaml")).decode("utf-8")
        #  print(type(actual_config))

        self.assertEqual(type(actual_config), type(u"ààeiu"))

        obj = yaml.load(actual_config)

        #  fakefile = StringIO(actual_config)

        confs = projects.read_conffile(actual_config)

        self.assertNotEqual(obj, None)
        self.assertNotEqual(confs, None)


#        loaded OK
