#!/usr/bin/env python

"""Bulk loader for loading members into datastore."""

import datetime

from google.appengine.ext import db
from google.appengine.tools import bulkloader

import freesidemodels
import random_util


def str_to_bool(s):
  """Casts a string like "TRUE" or "FALSE" into a bool.

  Args:
    s: str, boolean string--either "TRUE" or "FALSE"
  Returns:
    bool
  """
  return s == 'TRUE'


class MemberLoader(bulkloader.Loader):
  """Parse CSV of members and upload it to datastore."""

  def __init__(self):
    bulkloader.Loader.__init__(
      self,
      'Member',
      [('username', str),
       ('email', db.Email),
       ('active', str_to_bool),
       ('starving', str_to_bool),
       ('joined', lambda x: datetime.datetime.strptime(x, '%m/%d/%Y').date()),
       ('rfid', int),
       ('password', random_util.Password)])


loaders = [MemberLoader]
