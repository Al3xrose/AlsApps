#requesthandlers.py

import webapp2
import jinja2
import os

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

    def set_cookie(self, cookie_str):
        self.response.headers.add_header(str('Set-Cookie'), str(cookie_str))
        
    def write_html(self, *a, **kw):
        self.response.headers['Content-Type'] = 'text/html'
        self.response.out.write(*a, **kw)