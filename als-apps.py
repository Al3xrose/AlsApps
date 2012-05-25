import os
import webapp2
import jinja2

from google.appengine.ext import db

template_dir = os.path.join(os.path.dirname(__file__), 'templates')
jinja_env = jinja2.Environment(loader = jinja2.FileSystemLoader(template_dir), autoescape = True)

class Handler(webapp2.RequestHandler):
	def write(self, *a, **kw):
		self.response.out.write(*a, **kw)

	def render_str(self, template, **params):
		t = jinja_env.get_template(template)
		return t.render(params)

	def render(self, template, **kw):
		self.write(self.render_str(template, **kw))

class MainPage(Handler):
	def get(self):
		self.render("mainpage.html")

class LowerOrHigherPage(Handler):
	def get(self):
		self.render("lowerOrHigher.html")

class DrawingsPage(Handler):
	def get(self):
		self.render("drawings.html")

app = webapp2.WSGIApplication([('/', MainPage), 
							   ('/lowerorhigher', LowerOrHigherPage),
							   ('/drawings', DrawingsPage)], debug=True)