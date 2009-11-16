#!/usr/bin/env python

"""Unittest for member_loader.py"""

import unittest

import member_loader


class MemberLoaderTest(unittest.TestCase):

    def testStrToBool(self):
        self.assertTrue(member_loader.str_to_bool('TRUE'))
        self.assertFalse(member_loader.str_to_bool('FALSE'))
        self.assertFalse(member_loader.str_to_bool('FOO'))


if __name__ == '__main__':
    unittest.main()
