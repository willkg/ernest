from nose.tools import eq_

from . import TestCase
from ernest.bugzilla import BugzillaTracker


class BugzillaTestCase(TestCase):
    def test_parse_whiteboard(self):
        bz = BugzillaTracker(self.app)

        tests = (
            ('u=user c=comp p=1 s=2013.20', {
                'u': 'user', 'c': 'comp', 'p': 1, 's': '2013.20', 'flags': []}),
            ('[foo] u=user c=comp p=1 s=2013.20', {
                'u': 'user', 'c': 'comp', 'p': 1, 's': '2013.20', 'flags': ['foo']}),
            ('u=user c=comp p=1 s=2013.20 [foo]', {
                'u': 'user', 'c': 'comp', 'p': 1, 's': '2013.20', 'flags': ['foo']}),
            ('u=dev c=codequality p= s=input.2013q4', {
                'u': 'dev', 'c': 'codequality', 's': 'input.2013q4', 'flags': []}),
        )

        for text, expected in tests:
            eq_(bz.parse_whiteboard(text), expected)
