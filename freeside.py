import os
import hashlib
import datetime

from google.appengine.ext import webapp
from google.appengine.ext import db
from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext.webapp import template

from appengine_utilities.sessions import Session

import freesidemodels


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
    nomination_start = self.request.get('nomination_start')
    nomination_end = self.request.get('nomination_end')
    vote_start = self.request.get('vote_start')
    vote_end = self.request.get('vote_end')
    description = self.request.get('description')
    
    nominate_start = nominate_start.split('/')
    nominate_start = datetime.datetime(nominate_start[2],
                                       nominate_start[0],
                                       nominate_start[1])
    nominate_end = nominate_end.split('/')
    nominate_end = datetime.datetime(nominate_end[2],
                                     nominate_end[0],
                                     nominate_end[1])
    vote_start = vote_start.split('/')
    vote_start = datetime.datetime(vote_start[2],
                                   vote_start[0],
                                   vote_start[1])
    vote_end = vote_end.split('/')
    vote_end = datetime.datetime(vote_end[2],
                                 vote_end[0],
                                 vote_end[1])


    if election_type == 'OfficerElection':
      new_election = freesidemodels.OfficerElection(position=position,
                                                    nominate_start=nominate_start,
                                                    nominate_end=nominate_end,
                                                    vote_start=vote_end,
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
    task = self.request.get('task')


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
    q = db.GqlQuery("SELECT * FROM OfficerElection " +
                    "WHERE vote_end >= DATETIME(:1) " +
                    "ORDER BY vote_end",
                    str(datetime.datetime.now()).split('.')[0])
    # get rid of any elections that have not started.
    current_elections = []
    for election in q:
      if election.nominate_start < datetime.datetime.now():
        current_elections.append(election)

    voting = []
    nominating = []
    now = datetime.datetime.now()
    members = self.GetActiveMembers()
    # Sort current electionns by voting and nominating
    for election in current_elections:
      if election.nominate_start < now < election.nominate_end:
        eligible = []
        for member in members:
          if member.key() not in election.nominees:
            eligible.append(member)
        nominating.append({'election': election, 'eligible': eligible})
      elif election.vote_start < now < election.vote_end:
        eligible = []
        for member in members:
          if member.key() in election.nominees:
            eligible.append(member)
        voting.append({'election': election, 'eligible': eligible})
      else:
        raise Error('Error in the election dates.')

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
