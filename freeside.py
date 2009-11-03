import os
import hashlib
import datetime
import sys

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from appengine_utilities.sessions import Session

import freesidemodels


class UTC(datetime.tzinfo):
  """Plain old UTC time."""
  def utcoffset(self, dt):
    return datetime.timedelta(0)

  def tzname(self, dt):
    return 'UTC'

  def dst(self, dt):
    return datetime.timedelta(0)


class Eastern(datetime.tzinfo):
  """An implementation of the Eastern time zone.

  This is necessary because data store only uses UTC.
  """
  def utcoffset(self, dt):
    return datetime.timedelta(hours=-5) + self.dst(dt)

  def _FirstSunday(self, dt):
    return dt + datetime.timedelta(days=(6-dt.weekday()))

  def dst(self, dt):
    # 2 am on the second Sunday in March
    dst_start = self._FirstSunday(datetime.datetime(dt.year, 3, 8, 2))
    # 1 am on the first Sunday in November
    dst_end = self._FirstSunday(datetime.datetime(dt.year, 11, 1, 1))

    if dst_start <= dt.replace(tzinfo=None) < dst_end:
      return datetime.timedelta(hours=1)
    else:
      return datetime.timedelta(hours=0)

  def tzname(self, dt):
    if self.dst(dt) == datetime.timedelta(hour=0):
      return "EST"
    else:
      return "EDT"


def d():
  # a hack to make pdb work with app engine
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
        {'name': 'Vote', 'path': '/vote'},
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
                                       tzinfo=Eastern())
    nominate_end = nominate_end.split('/')
    nominate_end = map(int, nominate_end)
    nominate_end = datetime.datetime(year=nominate_end[2],
                                     month=nominate_end[0],
                                     day=nominate_end[1],
                                     tzinfo=Eastern())
    vote_start = vote_start.split('/')
    vote_start = map(int, vote_start)
    vote_start = datetime.datetime(year=vote_start[2],
                                   month=vote_start[0],
                                   day=vote_start[1],
                                   tzinfo=Eastern())
    vote_end = vote_end.split('/')
    vote_end = map(int, vote_end)
    vote_end = datetime.datetime(year=vote_end[2],
                                 month=vote_end[0],
                                 day=vote_end[1],
                                 tzinfo=Eastern())


    if election_type == 'OfficerElection':
      new_election = freesidemodels.OfficerElection(position=position,
                                                    nominate_start=nominate_start,
                                                    nominate_end=nominate_end,
                                                    vote_start=vote_start,
                                                    vote_end=vote_end,
                                                    description=description)
    #TODO add BoardElection once model is complete
    new_election.put()
    self.redirect('/admin')
                                                    

  def get(self):
    self.CheckAdmin()
    template_values = {'admintasks': self.admintasks}
    task =  self.request.get('task')
    template_values.update({'admintask': task})
    template_values.update({'electiontypes': self.electiontypes})
    template_values.update({'positions': ['President', 'Treasurer']})
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


#class MemberPage(FreesideHandler):
#  """Display a member's profile."""
#  def get(self):
#  #TODO Figure out how to get /members/username from the URL


class Vote(FreesideHandler):
  """Serve the voting page."""
  def get(self):
    self.CheckAuth()
    now = datetime.datetime.now(UTC())
    q = db.GqlQuery("SELECT * FROM OfficerElection " +
                    "WHERE vote_end >= DATETIME(:1) " +
                    "ORDER BY vote_end",
                    str(now).split('.')[0])
    # get rid of any elections that have not started.
    current_elections = []
    for election in q:
      if election.nominate_start.replace(tzinfo=UTC()) < now:
        current_elections.append(election)

    voting = []
    nominating = []
    members = self.GetActiveMembers()
    # Sort current elections by voting and nominating
    for election in current_elections:
      nominate_start = election.nominate_start.replace(tzinfo=UTC())
      nominate_end = election.nominate_end.replace(tzinfo=UTC())
      vote_start = election.vote_start.replace(tzinfo=UTC())
      vote_end = election.vote_end.replace(tzinfo=UTC())
      if nominate_start < now < nominate_end:
        eligible = []
        for member in members:
          if member.key() not in election.nominees:
            eligible.append(member)
        nominating.append({'election': election,
                           'eligible': eligible,
                           'nominate_end': nominate_end.astimezone(Eastern())})
      elif vote_start < now < vote_end:
        eligible = []
        for member in members:
          if member.key() in election.nominees:
            eligible.append(member)
        voting.append({'election': election, 'eligible': eligible})
      else:
        raise ValueError('Error in the election dates.')

    template_values = {'voting': voting,
                       'nominating': nominating,}
    self.RenderTemplate('vote.html', template_values)

  def post(self):
    self.CheckAuth()
    arguments = self.request.arguments()
    #TODO parse the post arguments and put them in the database


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
                                      ('/vote', Vote),],
                                     debug=True)

def main():
  run_wsgi_app(application)

if __name__ == '__main__':
  main()
