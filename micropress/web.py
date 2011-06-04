"""
micropress.web

Support code for running micropress as a embedded web server. Not for
production! simply a way to rapidly prototype stuff.
"""

from cherrypy import wsgiserver
import cherrypy
from functools import partial
import os.path
from micropress import DEFAULT_PREVIEW_DIR
from micropress.util import mkdir

content_type = dict(html="text/html",
  css='text/css',
  jpg='image/jpeg',
  xml='text/xml',
  png='image/png',
  js="text/javascript",
  ico='image/vnd.microsoft.icon')    

def build(site,name):
#         print "BUILD %s%s" % (path,ext)
 site.refresh()
 for proc in site.processors:
   if proc.accept(name):
     proc.build(name,DEFAULT_PREVIEW_DIR)
     return
 (path,ext) = os.path.splitext(name)   
 if ext == '.html':
   p = site.page(path)
   if p:
     p.make(DEFAULT_PREVIEW_DIR)
   
def wsgifunc(site,environ, start_response):
    block_size = 4096
    name = environ['PATH_INFO'][1:]
    print "GET "+name
    if name == '' or name[-1] == '/':
      name += 'index.html'
    (p,ext) = os.path.splitext(name)
    build(site,name)
    path = os.path.join(DEFAULT_PREVIEW_DIR,name)
    if os.path.exists(path):
      status = '200 OK'
      # TODO: don't fail if we don't know content type!
      response_headers = [('Content-type',content_type[ext[1:]])]
      start_response(status, response_headers)
      file = open(path,'rb')
      # http://www.python.org/dev/peps/pep-0333/#optional-platform-specific-file-handling
      if 'wsgi.file_wrapper' in environ:
          return environ['wsgi.file_wrapper'](file, block_size)
      else:
          return iter(lambda: file.read(block_size), '')
    else:
      # What is there is notfound page?
      status = '404 Not Found'
      start_response(status, [])
      return ["Not Found"]
      
def load_hook(site,event):
  " invoked after site load"
  site.domain = "http://localhost:8080"
  site.root = "/"
  site.preview_mode = True
  
def run(site):
  "launches a web server for site. uses web.py"
  # TODO: host and port in signature - pass to load hook!
#    http://www.cherrypy.org/wiki/WSGI
  site.dynamic = True
  site.hooks.append(load_hook)
  mkdir(DEFAULT_PREVIEW_DIR)
  # TODO: we want to set the domain/root properties and 
  # have them be retained across config changes!
  print "Starting web server at localhost:8080"
  server = wsgiserver.CherryPyWSGIServer(
              ('0.0.0.0', 8080), partial(wsgifunc,site),
              server_name='micropress.web')
  try:
   server.start()
  except KeyboardInterrupt:
   server.stop()
   