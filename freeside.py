import os
import hashlib
import datetime
import sys
from random import shuffle

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from appengine_utilities.sessions import Session

import freesidemodels
import timezones


class Error(Exception):
  """Basic Error."""

def d():
  # a hack to make pdb work with app engine SDK
  for attr in ('stdin', 'stdout', 'stderr'):
     setattr(sys, attr, getattr(sys, '__%s__' % attr))
  import pdb
  pdb.set_trace()


class FreesideHandler(webapp.RequestHandler):
  """Request Handler with some common functions."""
  def __init__(self):
    super(FreesideHandler, self).__init__()
    self.session = Session(set_cookie_expires=False)

  def GetSideBar(self):
    """Generate the sidebar list."""
    sidebar = [
        {'name': 'Home', 'path': '/home'},
        {'name': 'Members', 'path': '/members'},
        {'name': 'Elections', 'path': '/elections'},
    ]
    if self.session['user'].admin:
      sidebar.append({'name': 'Admin', 'path': '/admin'})

    for page in sidebar:
      if self.request.path == page['path']:
        page.update({'selected': True})

    return sidebar

  def RenderTemplate(self, template_name, template_values):
    path = os.path.join('templates', template_name)
    if 'user' in self.session:
      if 'sidebar' not in template_values:
        template_values.update({'sidebar': self.GetSideBar()})
      if 'user' not in template_values:
        template_values.update({'user': self.session['user']})
    self.response.out.write(template.render(path, template_values))

  def CheckAuth(self):
    if 'user' not in self.session:
      self.redirect('/login')

  def CheckAdmin(self):
    self.CheckAuth()
    if not self.session['user'].admin:
      self.redirect('/home')

  def GetActiveMembers(self):
    """Return a query object with all active members."""
    q = db.GqlQuery("SELECT * FROM Member " +
                    "WHERE active = TRUE")
    return q


class LoginPage(FreesideHandler):
  """The login page request handler."""
  def get(self):
    template_values = {}
    self.response.out.write(template.render('templates/login.html', template_values))

  def post(self):
    username = self.request.get('username')
    password = self.request.get('password')
    hashedpass = hashlib.sha256(password).digest()
    usernameq = db.GqlQuery("SELECT * FROM Member WHERE username = :1 AND active = True", username)
    user = usernameq.get()
    # Try looking up by email if username was not found
    if not user:
      emailq = db.GqlQuery("SELECT * FROM Member WHERE email = :1 AND active = True", username)
      user = emailq.get()
    if user and hashedpass == user.password:
        self.session['user'] = user
        self.redirect('/home')
    else:
      # TODO invalid username/password message
      self.redirect('/login')


class AdminPage(FreesideHandler):
  """The admin page request hanndler."""
  admintasks = {
      'addmember': 'Add Member',
      'addelection': 'Add Election',
  }
  electiontypes = ['BoardElection', 'OfficerElection']
  positions = ['President', 'Treasurer', 'Secretary', 'Board Member']

  def AddMember(self):
    """Add a new member to the database."""
    username = self.request.get('username')
    firstname = self.request.get('firstname')
    lastname = self.request.get('lastname')
    email = self.request.get('email')
    password = self.request.get('password')

    hashedpass = hashlib.sha256(password).digest()
    newmember = freesidemodels.Member(username=username,
                                      firstname=firstname,
                                      lastname=lastname,
                                      email=email,
                                      password=hashedpass,
    )

    if self.request.get('starving') == 'True':
      newmember.starving = True
    newmember.put()
    self.redirect('/admin')

  def AddElection(self):
    """Create an election."""
    election_type = self.request.get('election_type')
    position = self.request.get('position')
    nominate_start = self.request.get('nomination_start')
    nominate_end = self.request.get('nomination_end')
    vote_start = self.request.get('vote_start')
    vote_end = self.request.get('vote_end')
    description = self.request.get('description')

    nominate_start = nominate_start.split('/')
    nominate_start = map(int, nominate_start)
    nominate_start = datetime.datetime(year=nominate_start[2],
                                       month=nominate_start[0],
                                       day=nominate_start[1],
                                       tzinfo=timezones.Eastern())
    nominate_end = nominate_end.split('/')
    nominate_end = map(int, nominate_end)
    nominate_end = datetime.datetime(year=nominate_end[2],
                                     month=nominate_end[0],
                                     day=nominate_end[1],
                                     tzinfo=timezones.Eastern())
    vote_start = vote_start.split('/')
    vote_start = map(int, vote_start)
    vote_start = datetime.datetime(year=vote_start[2],
                                   month=vote_start[0],
                                   day=vote_start[1],
                                   tzinfo=timezones.Eastern())
    vote_end = vote_end.split('/')
    vote_end = map(int, vote_end)
    vote_end = datetime.datetime(year=vote_end[2],
                                 month=vote_end[0],
                                 day=vote_end[1],
                                 tzinfo=timezones.Eastern())

    if not nominate_start < nominate_end <= vote_start < vote_end:
      raise Error('Dates are not in order.')


    if election_type == 'OfficerElection':
      new_election = freesidemodels.OfficerElection(position=position,
                                                    nominate_start=nominate_start,
                                                    nominate_end=nominate_end,
                                                    vote_start=vote_start,
                                                    vote_end=vote_end,
                                                    description=description)
    elif election_type == 'BoardElection':
      new_election = freesidemodels.BoardElection(position=position,
                                                  nominate_start=nominate_start,
                                                  nominate_end=nominate_end,
                                                  vote_start=vote_start,
                                                  vote_end=vote_end,
                                                  description=description)
    else:
      raise Error('Unknown Election Type')

    new_election.put()
    self.redirect('/admin')


  def get(self):
    self.CheckAdmin()
    template_values = {'admintasks': self.admintasks}
    task =  self.request.get('task')
    template_values.update({'admintask': task})
    template_values.update({'electiontypes': self.electiontypes})
    template_values.update({'positions': self.positions})
    self.RenderTemplate('admin.html', template_values)

  def post(self):
    self.CheckAdmin()
    admin_methods = {'addmember': self.AddMember,
                     'addelection': self.AddElection,
    }
    task = self.request.get('task')
    admin_methods[task]()


class HomePage(FreesideHandler):
  """The default landing page."""
  def get(self):
    self.CheckAuth()
    template_values = {}
    self.RenderTemplate('base.html', template_values)


class MembersList(FreesideHandler):
  """The Members List."""
  def get(self):
    self.CheckAuth()

    q = db.GqlQuery("SELECT * FROM Member " +
                    "WHERE active = True")
    template_values = {'members': q}
    self.RenderTemplate('members.html', template_values)


class Elections(FreesideHandler):
  """Serve the voting page."""
  def GetOfficerElections(self):
    """Return a list of current officer elections."""
    now = datetime.datetime.now(timezones.UTC())
    q = db.GqlQuery("SELECT * FROM OfficerElection " +
                    "WHERE vote_end >= DATETIME(:1) " +
                    "ORDER BY vote_end",
                    str(now).split('.')[0])
    # get rid of any elections that have not started.
    officer_elections = []
    for election in q:
      if election.nominate_start.replace(tzinfo=timezones.UTC()) < now:
        officer_elections.append(election)

    return officer_elections

  def GetBoardElections(self):
    """Return a list of current board elections."""
    now = datetime.datetime.now(timezones.UTC())
    q = db.GqlQuery("SELECT * FROM BoardElection " +
                    "WHERE vote_end >= DATETIME(:1) " +
                    "ORDER BY vote_end",
                    str(now).split('.')[0])
    # get rid of any elections that have not started.
    board_elections = []
    for election in q:
      if election.nominate_start.replace(tzinfo=timezones.UTC()) < now:
        board_elections.append(election)

    return board_elections

  def _NominateTransaction(self, election_key, nominee_key):
    """Class to wrap the actual nomination in a transaction."""
    election = db.get(election_key)
    userkey = self.session['user'].key()
    if nominee_key not in election.nominees:
      election.nominees.append(nominee_key)
    else:
      raise db.Rollback('Person already nominated')

    if userkey not in election.nominators:
      election.nominators.append(userkey)
      # shuffle the nominators so they are anonymous
      shuffle(election.nominators)
    else:
      raise db.Rollback('You have already nominated someone')

    election.put()

  def Nominate(self, election_key, nominee_key):
    """Nominate a member for an election."""
    election = db.get(election_key)
    nominee = db.get(nominee_key)
    electiontype = election.kind()
    nomineetype = nominee.kind()
    now = datetime.datetime.now()

    # You can't nominate yourself
    if nominee_key == self.session['user'].key():
      raise Error('You cant nominate yourself')

    # you can only nominate once
    if self.session['user'].key() in election.nominators:
      raise Error('You can only nominate once')

    # Verify that the election is accepting nominations
    if not election.nominate_start < now < election.nominate_end:
      #TODO Error page
      raise Error('Election is not accepting nominations')

    # Verify the nominee is valid for the election type.
    if electiontype == 'OfficerElection' and nomineetype != 'Member':
      #TODO Replace with an error page.
      raise Error('Nominee is not a member')
    elif electiontype == 'BoardElection' and nomineetype not in ['Member', 'Person']:
      #TODO Replace with an error page.
      raise Error('Nominee is not a member or person')

    nominee_key = nominee.key()
    election_key = election.key()
    db.run_in_transaction(self._NominateTransaction, election_key, nominee_key)

  def _VoteTransaction(self, election_key, vote_key):
    """Transaction to handle the vote."""
    election = db.get(election_key)
    userkey = self.session['user'].key()
    if userkey not in election.voters:
      election.voters.append(userkey)
      election.votes.append(vote_key)
      # shuffle the voters so they are anonymous
      shuffle(election.voters)
    else:
      raise db.Rollback('You have already voted someone')

    election.put()

  def Vote(self, election_key, vote_key):
    """Cast a Vote."""
    election = db.get(election_key)
    vote = db.get(vote_key)
    now = datetime.datetime.now()

    # Make sure the election is accepting votes
    if not election.vote_start < now < election.vote_end:
      raise Error('Election is not accepting Votes')

    # Make sure that the vote was nominated
    if vote_key not in election.nominees:
      raise Error('Your vote was not nominated')

    # You can only vote once
    if self.session['user'].key() in election.voters:
      raise Error('You already voted')

    db.run_in_transaction(self._VoteTransaction, election_key, vote_key)

  def get(self):
    self.CheckAuth()
    now = datetime.datetime.now(timezones.UTC())
    current_elections = []
    current_elections.extend(self.GetOfficerElections())
    current_elections.extend(self.GetBoardElections())

    voting = []
    nominating = []
    user = self.session['user']
    # Sort current elections by voting and nominating
    for election in current_elections:
      nominate_start = election.nominate_start.replace(tzinfo=timezones.UTC())
      nominate_end = election.nominate_end.replace(tzinfo=timezones.UTC())
      vote_start = election.vote_start.replace(tzinfo=timezones.UTC())
      vote_end = election.vote_end.replace(tzinfo=timezones.UTC())
      if nominate_start < now < nominate_end:
        eligible = []
        nominees = []
        has_nominated = user.key() in election.nominators
        for member in self.GetActiveMembers():
          if member.key() not in election.nominees and member.key() != user.key():
            eligible.append(member)
        for nomineekey in election.nominees:
          nominees.append(db.get(nomineekey))
        nominating.append({'election': election,
                           'eligible': eligible,
                           'nominate_end': nominate_end.astimezone(timezones.Eastern()),
                           'nominees': nominees,
                           'has_nominated': has_nominated})
      elif vote_start < now < vote_end and user.key():
        eligible = []
        has_voted = user.key() in elections.voters
        for nominee in election.nominees:
            eligible.append(db.get(nominee))
        voting.append({'election': election,
                       'eligible': eligible,
                       'vote_end': vote_end.astimezone(timezones.Eastern())})

    template_values = {'voting': voting,
                       'nominating': nominating,}
    self.RenderTemplate('vote.html', template_values)

  def post(self):
    self.CheckAuth()
    arguments = self.request.arguments()
    vote = self.request.get('vote')
    nomination = self.request.get('nomination')
    election = self.request.get('election')
    election_key = db.Key(election)

    if nomination:
      nominee_key = db.Key(nomination)
      self.Nominate(election_key, nominee_key)
    elif vote:
      vote_key = db.Key(vote)
      self.Vote(election_key, vote_key)

    self.redirect('/elections')


class Logout(FreesideHandler):
  """Log the user out."""
  def get(self):
    self.CheckAuth()
    self.session.delete()
    self.redirect('/login')

application = webapp.WSGIApplication([('/', HomePage),
                                      ('/login', LoginPage),
                                      ('/home', HomePage),
                                      ('/admin', AdminPage),
                                      ('/members', MembersList),
                                      ('/logout', Logout),
                                      ('/elections', Elections),],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
