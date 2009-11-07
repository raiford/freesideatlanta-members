#!/usr/bin/env python

"""Bulk loader for loading members into datastore."""

import datetime
import hashlib
import random
import string

from google.appengine.ext import db
from google.appengine.tools import bulkloader

import freesidemodels


def str_to_bool(s):
  """Casts a string like "TRUE" or "FALSE" into a bool.

  Args:
    s: str, boolean string--either "TRUE" or "FALSE"
  Returns:
    bool
  """
  return s == 'TRUE'


def random_password():
  """Generates a sha256-encoded random ten letter password.

  Returns:
    str, sha256-encoded random ten letter password.
  """
  password = ''.join(random.sample(string.lowercase + string.digits, 10))
  return hashlib.sha256(password).digest()


class MemberLoader(bulkloader.Loader):
  """Parse CSV of members and upload it to datastore."""

  def __init__(self):
    bulkloader.Loader.__init__(
      self,
      'Member',
      [('username', str),
       ('email', db.Email),
       ('active', lambda x : x == 'TRUE'),
       ('starving', truefalse),
       ('joined', lambda x: datetime.datetime.strptime(x, '%m/%d/%Y').date()),
       ('rfid', int),
       ('password', random_password)])


loaders = [MemberLoader]
