from datetime import datetime

from google.appengine.ext import db

from appengine_utilities.sessions import Session


class Person(db.Model):
  """Base person class.  Necessary in the case of non-member board nominees."""
  firstname = db.StringProperty()
  lastname = db.StringProperty()
  #TODO validator method to prevent duplicate usernames
  username = db.StringProperty(required=True)
  email = db.EmailProperty(required=True)
  altemails = db.ListProperty(item_type=db.Email)
  phone = db.PhoneNumberProperty()
  altphones = db.ListProperty(item_type=db.PhoneNumber)
  address = db.PostalAddressProperty()
  # password is hashed with sha256
  password = db.BlobProperty(required=True)
  active = db.BooleanProperty(default=True)
  admin = db.BooleanProperty(default=False)
  joined = db.DateTimeProperty()
  left = db.DateTimeProperty()


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


class OfficerElection(Election):
  """An Officer Election."""


class BoardElection(Election):
  """A Board Member Election."""
