#!/usr/bin/python
# coding:utf-8

""" wrapper to launch tests of maj_annonces scripts """


import doctest

from unittest import TestSuite

import pwbscripts
# import pwbscripts.projects as projects

CONF = "PWBSCRIPTS_CONFFILE"


class TestNetProjets(net_projets.Test):

    """ wrapper subclass """

    def runTest(self):
        return super(net_projets.Test, self).runTest()
        # net_projets.Test.runTest(self)


def load_tests(loader, tests, pattern):
    # TODO: patch trial to make this work

    suite = TestSuite()
    for test_class in [TestNetProjets]:
        tests = loader.loadTestsFromTestCase(test_class)
    suite.addTests(tests)

    suite.addTests(doctest.DocTestSuite(net_projets))

    return suite
