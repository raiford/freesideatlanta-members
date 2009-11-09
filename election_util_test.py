#!/usr/bin/env python

"""Unittest for election_util.py."""

import datetime
import random
import unittest

import freesidemodels
import member_util
import election_util
import random_util
import test_util


class FunctionsTest(unittest.TestCase):

    def setUp(self):
        now = datetime.datetime.now()
        self.board_election = freesidemodels.BoardElection(
            position='board member',
            nominate_start=now,
            nominate_end=now,
            vote_start=now,
            vote_end=now)
        self.officer_election = freesidemodels.OfficerElection(
            position='officer',
            nominate_start=now,
            nominate_end=now,
            vote_start=now,
            vote_end=now)

    def testIsOfficerElection(self):
        self.assertTrue(election_util._IsOfficerElection(self.officer_election))
        self.assertFalse(election_util._IsOfficerElection(self.board_election))

    def testIsBoardElection(self):
        self.assertTrue(election_util._IsBoardElection(self.board_election))
        self.assertFalse(election_util._IsBoardElection(self.officer_election))


class ElectionUtilTest(test_util.AppEngineTestBase):

    def setUp(self):
        test_util.AppEngineTestBase.setUp(self)
        self.people = []
        self.members = []
        self.SeedPeople()

    def SeedPeople(self):
        for _ in range(10):
            person = random_util.Person()
            person.put()
            self.people.append(person)

            member = random_util.Member()
            member.put()
            self.members.append(member)

    def MakeElection(self, election_cls):
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=1)
        return election_cls(
            position=election_cls.__name__,
            nominate_start=now-delta*6,
            nominate_end=now-delta*4,
            vote_start=now-delta*2,
            vote_end=now+delta*2)

    def testNominate(self):
        el = self.MakeElection(freesidemodels.OfficerElection)

        # Unsaved election
        self.assertRaises(
            election_util.InvalidElectionError,
            election_util.Nominate,
            el, self.members[0], self.members[1])
        el.put()

        # Nominating as a non-member
        self.assertRaises(
            election_util.ElectionError,
            election_util.Nominate,
            el, self.members[0], self.people[0])

        # Nominating yourself
        self.assertRaises(
            election_util.NomineeError,
            election_util.Nominate,
            el, self.members[0], self.members[0])

        # Existing nominee
        el.nominees.append(self.members[0].key())
        self.assertRaises(
            election_util.NomineeError,
            election_util.Nominate,
            el, self.members[0], self.members[1])

        # Already voted
        el.nominees = []
        el.nominators.append(self.members[1])
        self.assertRaises(
            election_util.ElectionError,
            election_util.Nominate,
            el, self.members[0], self.members[1])

        # Not accepting nominations
        el.nominators = []
        self.assertRaises(
            election_util.ElectionDateError,
            election_util.Nominate,
            el, self.members[0], self.members[1])

        now = datetime.datetime.now()
        delta = datetime.timedelta(days=1)
        el.nominate_start = now - delta
        el.nominate_end = now + delta

        self.assertRaises(
            election_util.NomineeError,
            election_util.Nominate,
            el, self.people[0], self.members[1])

        bel = self.MakeElection(freesidemodels.BoardElection)
        bel.nominate_start = now - delta
        bel.nominate_end = now + delta
        bel.put()
        # Invalid nominee
        self.assertRaises(
            election_util.NomineeError,
            election_util.Nominate,
            bel, el, self.members[1])

        # Successful nomination
        election_util.Nominate(el, self.members[0], self.members[1])
        self.assertEquals([self.members[0].key()], el.nominees)
        self.assertTrue(self.members[1].key() in el.nominators)

        # Another successful nomination
        election_util.Nominate(el, self.members[1], self.members[2])
        self.assertEquals(
            [self.members[0].key(), self.members[1].key()], el.nominees)
        self.assertTrue(self.members[2].key() in el.nominators)

    def testVote(self):
        el = self.MakeElection(freesidemodels.BoardElection)

        # Unsaved election
        self.assertRaises(
            election_util.InvalidElectionError,
            election_util.Vote,
            el, self.members[0], self.members[1])

        # Invalid date range
        now = datetime.datetime.now()
        delta = datetime.timedelta(days=1)
        el.put()
        el.vote_start = now - delta * 4
        el.vote_end = now - delta
        self.assertRaises(
            election_util.ElectionDateError,
            election_util.Vote,
            el, self.members[0], self.members[1])

        # Non-nominated candidate
        el = self.MakeElection(freesidemodels.BoardElection)
        el.put()
        self.assertRaises(
            election_util.NomineeError,
            election_util.Vote,
            el, self.members[0], self.members[1])

        # Multiple votes
        el.nominees.append(self.members[0].key())
        el.voters.append(self.members[1].key())
        self.assertRaises(
            election_util.ElectionError,
            election_util.Vote,
            el, self.members[0], self.members[1])
        el.voters = []
        el.put()

        # Successful vote
        election_util.Vote(el, self.members[0], self.members[1])
        self.assertEquals([self.members[0].key()], el.votes)
        self.assertEquals([self.members[1].key()], el.voters)

        # Another successful vote
        election_util.Vote(el, self.members[0], self.members[2])
        self.assertEquals([self.members[0].key()] * 2, el.votes)
        self.assertTrue(self.members[2].key() in el.voters)


if __name__ == '__main__':
    unittest.main()
