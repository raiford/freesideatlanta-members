#!/usr/bin/env python

"""Utility functions for dealing with members."""

from google.appengine.ext import db

import freesidemodels


def MakeMember(*args, **kwargs):
    """Helper function for creating a new member.

    This does not add the member to datastore.

    If password is passed as a keyword argument, it is automatically
    encrypted using the encryption algorithm from
    freesidemodels.Person.EncryptPassword.
    """
    if 'password' in kwargs:
        kwargs['password'] = freesidemodels.Person.EncryptPassword(
            kwargs['password'])
    return freesidemodels.Member(*args, **kwargs)


def SaveMember(member):
    """Saves a member to datastore, with a transaction.

    Args:
      member: freesidemodels.Member
    Returns:
      freesidemodels.Member
    """
    def DoPut(member):
        member.put()
    db.run_in_transaction(DoPut, member)
    return member


def SaveIfChanged(new_member):
    """Saves the member to datastore if any of its fields have changed.

    Args:
      new_member: freesidemodels.Member, possibly changed Member object.
    Returns:
      freesidemodels.member
    """
    orig_member = freesidemodels.Member.get_by_key_name(str(new_member.key()))
    def _CompareAttr(attr):
        return getattr(orig_member, attr) != getattr(new_member, attr)
    if any(map(_CompareAttr, dir(orig_member))):
        return SaveMember(new_member)
    return new_member


def GetActiveMembers():
    """Gets all active members from datastore.

    Returns:
      list of freesidemodels.Member
    """
    return freesidemodels.Member.all().filter('active =', True).fetch(1000)


def GetMemberByUsername(username, active=True):
    """Gets a member by his or her username.

    Args:
      username: str, the member's username.
      active: bool, whether to fetch only an active member.
    Returns:
      freesidemodels.Member or None
    """
    q = freesidemodels.Member.all().filter('username =', username)
    if active:
        q.filter('active =', True)

    result = q.fetch(1)
    if len(result) == 1:
        return result[0]
    else:
        return None


def GetMemberByEmail(email, active=True):
    """Gets a member by his or her email address.

    Args:
      email: str, the member's email address.
      active: bool, whether to fetch only an active member.
    Returns:
      freesidemodels.Member or None
    """
    q = freesidemodels.Member.all().filter('email =', email)
    if active:
        q.filter('active =', True)

    result = q.fetch(1)
    if len(result) == 1:
        return result[0]
    else:
        return None
