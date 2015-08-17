#!/usr/bin/python
# coding:utf-8

""" wrapper to launch tests of maj_annonces scripts """


import doctest
from unittest import TestSuite

import net_projets

from net_projets import Test as Testn

# import pwbscripts.projects as projects
CONF = "PWBSCRIPTS_CONFFILE"


class TestNetProjets(Testn):

    """ wrapper subclass """

    def runTest(self):
        """ Wrapping method """
        return super(TestNetProjets, self).runTest()
        # net_projets.Test.runTest(self)


def load_tests(loader, tests, other=None):
    """
    #  (avoided) patch trial to make this work
    """
    suite = other
    suite = TestSuite()

    for test_class in [TestNetProjets]:
        tests = loader.loadTestsFromTestCase(test_class)
    suite.addTests(tests)

    suite.addTests(doctest.DocTestSuite(net_projets))

    return suite
