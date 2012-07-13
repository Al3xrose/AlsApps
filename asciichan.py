#asciichan.py

import webapp2
import urllib2
from handler import Handler
from xml.dom import minidom

from google.appengine.ext import db
from google.appengine.api import memcache

IP_URL = "http://api.hostip.info/?ip="

def get_coords(ip):
    url = IP_URL + ip
    content = None

    try:
        content = urllib2.urlopen(url).read()
    except URLError:
        return

    if content:
        #parse the xml and find the coordinates
        d = minidom.parseString(content)
        coords = d.getElementsByTagName("gml:coordinates")
        if coords and coords[0].childNodes[0].nodeValue:
            lon, lat = coords[0].childNodes[0].nodeValue.split(',')
            return db.GeoPt(lat, lon)

GMAPS_URL = "http://maps.googleapis.com/maps/api/staticmap?size=380x263&sensor=false&"

def gmaps_img(points):
    markers = '&'.join('markers=%s,%s' % (p.lat, p.lon) for p in points)

    return GMAPS_URL + markers

class Art(db.Model):
    title = db.StringProperty(required=True)
    art = db.TextProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)
    coords = db.GeoPtProperty()


class AsciiChanPage(Handler):

    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("title")
        art = self.request.get("art")

        if title and art:
            a = Art(title=title, art=art)

            #Look up the users coordinates from IP
            coords = get_coords(self.request.remote_addr)

            if coords:
                a.coords = coords

            #if we have coordinates, add them to the art
            a.put()

            top_arts(update = True)
            
            self.redirect("/asciichan")
        else:
            error = "we need both a title and ASCII"
            self.render_front(error=error, art=art, title=title)

    def render_front(self, error="", art="", title=""):
        
        arts = self.top_arts()

        #find which arts have coords
        points = filter(None, (a.coords for a in arts))

        #if we have any arts coords, make an image url
        img_url = None
        
        if points:
            img_url = gmaps_img(points)

        self.render("asciichan.html", error=error, art=art, title=title, arts=arts, img_url = img_url)
        
    def top_arts(self, update = False):
        key = 'top'
        arts = memcache.get(key)
        if arts == None or update:
            arts = db.GqlQuery("select * from Art "
                           "order by created desc "
                           "limit 10")
            arts = list(arts)
            memcache.set(key, arts)
        
        return arts
        

app = webapp2.WSGIApplication([('/asciichan', AsciiChanPage)], debug=True)