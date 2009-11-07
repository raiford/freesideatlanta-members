#!/usr/bin/env/python

"""Utility functions for making random objects."""

import datetime
import random
import string
import hashlib

import freesidemodels


NAMES = (
    'George Washington', 'John Adams', 'Thomas Jefferson', 'James Madison',
    'James Monroe', 'John Quincy Adams', 'Andrew Jackson', 'Martin Van Buren',
    'William Henry Harrison', 'John Tyler', 'James K. Polk', 'Zachary Taylor',
    'Millard Fillmore', 'Franklin Pierce', 'James Buchanan', 'Aberham Lincoln',
    'Andrew Johnson', 'Ulysses S. Grant', 'Rutherford B. Hayes',
    'James A. Garfield', 'Chester A. Arthur', 'Grover Cleveland')


def _NameAttributes(name):
    """Gets attributes about a name.

    Returns:
      dict with keys: 'firstname', 'lastname', 'username', 'email'
    """
    first_name = name.split()[0]
    last_name = name.split()[-1]
    username = '%s%s' % (first_name[0].lower(), last_name.lower())
    return {
        'firstname': first_name,
        'lastname': last_name,
        'username': username,
        'email': '%s@domain.com' % username}


def RandomPassword():
    """Generates a sha256-encoded random ten letter password.

    Returns:
      str, sha256-encoded random ten letter password.
    """
    password = ''.join(random.sample(string.lowercase + string.digits, 10))
    return hashlib.sha256(password).digest()


def _PersonDict(active=True, admin=False):
    """Creates a dict containing key/value pairs for a freesidemodels.Person.

    Returns:
      dict
    """
    # TODO(dknowles): Populate "left" if active is False
    name_dict = _NameAttributes(random.choice(NAMES))
    name_dict.update(
        {'password': RandomPassword(),
         'active': active,
         'admin': admin,
         'joined': datetime.date(2009, 01, 15)})
    return name_dict


def RandomPerson(active=True, admin=False):
    """Creates a random person.

    """
    return freesidemodels.Person(**_PersonDict(active=active, admin=admin))


def RandomMember(active=True, admin=False, starving=False):
    """Creates a random member.

    This does not add the member to datastore.

    Returns:
      freesidemodels.Member
    """
    return freesidemodels.Member(
        starving=starving,
        rfid=random.randint(0, 1000),
        **_PersonDict(active=active, admin=admin))
