#drawings.py

import webapp2
from handler import Handler

class DrawingsPage(Handler):
	def get(self):
		self.render("drawings.html")
        
class TreesPage(Handler):
    def get(self):
        self.render("trees.html")

app = webapp2.WSGIApplication([('/drawings', DrawingsPage),
                               ('/trees', TreesPage)], debug=True)