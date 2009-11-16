#!/usr/bin/env python

"""Unittest for random_util.py"""

import unittest

import random_util


class RandomUtilTestCase(unittest.TestCase):

    def testNameAttributes(self):
        self.assertEquals(
            {'firstname': 'Jack',
             'lastname': 'Bauer',
             'username': 'jbauer',
             'email': 'jbauer@domain.com'},
            random_util._NameAttributes('Jack Bauer'))
        self.assertEquals(
            {'firstname': 'John',
             'lastname': 'Adams',
             'username': 'jadams',
             'email': 'jadams@domain.com'},
            random_util._NameAttributes('John Quincy Adams'))

    def testRandomPerson(self):
        # make sure it doesn't asplode
        person = random_util.Person()
        self.assertTrue(person.active)
        self.assertFalse(person.admin)
        self.assertTrue(
            person.firstname in [n.split()[0] for n in random_util.NAMES])
        self.assertTrue(
            person.lastname in [n.split()[-1] for n in random_util.NAMES])

    def testRandomMember(self):
        # make sure it doesn't asplode
        member = random_util.Member(active=False, admin=True)
        self.assertFalse(member.active)
        self.assertTrue(member.admin)
        self.assertFalse(member.starving)


if __name__ == '__main__':
    unittest.main()
