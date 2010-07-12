#!/usr/bin/env python

import datetime
import os
import random
import re
import string
import sys
import urllib
import urlparse
import wsgiref.handlers

import time

from google.appengine.api import urlfetch
from google.appengine.api import users
from google.appengine.ext import db
from google.appengine.ext import webapp
from google.appengine.ext.webapp import template
from google.appengine.ext.webapp.util import login_required

# Set to true if we want to have our webapp print stack traces, etc
_DEBUG = True

def rfc3339():
    """
    Format a date the way Atom likes it (RFC3339)
    """
    return time.strftime('%Y-%m-%dT%H:%M:%S%z')

class Item(db.Model):
  name = db.StringProperty(required=True)
  text = db.TextProperty()
  created = db.DateTimeProperty(auto_now_add=True)
  updated = db.DateTimeProperty(auto_now=True)

class BaseRequestHandler(webapp.RequestHandler):
  """Supplies a common template generation function.

  When you call generate(), we augment the template variables supplied with
  the current user in the 'user' variable and the current webapp request
  in the 'request' variable.
  """
  def generate(self, template_name, template_values={}):
    values = {
      'request': self.request,
      'user': users.GetCurrentUser(),
      'login_url': users.CreateLoginURL(self.request.uri),
      'logout_url': users.CreateLogoutURL('http://' + self.request.host + '/'),
      'debug': self.request.get('deb'),
      'msg': self.request.get('msg'),
      'application_name': 'meta-box',
    }
    values.update(template_values)
    directory = os.path.dirname(__file__)
    path = os.path.join(directory, os.path.join('templates', template_name))
    self.response.out.write(template.render(path, values, debug=_DEBUG))

class ItemsHandler(BaseRequestHandler):
  """Lists the items """

  @login_required
  def get(self):
      cache=False
      items = db.GqlQuery("SELECT * from Item ORDER BY created")
      self.generate('items.html', {
          'items': items,
      })

  def post(self):
      name = self.request.get('name')
      text = self.request.get('text')
      if (name and text):
          item = Item(name=name,text=text)
          item.put()
      self.redirect('items')

class IndexHandler(BaseRequestHandler):
  def get(self):
      self.generate('index.html')

class ItemHandler(BaseRequestHandler):
  def delete(self,key=''):
      item = Item.get(key);
      item.delete()
  def get(self,key=''):
      item = Item.get(key);
      self.response.headers['Content-Type'] = 'application/json'
      self.response.out.write(item.to_xml())
  def put(self,key=''):
      pass

def main():
  application = webapp.WSGIApplication([
    ('/', ItemsHandler),
    ('/items', ItemsHandler),
    ('/item/(.*)', ItemHandler),
  ], debug=_DEBUG)
  wsgiref.handlers.CGIHandler().run(application)

if __name__ == '__main__':
  main()
