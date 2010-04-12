#!/usr/bin/env python

"""Bulk loader for loading members into datastore."""

import datetime

from google.appengine.ext import db
from google.appengine.tools import bulkloader

import freesidemodels


class PayPalLoader(bulkloader.Loader):
  """Parse CSV from paypal and upload to the datastore."""

  def __init__(self):
    bulkloader.Loader.__init__(
      self,
      'Dues',
      [('time', lambda x: datetime.datetime.strptime(x, '%m/%d/%Y')),
       ('paypalName', str),
       ('gross', float),
       ('paypalFee', float),
       ('net', float),
       ('email', db.Email),
       ('paypalID', str)])


loaders = [PayPalLoader]
