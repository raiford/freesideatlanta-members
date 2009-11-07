#!/usr/bin/env python

"""Unittest for member_util.py"""

import random
import unittest

import freesidemodels
import member_util
import random_util
import test_util


def GetKey(m):
    return m.key()


class SaveMemberTest(test_util.AppEngineTestBase):

    def testSave(self):
        member = member_util.SaveMember(random_util.Member())
        self.assertEquals(member.key(), freesidemodels.Member.all()[0].key())

    def testSaveIfChanged(self):
        new_member = member_util.SaveMember(random_util.Member())
        new_member.username = 'fry'
        new_member.email = 'fry@planex.com'
        member_util.SaveIfChanged(new_member)

        [member] = freesidemodels.Member.all().fetch(1)
        self.assertEquals(member.username, new_member.username)
        self.assertEquals(member.email, new_member.email)

    def testSaveIfChangedNotChanged(self):
        member = member_util.SaveMember(random_util.Member())

        # TODO(dknowles): Use mox instead
        called = False
        orig_save_member = member_util.SaveMember
        def MockSaveMember(member):
            called = True
        member_util.SaveMember = MockSaveMember

        member_util.SaveIfChanged(member)
        member_util.SaveMember = orig_save_member
        self.failIf(called)


class MemberUtilTest(test_util.AppEngineTestBase):

    def setUp(self):
        test_util.AppEngineTestBase.setUp(self)
        self.active_members = []
        self.inactive_members = []
        self.SeedMembers()

    def SeedMembers(self):
        def DoSeed(count, member_list, active):
            for _ in xrange(0, count):
                member_list.append(
                    member_util.SaveMember(random_util.Member(active=active)))

        DoSeed(10, self.active_members, active=True)
        DoSeed(10, self.inactive_members, active=False)

    def testMakeMember(self):
        password = 'sweet.zombie.jesus'
        member = member_util.MakeMember(
            username='farnsworth',
            email='hubert.j.farnsworth@planex.com',
            password=password)
        self.assertEquals(
            member.password, freesidemodels.Person.EncryptPassword(password))

    def testGetActiveMembers(self):
        self.assertEquals(
            map(GetKey, self.active_members),
            map(GetKey, member_util.GetActiveMembers()))

    def testGetMemberByUsername(self):
        member = freesidemodels.Member(
            username='bender', password='foo', email='bender@robots.com')
        member.put()
        self.assertEquals(
            member.key(),
            member_util.GetMemberByUsername(member.username).key())

        member.active = False
        member.put()
        self.assertEquals(
            None, member_util.GetMemberByUsername(member.username))
        self.assertEquals(
            member.key(),
            member_util.GetMemberByUsername(
                member.username, active=False).key())

    def testGetMemberByEmail(self):
        member = freesidemodels.Member(
            username='bender', password='foo', email='bender@robots.com')
        member.put()
        self.assertEquals(
            member.key(),
            member_util.GetMemberByEmail(member.email).key())

        member.active = False
        member.put()
        self.assertEquals(
            None, member_util.GetMemberByEmail(member.email))
        self.assertEquals(
            member.key(),
            member_util.GetMemberByEmail(member.email, active=False).key())


if __name__ == '__main__':
    unittest.main()
