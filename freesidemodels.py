#!/usr/bin/env python

"""Datastore models for Freeside Atlanta's Member Portal."""

import hashlib

from google.appengine.ext import db


class Person(db.Model):
  """Base person class.  Necessary in the case of non-member board nominees."""

  firstname = db.StringProperty()
  lastname = db.StringProperty()
  username = db.StringProperty(required=True)
  email = db.EmailProperty(required=True)
  altemails = db.ListProperty(item_type=db.Email)
  phone = db.PhoneNumberProperty()
  altphones = db.ListProperty(item_type=db.PhoneNumber)
  address = db.PostalAddressProperty()
  # password is hashed with sha256
  password = db.BlobProperty(required=True)
  password_expired = db.BooleanProperty(default=False)
  active = db.BooleanProperty(default=True)
  admin = db.BooleanProperty(default=False)
  joined = db.DateProperty()
  left = db.DateProperty()

  @staticmethod
  def EncryptPassword(password):
    """Encrypts a password using SHA-256 encoding.

    Args:
      password: str, password to encrypt.
    Returns:
      str, encrypted password.
    """
    return hashlib.sha256(password).digest()


class Member(Person):
  """Your basic freeside member."""

  starving = db.BooleanProperty(default=False)
  rfid = db.IntegerProperty()
  doormusic = db.BlobProperty()
  liability = db.BooleanProperty(default=False)
  liabilitypdf = db.BlobProperty()
  picture = db.BlobProperty()
  website = db.StringProperty()


class Election(db.Model):
  """Election Base Class."""

  position = db.StringProperty(required=True)
  description = db.TextProperty()
  nominate_start = db.DateTimeProperty(required=True)
  nominate_end = db.DateTimeProperty(required=True)
  vote_start = db.DateTimeProperty(required=True)
  vote_end = db.DateTimeProperty(required=True)
  # Unique list of Nominees
  nominees = db.ListProperty(item_type=db.Key)
  # List of votes stored as keys to Members or boardmembers
  votes = db.ListProperty(item_type=db.Key)
  # Unique list of member keys to prevent double voting.
  nominators = db.ListProperty(item_type=db.Key)
  voters = db.ListProperty(item_type=db.Key)


def GetAllElectionTypes():
  """Gets all valid election types."""
  return [s.__name__ for s in Election.__subclasses__()]


class OfficerElection(Election):
  """An Officer Election."""


class BoardElection(Election):
  """A Board Member Election."""


class Payment(db.Model):
  """Base class for Payments."""
  gross = db.FloatProperty(required=True)
  net = db.FloatProperty(required=True)
  time = db.DateTimeProperty(required=True)
  gcheckoutTransID = db.StringProperty()
  gcheckoutBuyerID = db.StringProperty()
  gcheckoutFee = db.FloatProperty()
  paypalID = db.StringProperty()
  paypalName = db.StringProperty()
  paypalFee = db.FloatProperty()
  #TODO(raiford): verify payment method is valid from a list.
  paymentmethod = db.StringProperty()
  email = db.EmailProperty()


class Dues(Payment):
  """A members monthly dues."""
  #TODO(raiford): a cron job to audit dues without member set
  member = db.ReferenceProperty()


class Donation(Payment):
  """A donation."""
  firstname = db.StringProperty()
  lastname = db.StringProperty()

