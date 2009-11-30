#!/usr/bin/env python

"""Utility functions for doing board elections."""

import datetime
import random

from google.appengine.ext import db

import freesidemodels
import member_util


class Error(Exception):
    """Base error class for this module."""


class ElectionError(Error):
    """Raised when there is a problem in the election."""


class InvalidElectionError(ElectionError):
    """Raised when an invalid election is used."""


class NomineeError(ElectionError):
    """Raised when an invalid nominee is nominated."""


class ElectionDateError(ElectionError):
    """Raised when an election has an invalid date range."""


def _IsOfficerElection(election):
    """Determines if an election is an officer election.

    Args:
      election: freesidemodels.Election, the election to check.
    Returns:
      bool, whether the election is an officer election.
    """
    return isinstance(election, freesidemodels.OfficerElection)


def _IsBoardElection(election):
    """Determines if an election is a board member election.

    Args:
      election: freesidemodels.Election, the election to check.
    Returns:
      bool, whether the election is a board member election.
    """
    return isinstance(election, freesidemodels.BoardElection)


def Nominate(election, nominee, current_user):
    """Nominate a Person for an election.

    Args:
      election: freesidemodels.Election, the election
      nominee: freesidemodels.Person, the person being elected
      current_user: freesidemodels.Person, the current user
    """
    def DoNomination():
        election.nominees.append(nominee.key())
        election.nominators.append(current_user.key())
        # Shuffle the nominators so they are anonymous.
        random.shuffle(election.nominators)
        election.put()

    try:
        election.key()
    except db.NotSavedError:
        raise InvalidElectionError('Invalid election.')

    if not member_util.IsActiveMember(current_user):
        raise ElectionError('Only active Freeside members can nominate.')

    if nominee.key() == current_user.key():
        raise NomineeError('You can\'t nominate yourself.')

    if nominee.key() in election.nominees:
        raise NomineeError('%s has already been nominated for %s.' %
                            (nominee.username, election.position))

    if current_user.key() in election.nominators:
        raise ElectionError('You can only nominate one person per election.')

    now = datetime.datetime.now()
    if not election.nominate_start < now < election.nominate_end:
        raise ElectionDateError('Election is not accepting nominations.')

    if _IsOfficerElection(election) and not member_util.IsActiveMember(nominee):
        raise NomineeError('Officers must be active Freeside members.')
    elif (_IsBoardElection(election)
          and not isinstance(nominee, freesidemodels.Person)):
        raise NomineeError('Invalid nominee.')

    db.run_in_transaction(DoNomination)


def Vote(election, candidate, current_user):
    """Cast a vote for a candidate.

    Args:
      election: freesidemodels.Election, the election to vote in.
      candidate: freesidemodels.Person, the candidate to cast a vote for.
      current_user: freesidemodels.Person, the current user.
    """
    def DoVote():
        election.votes.append(candidate.key())
        election.voters.append(current_user.key())
        # Shuffle teh voters so they are anonymous.
        random.shuffle(election.voters)
        election.put()

    try:
        election.key()
    except db.NotSavedError:
        raise InvalidElectionError('Invalid election.')

    now = datetime.datetime.now()
    if not election.vote_start < now < election.vote_end:
        raise ElectionDateError('Election is not accepting votes.')

    if candidate.key() not in election.nominees:
        raise NomineeError('Candidate has not been nominated.')

    if current_user.key() in election.voters:
        raise ElectionError('You can only vote once per election.')

    db.run_in_transaction(DoVote)
