#blog.py

import os
import webapp2
import re
import random
import hashlib
import string
import time
from handler import Handler
import json

from google.appengine.ext import db
from google.appengine.api import memcache

USER_RE = re.compile(r"^[a-zA-Z0-9_-]{3,20}$")
PASS_RE = re.compile("^.{3,20}$")
EMAIL_RE = re.compile("^[\S]+@[\S]+\.[\S]+$")
#LAST_QUERIED_TIME = time.time()

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
    
def recent_posts(update = False):
    key = 'top'
    posts = memcache.get(key)
    if not posts or update:
        posts = db.GqlQuery("SELECT * "
                            "FROM BlogPost "
                            "ORDER BY created DESC "
                            "LIMIT 10")
                            
        posts = list(posts)
        memcache.set(key, posts)
        memcache.set('time', time.time())
        #global LAST_QUERIED_TIME
        #LAST_QUERIED_TIME = time.time()
        
    return posts
        
def get_post(blogpost_id):
    key = str(blogpost_id)
    post = memcache.get(key)
    
    if not post:
        post = BlogPost.get_by_id(blogpost_id)
        memcache.set(key, post)
        memcache.set(key + 'time', time.time())
    
    return post
        

class BlogPost(db.Model):
	subject = db.StringProperty(required=True)
	content = db.TextProperty(required=True)
	created = db.DateTimeProperty(auto_now_add = True)

class User(db.Model):
    username = db.StringProperty(required=True)
    pw_hash = db.StringProperty(required=True)

class MainPage(Handler):
    def get(self):
        blogposts = recent_posts()
        last_query_time = memcache.get('time')
        if last_query_time:
            seconds = time.time() - float(last_query_time)
        else:
            seconds = 0
        seconds = '%.2f' % seconds
        self.render("blog.html", blogposts = blogposts, seconds = seconds)
        self.write_html("<b>LOL</b>")

class NewPostPage(Handler):
    def get(self):
        self.render_front()

    def post(self):
        subject = self.request.get("subject")
        content = self.request.get("content")

        if subject and content:
            b = BlogPost(subject=subject, content=content)
            b.put()
            recent_posts(update = True)
            self.redirect("/blog/" + str(b.key().id()))
        else:
            error = "Enter a subject and content"
            self.render_front(subject=subject, content=content, error=error)

    def render_front(self, subject="", content="", error=""):
        self.render("newpost.html", subject=subject, content=content, error=error)

class BlogEntryPage(Handler):
    def get(self, blogpost_id):
        blogpost = get_post(int(blogpost_id))
        last_queried_time = memcache.get(blogpost_id + 'time')
        
        if last_queried_time:
            seconds = time.time() - last_queried_time
        else:
            seconds = 0
            
        seconds = "%.2f" % seconds
        
        self.render('blogpost.html', blogpost = blogpost, seconds = seconds)

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

class JsonMainPage(Handler):
    def get(self):
        blogposts = db.GqlQuery("select * from BlogPost "
                        "order by created desc")

        self.response.out.headers['Content-Type'] = 'application/json'

        json_list = []

        for blogpost in blogposts:
            json_list.append({'subject' : blogpost.subject, 'content' : blogpost.content})

        self.write(json.dumps(json_list))

class JsonEntryPage(Handler):
    def get(self, blogpost_id):

        blogpost = BlogPost.get_by_id(int(blogpost_id))

        self.response.out.headers['Content-Type'] = 'application/json'

        blogpost_json = {'subject': blogpost.subject, 'content': blogpost.content}

        self.write(json.dumps(blogpost_json))
        
class FlushPage(Handler):
    def get(self):
        memcache.flush_all()
        self.redirect('/blog')



app = webapp2.WSGIApplication([('/blog', MainPage),
                               ('/blog/.json', JsonMainPage),
                               ('/blog/newpost', NewPostPage),
                               ('/blog/signup', SignupPage),
                               ('/blog/(\d+)', BlogEntryPage),
                               ('/blog/(\d+).json', JsonEntryPage),
                               ('/blog/welcome', WelcomePage), 
                               ('/blog/login', LoginPage),
                               ('/blog/logout', LogoutPage),
                               ('/blog/flush', FlushPage)], debug=True)