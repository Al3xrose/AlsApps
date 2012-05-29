#drawings.py

import webapp2
from handler import Handler

class DrawingsPage(Handler):
	def get(self):
		self.render("drawings.html")

app = webapp2.WSGIApplication([('/drawings', DrawingsPage)], debug=True)