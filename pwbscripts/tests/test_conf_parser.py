#!/usr/bin/python
#encoding:utf-8


"""
Yaml parser & ProjectParameters objects test
"""

import unittest
import pkgutil

import yaml

from project_parameters import ProjectParameters
import projects

import scripts

from StringIO import StringIO

SAMPLEYAML = \
u"""
Informatique:
        page:  Projet:Informatique
        tasks: [announces]

Mathématiques:
    page: Projet:Mathématiques
    tasks: [Hyubot]
    portals: ["Portail:Algèbre"]
    tasks: [announces, HyuBot]
"""


class TestParser(unittest.TestCase):
    """ Preliminary & API tests """

    def assertIn(self, elem, list):
        """ custom test : elem in list"""
        self.assertTrue(elem in list)

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
        config = pkgutil.get_data("pwbscripts", "projects.yaml")
        obj = yaml.load(config)
        
        fakefile = StringIO(config)

        confs = projects.read_conffile(fakefile)

        # loaded OK

