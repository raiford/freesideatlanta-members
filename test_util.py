#!/usr/bin/env python

"""Base class for tests involving the AppEngine stack."""

import os
import time
import unittest

from google.appengine.api import apiproxy_stub_map
from google.appengine.api import datastore_file_stub
from google.appengine.api import mail_stub
from google.appengine.api import urlfetch_stub
from google.appengine.api import user_service_stub

APP_ID = u'freesideatlanta-members'
AUTH_DOMAIN = 'gmail.com'
LOGGED_IN_USER = 'test_user@example.com'


class AppEngineTestBase(unittest.TestCase):
    """Base class for tests involving the AppEngine stack."""

    def setUp(self):
        # Ensure we're in UTC.
        os.environ['TZ'] = 'UTC'
        time.tzset()

        # Start with a fresh api proxy.
        apiproxy_stub_map.apiproxy = apiproxy_stub_map.APIProxyStubMap()

        # Use a fresh stub datastore.
        self.__datastore_stub = datastore_file_stub.DatastoreFileStub(
            APP_ID, '/dev/null', '/dev/null')
        apiproxy_stub_map.apiproxy.RegisterStub(
            'datastore_v3', self.__datastore_stub)
        os.environ['APPLICATION_ID'] = APP_ID

        # Use a fresh stub UserService.
        apiproxy_stub_map.apiproxy.RegisterStub(
            'user', user_service_stub.UserServiceStub())
        os.environ['AUTH_DOMAIN'] = AUTH_DOMAIN
        os.environ['USER_EMAIL'] = LOGGED_IN_USER

        # Use a fresh urlfetch stub.
        apiproxy_stub_map.apiproxy.RegisterStub(
            'urlfetch', urlfetch_stub.URLFetchServiceStub())

        # Use a fresh mail stub.
        apiproxy_stub_map.apiproxy.RegisterStub(
            'mail', mail_stub.MailServiceStub())

    def tearDown(self):
        self.__datastore_stub.Clear()
