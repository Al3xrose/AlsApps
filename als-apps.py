#als-apps.py

import os
import webapp2
import jinja2
from handler import Handler

from google.appengine.ext import db

class MainPage(Handler):
	def get(self):
		self.render("mainpage.html")

app = webapp2.WSGIApplication([('/', MainPage)], debug=True)