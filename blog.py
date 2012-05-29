#blog.py

import os
import webapp2
import re
import random
import hashlib
import string
from handler import Handler

from google.appengine.ext import db

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")

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

class BlogPost(db.Model):
	title = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)

class MainPage(Handler):
    def get(self):
        blogposts = db.GqlQuery("select * from BlogPost "
                           "order by created desc")
        self.render("frontpage.html", blogposts = blogposts)

class NewPostPage(Handler):
    def get(self):
        self.render_front()

    def post(self):
        title = self.request.get("subject")
        content = self.request.get("content")

        if title and content:
            b = BlogPost(title=title, content=content)
            b.put()
            self.redirect("/blog/" + str(b.key().id()))
        else:
            error = "Enter a title and content"
            self.render_front(title=title, content=content, error=error)

    def render_front(self, title="", content="", error=""):
        self.render("newpost.html", title=title, content=content, error=error)

class BlogEntryPage(Handler):
    def get(self, blogpost_id):
        blogpost = BlogPost.get_by_id(int(blogpost_id))
        self.render('blogpost.html', blogpost = blogpost)

class SignupPage(Handler):
    def get(self):
        self.render('signup.html')

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
            and password == verify and self.valid_email(email) and not self.user_exists(username):

            pw_hash = make_pw_hash(username, password)
            u = User(username = username, pw_hash = pw_hash)
            u.put()

            cookie_val = 'user_id=%s|%s; Path=/' % (username, pw_hash)

            self.set_cookie(cookie_val)

            self.redirect('/blog/welcome')

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

    def user_exists(self, username):
        user_query = db.GqlQuery("select * from User where username = '%s'" % username)
        user = user_query.get()

        if user:
            return True
        else:
            return False

class WelcomePage(Handler):
    def get(self):
        user_id_cookie_str = self.request.cookies.get('user_id')

        if not user_id_cookie_str:
            self.redirect('/blog/signup')
        else:
            username = user_id_cookie_str.split('|')[0]
            #validate user_id cookie
            user_exists_query = db.GqlQuery("select * from User where username = '%s'" % username)
            user = user_exists_query.get()

            if user:
                self.render('welcome.html', username = username)
            else:
                self.redirect('/blog/signup')

class LoginPage(Handler):
    def get(self):
        self.render("login.html")

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
                self.redirect("/welcome")
            else:
                password_error = "Incorrect password"

        self.render("login.html", password_error = password_error, username_error = username_error)

    def valid_password(self, user, username, password):
        h = user.pw_hash

        return valid_pw(username, password, h)
        
class LogoutPage(Handler):
    def get(self):
        self.set_cookie('user_id=; Path=/')
        self.redirect("/blog/signup")

        


app = webapp2.WSGIApplication([('/blog', MainPage),
                               ('/blog/newpost', NewPostPage),
                               ('/blog/signup', SignupPage),
                               ('/blog/(\d+)', BlogEntryPage),
                               ('/blog/welcome', WelcomePage), 
                               ('/blog/login', LoginPage),
                               ('/blog/logout', LogoutPage)], debug=True)