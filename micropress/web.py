from cherrypy import wsgiserver
import cherrypy

def run(site):
  "launches a web server for site. uses web.py"
  
#    http://www.cherrypy.org/wiki/WSGI
  
  server = wsgiserver.CherryPyWSGIServer(
              ('0.0.0.0', 8080), site.wsgifunc(),
              server_name='www.cherrypy.example')
  try:
   server.start()
  except KeyboardInterrupt:
   server.stop()
   