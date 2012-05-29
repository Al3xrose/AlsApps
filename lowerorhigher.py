#lowerorhigher.py

import webapp2
from handler import Handler

class LowerOrHigherPage(Handler):
	def get(self):
		self.render("lowerOrHigher.html")

app = webapp2.WSGIApplication([('/lowerorhigher', LowerOrHigherPage)], debug=True)