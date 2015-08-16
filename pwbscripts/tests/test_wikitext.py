'''
Created on 15 juil. 2014

@author: tom
'''

import unittest

from pwbscripts.wikitext.wikitext import Text
import pwbscripts.wikitext.wikitext as Code
import pwbscripts.wikitext.builder as build


class Test(unittest.TestCase):

    def testTrivialText(self):
        text = Code.Text("plop")
        self.assertEqual(str(text), "plop")

        self.assertEqual(str(Code.wikiconcat([text, text])), "plopplop")
        self.assertEqual(str(text + text), "plopplop")

        escaped = Code.Text("plop|")

        self.assertNotEqual(escaped, "plop!", "should be escaped, found the same string")

        trivial_template = "{{plop}}"
        escaped = Code.Text(trivial_template)

        self.assertNotEqual(escaped, trivial_template,
                            "{} should be escaped, found the same string as {!r}".format(trivial_template,
                                                                                         escaped))


class TestLink(unittest.TestCase):

    def testLink(self):
        link = Code.Link("Plop")
        self.assertEqual(str(link), "[[Plop]]")

        link = Code.Link("Plop", Code.Text("wouh !"))
        self.assertEqual(str(link), "[[Plop|wouh !]]")

    def testInvalid(self):

        self.assertRaises(AssertionError, lambda: Code.Link("Plop", "wow"))

        self.assertRaises(AssertionError, lambda: Code.Link("wow|a"))

    def testComposite(self):
        """Composite : test with various texts combinations"""

        link = Code.Link("Plop", Code.Text("wouh |"))
        self.assertEqual(str(link), "[[Plop|wouh {{!}}]]")


class TestTemplate(unittest.TestCase):

    def testSimple(self):
        tmpl = Code.Template("plop")
        self.assertEqual(str(tmpl), "{{plop}}")

        tmpl = Code.Template("plop", [Text("A"), Text("B")], {"wow1": Text("plop")})

        tmpl_str = str(tmpl)

        self.assertIn("|1=A", tmpl_str)
        self.assertNotIn("|0=", tmpl_str)
        self.assertNotIn("|3=", tmpl_str)

        self.assertIn("|wow1=plop", tmpl_str)

        #self.assertRegex(tmpl_str, "^{{plop|")


class TestMWParserFromHell2WikiText(unittest.TestCase):

    def test1(self):
        code = "Le {{Plop|bidou}} petit"
        wkt = build.build_wikitext(code)
        self.assertIn(str(wkt), ["Le {{Plop|bidou}} petit", "Le {{Plop|1=bidou}} petit"])

if __name__ == "__main__":

    unittest.main()
