import os
import webapp2
import re
import string
import time
import hashlib
import random
from handler import Handler

from google.appengine.ext import db
from google.appengine.api import memcache

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")

class User(db.Model):
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)
    
class WikiPage(db.Model):
    name = db.StringProperty(required=True)
    content = db.StringProperty(required=True)
    created = db.DateTimeProperty(auto_now_add = True)

def user_exists(username):
    user_query = db.GqlQuery("select * from User where username = '%s'" % username)
    user = user_query.get()

    if user:
        return True
    else:
        return False
            
#def validate_user(username, pw_hash)
#    logged_in = memcache.get('%s,%s' % (username, pw_hash))
    
#    if not logged_in

def logged_in(user_id_cookie_str):
    
    if user_id_cookie_str:
        return True
    else:
        return False

        
def get_content(wikipage_id):
    wikipage = memcache.get(wikipage_id)
    
    if not wikipage:
        wikipage = db.GqlQuery("select * from WikiPage where name = '%s'" % wikipage_id)
        wikipage = wikipage.get()
        memcache.set(wikipage_id, wikipage)
    
    return wikipage
    
    
def make_salt():
    return ''.join(random.choice(string.letters) for x in xrange(5))

def make_pw_hash(name, pw, salt = None):
    if not salt:
        salt = make_salt()

    h = hashlib.sha256(name + pw + salt).hexdigest()
    return '%s,%s' % (h, salt)

def valid_pw(name, pw, h):
    salt = h.split(',')[1]
    return h == make_pw_hash(name, pw, salt)

class MainPage(Handler):
    def get(self):
        user_id_cookie_str = self.request.cookies.get('user_id')
        
        self.render("/wiki/mainpage.html")
        
class Signup(Handler):
    def get(self):
        self.render('/wiki/signup.html')

    def post(self):
        
        username = self.request.get("username")
        password = self.request.get("password")
        verify = self.request.get("verify")
        email = self.request.get("email")
        username_error = ""
        password_error = ""
        verify_error = ""
        email_error = ""
        
        #validate input
        if self.valid_username(username) and self.valid_password(password) \
            and password == verify and self.valid_email(email) and not user_exists(username):

            pw_hash = make_pw_hash(username, password)
            u = User(username = username, pw_hash = pw_hash)
            u.put()

            cookie_val = 'user_id=%s|%s; Path=/' % (username, pw_hash)

            self.set_cookie(cookie_val)

            self.redirect('/wiki')

        else:
            if not self.valid_username(username):
                username_error = "Enter a valid username"
            elif self.user_exists(username):
                username_error = "Username already exists"
        
            if not self.valid_password(password):
                password_error = "Enter a valid password"
        
            if not password == verify:
                verify_error = "Passwords don't match"
                
            if not self.valid_email(email):
                email_error = "Enter a valid email"
        
            self.render('signup.html', username = username, email = email, \
                username_error = username_error, password_error = password_error, \
                verify_error = verify_error, email_error = email_error)
        
    def valid_username(self, username):
        return USER_RE.match(username)
        
    def valid_password(self, password):
        return PASS_RE.match(password)
        
    def valid_email(self, email):
        if email == '':
            return True
        else:
            return EMAIL_RE.match(email)

class Login(Handler):
    def get(self):
        self.render("/wiki/login.html")

    def post(self):
        username = self.request.get('username')
        password = self.request.get('password')

        username_error = ""
        password_error = ""

        user_query = db.GqlQuery("select * from User where username = '%s'" % username)
        user = user_query.get()

        if not user:
            username_error = "User doesn't exist!"
        else:
            if self.valid_password(user, username, password):
                cookie_str = "user_id=%s|%s; Path=/" %(user.username, user.pw_hash)
                self.set_cookie(cookie_str)
                self.redirect("/wiki")
            else:
                password_error = "Incorrect password"

        self.render("/wiki/login.html", password_error = password_error, username_error = username_error)

    def valid_password(self, user, username, password):
        h = user.pw_hash

        return valid_pw(username, password, h)
        
class Logout(Handler):
    def get(self):
        self.set_cookie('user_id=; Path=/')
        self.redirect("/wiki")
        
class WikiEntryPage(Handler):
    def get(self, wikipage_id):
        user_id_cookie_str = self.request.cookies.get('user_id')
        
        #if logged_in(user_id_cookie_str)
        
        wikipage_content = get_content(wikipage_id)
        
        if wikipage_content:
            self.render("/wiki/wikipage.html")
            self.write_html(wikipage_content)
        elif not wikipage_content and logged_in(user_id_cookie_str):
            self.redirect("/wiki/_edit/%s" % wikipage_id)
        else:
            self.redirect("/wiki/signup")
        
class EditPage(Handler):
    def get(self, wikipage_id):
        wikipage_content = get_content(wikipage_id)
        
        if not wikipage_content:
            wikipage_content = ""
        
        self.render("/wiki/editpage.html", edit = wikipage_content)
        
    def post(self, wikipage_id):
        content = self.request.get('content')
        
        p = WikiPage(name = wikipage_id, content = content)
        p.put()
        memcache.set(wikipage_id, content)
        self.redirect('/wiki/%s' % wikipage_id)
        

PAGE_RE = r'((?:[a-zA-Z0-9_-]+/?)*)'
app = webapp2.WSGIApplication([('/wiki', MainPage),
                               ('/wiki/signup', Signup),
                               ('/wiki/login', Login),
                               ('/wiki/logout', Logout),
                               ('/wiki/_edit/' + PAGE_RE, EditPage),
                               ('/wiki/' + PAGE_RE, WikiEntryPage)], debug=True)