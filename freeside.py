#!/usr/bin/env python

"""Main web handlers."""

import datetime
import logging
import operator
import os
import random
import sys
import urllib

from google.appengine.api import mail
from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp import util

from appengine_utilities.sessions import Session

import freesidemodels
import member_util
import timezones


class Error(Exception):
  """Base error class for this module."""


def set_trace():
  """Hack to make pdb work with AppEngine SDK."""
  for attr in ('stdin', 'stdout', 'stderr'):
     setattr(sys, attr, getattr(sys, '__%s__' % attr))
  import pdb
  pdb.set_trace()


def RedirectIfUnauthorized(fn):
  """Decorator to redirect back to /login if user is not logged in.

  Args:
    fn: callable, function to decorate
  Returns:
    decorated function
  """
  def MaybeRedirect(self, *args, **kwargs):
    if not self.CheckAuth():
      self.redirect('/login')
    else:
      return fn(self, *args, **kwargs)

  MaybeRedirect.__name__ = fn.__name__
  MaybeRedirect.__doc__ = fn.__doc__
  return MaybeRedirect


def RedirectIfNotAdmin(fn):
  """Decorator to redirect back to /home if user is not an administrator.

  Args:
    fn: callable, function to decorate
  Returns:
    decorated function
  """
  def MaybeRedirect(self, *args, **kwargs):
    if not self.CheckAdmin():
      self.redirect('/home')
    else:
      return fn(self, *args, **kwargs)

  MaybeRedirect.__name__ = fn.__name__
  MaybeRedirect.__doc__ = fn.__doc__
  return MaybeRedirect


class FreesideHandler(webapp.RequestHandler):
  """Request Handler with some common functions."""

  def __init__(self):
    super(FreesideHandler, self).__init__()
    self.session = Session()

  def GetSideBar(self):
    """Generate the sidebar list."""
    sidebar = [
        {'name': 'Home', 'path': '/home'},
        {'name': 'Members', 'path': '/members'},
        {'name': 'Elections', 'path': '/elections'},
    ]
    if self.CheckAdmin():
      sidebar.append({'name': 'Admin', 'path': '/admin'})

    for page in sidebar:
      page['selected'] = page['path'] in self.request.path

    return sidebar

  def RenderTemplate(self, template_name, template_values):
    """Helper function to render a template.

    Args:
      template_name: str, name of the template to render
      template_values: dict, values to pass to the template
    """
    if self.CheckAuth():
      if 'sidebar' not in template_values:
        template_values['sidebar'] = self.GetSideBar()
      if 'user' not in template_values:
        template_values['user'] = self.session['user']
      template_values['admin'] = self.CheckAdmin()
    template_path = os.path.join('templates', template_name)
    self.response.out.write(template.render(template_path, template_values))

  def CheckAuth(self):
    """Determines if the current user has logged in.

    Returns:
      bool
    """
    return 'user' in self.session

  def CheckAdmin(self):
    """Determines if the current user is a site admin.

    Returns:
      bool
    """
    return self.session['user'].admin


class LoginPage(FreesideHandler):
  """The login page request handler."""

  def get(self):
    self.RenderTemplate('login.html', {})

  def post(self):
    username = self.request.get('username')
    user = member_util.GetMemberByUsername(username)
    if not user:
      # Try finding user by email.
      user = member_util.GetMemberByEmail(self.request.get(username))

    hashedpass = freesidemodels.Person.EncryptPassword(
      self.request.get('password'))
    if user and hashedpass == user.password:
      self.session['user'] = user
      self.redirect('/home')
    else:
      # TODO invalid username/password message
      self.redirect('/login')


class AdminPage(FreesideHandler):
  """The admin page request hanndler."""

  admintasks = {
    'AddMember': 'Add Member',
    'AddElection': 'Add Election',
    'ResetPassword': 'Reset Password',
  }
  electiontypes = freesidemodels.GetAllElectionTypes()
  positions = ['President', 'Treasurer', 'Secretary', 'Board Member']

  def ResetPassword(self):
    """Scramble a members password and email it to them."""
    memberkey = self.request.get('resetmember')
    member = db.get(memberkey)
    # check that the member is active
    if not member_util.IsActiveMember(member):
      template_values = {'errortxt': 'Member is not active'}
      self.RenderTemplate('error.html', template_values)
      return
    # check that the members email address is valid
    if not mail.is_email_valid(member.email):
      template_values = {'errortxt': 'Members email is not valid'}
      self.RenderTemplate('error.html', template_values)
      return
    member_util.ResetAndEmailPassword(member)
    self.redirect('/admin?&task=ResetPassword')

  def AddMember(self):
    """Add a new member to the database."""
    #member_dict = dict(
    #  (p, self.request.get(p)) for p, cls in freesidemodels.Member._properties)
    member = member_util.SaveMember(
      member_util.MakeMember(
        username=self.request.get('username'),
        firstname=self.request.get('firstname'),
        lastname=self.request.get('lastname'),
        email=self.request.get('email'),
        password=self.request.get('password'),
        starving=self.request.get('starving') == 'True'))
    self.redirect('/admin')

  def _ParseDate(self, date_str, tzinfo=timezones.Eastern()):
    """Parses a date string in format "MM/DD/YYYY".

    Args:
      date_str: date string in format "MM/DD/YYYY"
      tzinfo: datetime.tzinfo, timezone for the date
    Returns:
      datetime.datetime
    """
    month, day, year = map(int, date_str.split('/'))
    return datetime.datetime(
      year=year, month=month, day=day, hour=0, minute=0, second=0)

  def AddElection(self):
    """Creates a new election."""
    # TODO(dknowles): Move this to election_util
    nominate_start = self._ParseDate(self.request.get('nomination_start'))
    nominate_end = self._ParseDate(self.request.get('nomination_end'))
    vote_start = self._ParseDate(self.request.get('vote_start'))
    vote_end = self._ParseDate(self.request.get('vote_end'))

    if not nominate_start < nominate_end <= vote_start < vote_end:
      raise Error('Dates are not in order.')

    election_type = self.request.get('election_type')
    if election_type not in self.electiontypes:
      raise Error('Invalid election type.')

    new_election = getattr(freesidemodels, election_type)(
      position=self.request.get('position'),
      nominate_start=nominate_start,
      nominate_end=nominate_end,
      vote_start=vote_start,
      vote_end=vote_end,
      description=self.request.get('description'))
    new_election.put()
    self.redirect('/admin')

  @RedirectIfUnauthorized
  @RedirectIfNotAdmin
  def get(self):
    template_values = {
      'admintasks': self.admintasks.items(),
      'admintask': self.request.get('task'),
      'electiontypes': self.electiontypes,
      'positions': self.positions,
      }
    if template_values['admintask'] == 'ResetPassword':
      members = sorted(member_util.GetActiveMembers(), key=lambda m: m.username)
      template_values['members'] = members
    self.RenderTemplate('admin.html', template_values)

  @RedirectIfUnauthorized
  @RedirectIfNotAdmin
  def post(self):
    task = self.request.get('task')
    if task not in self.admintasks:
      self.redirect('./')
    else:
      getattr(self, task)()


class HomePage(FreesideHandler):
  """The default landing page."""

  @RedirectIfUnauthorized
  def get(self):
    self.RenderTemplate('home.html', {})


class MembersList(FreesideHandler):
  """The Members List."""

  @RedirectIfUnauthorized
  def get(self):
    members = sorted(member_util.GetActiveMembers(), key=lambda m: m.username)
    self.RenderTemplate('members.html', {'members': members})


class Profile(FreesideHandler):
  """Display the details about a member."""

  @RedirectIfUnauthorized
  def get(self, username):
    """Shows details about a member."""
    member = member_util.GetMemberByUsername(urllib.unquote(username))
    if not member:
      self.redirect('/members')
      return

    user = self.session['user']
    edit = self.request.get('mode') == 'edit'
    canedit = user.key() == member.key() or user.admin

    self.RenderTemplate(
      'profile.html',
      {'member': member, 'canedit': canedit, 'edit': edit})

  @RedirectIfUnauthorized
  def post(self, username):
    """Modifies a Member."""
    member = member_util.GetMemberByUsername(urllib.unquote(username))
    if member is None:
      self.RenderTemplate(
          'error.html',
          {'errortxt': 'Could not find member with username: %s' % username})
      return

    currentpass = self.request.get('currentpass')
    newpass = self.request.get('newpass')
    if currentpass and newpass:
      if freesidemodels.Person.EncryptPassword(currentpass) != member.password:
        template_values = {'errortxt': 'Incorrect Password. Please try again.'}
        self.RenderTemplate('error.html', template_values)
        return
      else:
        member.password = freesidemodels.Person.EncryptPassword(newpass)
        member.password_expired = False

    member.firstname = self.request.get('firstname')
    member.lastname = self.request.get('lastname')
    member.email = self.request.get('email')

    newusername = self.request.get('username')
    if newusername != member.username:
      if member_util.GetMemberByUsername(newusername) is None:
        member.username = newusername
      else:
        template_values = {'errortxt': 'Requested username is already in use.'}
        self.RenderTemplate('error.html', template_values)
        return

    member_util.SaveIfChanged(member)
    self.redirect('/members/%s' % member.username)


class Elections(FreesideHandler):
  """Serve the voting page."""

  def _GetActiveElections(self, election_type):
    if election_type not in freesidemodels.GetAllElectionTypes():
      raise Error('Invalid election type')

    return getattr(freesidemodels, election_type).all().filter(
      'vote_end >=', datetime.datetime.now(timezones.UTC())).fetch(1000)

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
      random.shuffle(election.nominators)
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
      raise Error('You can\'t nominate yourself.')

    # you can only nominate once
    if self.session['user'].key() in election.nominators:
      raise Error('You can only nominate once.')

    # Verify that the election is accepting nominations
    if not election.nominate_start < now < election.nominate_end:
      # TODO Error page
      raise Error('Election is not accepting nominations.')

    # Verify the nominee is valid for the election type.
    if electiontype == 'OfficerElection' and nomineetype != 'Member':
      # TODO Replace with an error page.
      raise Error('Nominee is not a member')
    elif electiontype == 'BoardElection' and nomineetype not in ['Member', 'Person']:
      # TODO Replace with an error page.
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
      random.shuffle(election.voters)
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

  @RedirectIfUnauthorized
  def get(self):
    now = datetime.datetime.now(timezones.UTC())
    current_elections = map(
      self._GetActiveElections, freesidemodels.GetAllElectionTypes())
    # Flatten the current_elections list
    current_elections = [
      election for elections in current_elections for election in elections]

    voting = []
    nominating = []
    ended = []
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
        for member in member_util.GetActiveMembers():
          if member.key() not in election.nominees and member.key() != user.key():
            eligible.append(member)
        for nomineekey in election.nominees:
          nominees.append(db.get(nomineekey))
        nominating.append({'election': election,
                           'eligible': eligible,
                           'nominate_end': nominate_end.astimezone(timezones.Eastern()),
                           'nominees': nominees,
                           'has_nominated': has_nominated})
      elif vote_start < now < vote_end:
        eligible = []
        has_voted = user.key() in election.voters
        for nominee in election.nominees:
            eligible.append(db.get(nominee))
        voting.append({'election': election,
                       'eligible': eligible,
                       'has_voted': has_voted,
                       'vote_end': vote_end.astimezone(timezones.Eastern())})
      elif vote_end < now:
        total_votes = len(election.votes)
        vote_totals = {}
        for vote in election.votes:
          member = db.get(vote)
          if member.username in vote_totals:
            vote_totals[member.username] += 1
          else:
            vote_totals[member.username] = 1
        ended.append({'election': election,
                      'totals': sorted(vote_totals.iteritems(),
                                       key=operator.itemgetter(1),
                                       reverse=True),
                      'vote_end': vote_end.astimezone(timezones.Eastern())})

    template_values = {'voting': voting,
                       'nominating': nominating,
                       'ended': ended}
    self.RenderTemplate('vote.html', template_values)

  @RedirectIfUnauthorized
  def post(self):
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
    self.session.delete()
    self.redirect('/login')


def main():
  url_map = {
    r'/': HomePage,
    r'/login': LoginPage,
    r'/home/?': HomePage,
    r'/admin/?': AdminPage,
    r'/members/?': MembersList,
    r'/members/(.*)': Profile,
    r'/logout': Logout,
    r'/elections/?': Elections}
  util.run_wsgi_app(webapp.WSGIApplication(url_map.items(), debug=True))


if __name__ == '__main__':
  main()
