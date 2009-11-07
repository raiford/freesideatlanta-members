import datetime
import hashlib
import random

from google.appengine.ext import db
from google.appengine.tools import bulkloader
import freesidemodels

def randompassword(x):
  alphabet = 'abcdefghijklmnopqrstuvwxyz1234567890'
  string=''
  for x in random.sample(alphabet,10):
    string+=x
  return hashlib.sha256(string).digest()



def truefalse(x):
  if x == 'TRUE':
    return True
  else:
    return False

class MemberLoader(bulkloader.Loader):
  """Parse csv and upload it."""
  def __init__(self):
    bulkloader.Loader.__init__(self, 'Member',
                               [('username', str),
                                ('email', db.Email),
                                ('active', truefalse),
                                ('starving', truefalse),
                                ('joined', 
                                  lambda x: datetime.datetime.strptime(x, '%m/%d/%Y').date()),
                                ('rfid', int),
                                ('password', randompassword),
                               ])

loaders = [MemberLoader]
