#!/usr/bin/env python
# encoding: utf-8
"""
micropress.py

micropress is an extremely simple tool for generating [[static]] websites. It is, by design, limited in scope. It chooses a core set of technologies and best-practices and does them and no more. If you want something entirely different - look somewhere else. 

Why static? Static HTML sites are cheap and efficient. You can push them onto S3 or do whatever you like. 

site/
- config.yaml
- pages/
- templates/
- js/
- css/
- resources/
- hooks/

and then generates
- tmp/
- build/

config.yaml defines the general config option and allows you to define global template variables

pages/ contains html or markdown files which are subsitatied into templates. Markdown files look like this:

title:
tags:
template:
meta1:
meta2:

content

templates/ cheetah templates i guess or django
js/ directory may be coffeescript or javascript - optimizied on deploy
css/ may be regular css or any of the css processors
resources/ is copied directly into site folder
hooks are simply scripts called at various times 

micropress clean
micropress run # runs site in embedded web server
micropress publish
micropress deploy

tempaltes - need a way to pull image and get dimensions!

extras
- google sitemap generation
- rich snippets
- shortcodes 
- flicks
- microformats
- mobile generation

web.py
- cherry.py used internall 3.1.2
- 

TODO: incremental updates needed - avoid sync to ftp
TODO: had a problem where absolute site paths fail/hard to configure
TODO: way to override site properties at invokation (site docroot)
TODO: publish to alternate output dir for FTP 
TODO: site.site_opts is bad name for config for template purposes

Created by Joel Carranza on 2011-04-09.
Copyright (c) 2011 Joel Carranza. All rights reserved.
"""

import markdown
# http://jinja.pocoo.org/docs/#
from jinja2 import Template,Environment,FileSystemLoader
import yaml
import os
import codecs
import os.path
import shutil
import subprocess
import sys
import re
from datetime import datetime

# constants
SITE_CONFIG_PATH = 'site.yaml'
TEMPLATE_DIR = 'templates'
PAGE_DIR = 'pages'
RESOURCES_DIR = 'resources'
OUTPUT_DIR = 'site'
PAGES_DIR = 'pages'

# logging
debugLevel = 0

def info(msg):
  """docstring for info"""
  if debugLevel >= 0:
    print msg

def debug(msg):
  """docstring for debug"""
  if debugLevel >= 1:
    print msg

def trace(msg):
  """docstring for trace"""
  if debugLevel >= 2:
    print msg

class Processor():
  """docstring for Processor"""
  def __init__(self,indir,ext=None):
    self.indir = indir
    self.ext = ext
    
  def resources(self):
    """enumeration of all resources that this processor publishes"""
    # TODO: implement a common list of exclusions
    for root, dirs, files in os.walk(self.indir):
      # do not walk directories with dot prefix
      dirs[:] = [d for d in dirs if d[0] != '.']
      for f in files:
        # path contains prefix of dir - strip prefix
        if self.ext:
          (name,ext) = os.path.splitext(f)
          if ext != self.ext:
            continue
        yield self.resource_from_path(os.path.join(root,f))
  
  def resource_from_path(self,path):
    """converts this internal source path into an output resource"""
    return path
    
  def path_from_resource(self,rsc):
    """converts this resource into the source path"""
    return rsc
    
  def accept(self,rsc):
    """determine if the processor can handle this resource"""
    # TODO this could be done better
    return rsc in self.resources()
    
  def _dobuild(self,src,dest):
    "build if needed"
    shutil.copyfile(src,dest)
    
  def build(self,rsc,outdir):
    """create the target resource in the output directory"""
    dest = os.path.join(outdir,rsc)
    dirname = os.path.dirname(dest)
    if not os.path.exists(dirname):
      os.mkdir(dirname)
    src = self.path_from_resource(rsc)
    if not isuptodate(dest,src):
      # root include resources - needs to
      print "copying to %s " % dest
      self._dobuild(src,dest)
    else:
      print "skipping %s" %dest
    
  def make(self,outdir):
    for rsc in self.resources():
      self.build(rsc,outdir)
      
class StaticResourcesProcessor(Processor):
  
  def resource_from_path(self,path):
    # strip leading directory prefix
    n = len(self.indir)+1
    return path[n:]
    
  def path_from_resource(self,rsc):
    return os.path.join(self.indir,rsc)

class Site():
  """
  A single site object is created for the entire site. You can use
  methods on site to extract global information (see querypages)
  """
  
  def __init__(self,path):
    self.util = {}
    self.pages = {}
    self.path = path
    self.markdown_opts = {}
    # TODO: site_opts is a terrible name
    self.site_opts = {}
    self.dynamic = False
    self.load()
    self.loadpages()
    self.processors = [
      StaticResourcesProcessor("resources"),
      Processor("css",".css"),
      Processor("js",".js")      
    ]
    self.load_extension('coffeescript')
    self.load_extension('less')
    self.load_extension('picassa')
    self.load_extension('datasource_json')
    # extension should be able to add to templates too!
    self.env = Environment(loader=FileSystemLoader(os.getcwd()+'/templates'))
    
  def load_extension(self,name):
    ext = __import__(name)
    ext.extend_micropress(self)
  
  def load_template(self,name):
    return self.env.get_template(name+".tmpl")

  def render_markdown(self,text):
    """Render markdown text into HTML/XHTML"""
    return self.markdown.convert(text)
  
  # TODO def sitemap(self,file)
  # http://diveintohtml5.org/offline.html
  # TODO def manifest(self,file)

  def load(self):
    """Load options from config file"""
    siteconfig = yaml.load(open(self.path))
    if 'markdown' in siteconfig:
      markdown_opts = siteconfig['markdown']
    else:
      markdown_opts = {}
    if 'site' in siteconfig:
      self.site_opts = siteconfig['site']
    self.encoding = siteconfig.get('encoding','utf8')
    self.loadts = os.path.getmtime(self.path)
    self.page_decorators = []
    self.markdown = markdown.Markdown(**markdown_opts)
  
  def loadpages(self):
    """Scan pages directory for new pages"""
    newpages = {}
    for page in listfiles(PAGES_DIR):
       (path,ext) = os.path.splitext(page)
       if ext == '.markdown' or ext == '.html':
         path = os.path.join(PAGES_DIR,page)
         (rest,ext) = os.path.splitext(page)
         # reuse existing pages where we can
         if rest in self.pages:
           newpages[rest] = self.pages[rest]
         else:
           p = Page(self,path)
           for decorators in self.page_decorators:
            decorators.extend_page()
           newpages[rest] = p
    self.pages = newpages
  
  def page(self,path):
    p = self.pages.get(path)
    if p and self.dynamic:
      p.refresh()
    return p
    
  # this is inspired by the wordpress loop!
  # http://codex.wordpress.org/Template_Tags/get_posts
  def querypages(self,tag=None,category=None,maxitems=None,order=None):
    if self.dynamic:
      for p in self.pages.values():
        p.refresh()
    
    pages = []
    for p in self.pages.values():
      if tag is not None and tag not in p.tags:
        continue
      if category is not None and category != p.category:
        continue  
      pages.append(p)
    if order:
      if order == 'date_created':
        pages.sort(key=lambda p:p.date_created())
        pages.reverse()
      elif order == 'date_modified':
        pages.sort(key=lambda p:p.date_modified())
        pages.reverse()
      elif order == 'title':
        pages.sort(key=lambda p:p.title)
    
    if maxitems is not None:
      pages = pages[0:maxitems]
    return pages
  
  def refresh(self):
    """Reload configuration if needed"""
    if os.path.getmtime(self.path) != self.loadts:
      self.load()
    self.loadpages()
  
  def brew(self):
    # create output dir if it doesn't exist
    mkdir(OUTPUT_DIR)

    for p in self.processors:
      p.make(OUTPUT_DIR)

    # make pages
    for p in site.querypages():
      p.make()
      
  def clean(self):
    # TODO: remove output dir
    pass

  def wsgifunc(self):
    site = self
    site.dynamic = True
    
    def build(name):
#         print "BUILD %s%s" % (path,ext)
     site.refresh()
     for proc in self.processors:
       if proc.accept(name):
         proc.build(name,OUTPUT_DIR)
         return
     (path,ext) = os.path.splitext(name)   
     if ext == '.html':
       p = site.page(path)
       if p:
         p.make()
       
    def simple_app(environ, start_response):
        block_size = 4096
        content_type = dict(html="text/html",css='text/css',jpg='image/jpeg',png='image/png',js="text/javascript",ico='image/vnd.microsoft.icon')     
        name = environ['PATH_INFO'][1:]
        print "GET "+name
        if name == '' or name[-1] == '/':
          name += 'index.html'
        (p,ext) = os.path.splitext(name)
        build(name)
        path = os.path.join(OUTPUT_DIR,name)
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
          status = '404 Not Found'
          start_response(status, response_headers)
          return ["Not Found"]
                    
    return simple_app
  
  def run(self):
    "launches a web server for site. uses web.py"
    
#    http://www.cherrypy.org/wiki/WSGI
    from cherrypy import wsgiserver
    import cherrypy
    
    server = wsgiserver.CherryPyWSGIServer(
                ('0.0.0.0', 8080), self.wsgifunc(),
                server_name='www.cherrypy.example')
    try:
     server.start()
    except KeyboardInterrupt:
     server.stop()

class Page():
  """
  A page is created for each markdown/html file in your pages/ 
  directory
  """
  # TODO: excerpt
  
  def __init__(self,site,path):
    self.site = site
    self.path = path
    self.load()
  
  def load(self):
    """instatiate"""
    f = codecs.open(self.path, mode="r",encoding=self.site.encoding)
    line = f.readline().rstrip()
    header = {}
    while line:
      # support line comments via '#'
     ix = line.find('#')
     if ix != -1:
       line = line[0:ix]
       if not line:
         # empty line - next!
         line = f.readline().rstrip()
         continue
     (key,value) = re.split(r':\s*',line,1)
     # convert foo-bar to foo_bar
     header[key] = value
     line = f.readline().rstrip()
    lines = []
    line = 'X'
    while line:
     line = f.readline()
     lines.append(line)
    body = "".join(lines)
    (rest,ext) = os.path.splitext(self.path)
    self.type = ext[1:]
    # strip page!
    self.name = self.path[6:].split('.')[0]
    self.meta = header
    self.title = header.get('title',self.name)
    self.tags = re.split(r'\s*,\s*',header['tags']) if 'tags' in header else []
    self.category = header.get('category')
    self.body = body
    self.loadts = os.path.getmtime(self.path)
  
  def href(self,base):
    # TODO: base not implemented correctly!
    return self.name+'.html'
  
  def date_created(self,fmt=None):
    if 'date_created' in self.meta:
      dt = datetime.strptime(self.meta['date_created'],'%m/%d/%Y')
    else:
      dt = datetime.fromtimestamp(os.path.getctime(self.path))
    if fmt:
      return dt.strftime(fmt)
    else:
      return dt
  
  def date_modified(self,fmt=None):
    dt = datetime.fromtimestamp(os.path.getmtime(self.path))
    if fmt:
      return dt.strftime(fmt)
    else:
      return dt
    
  
  def get_target_path(self):
    return 'site/'+self.name+'.html'
    
  def html(self):
    if self.type == 'html':
      return self.body
    else:
      return self.site.render_markdown(self.body)
    
  def refresh(self):
    """Reload configuration if needed"""
    if os.path.getmtime(self.path) != self.loadts:
      self.load()
  
  def render(self):
    templateName = self.meta.get('template','default')
    template = site.load_template(templateName)
    return template.render(
      content=self.html(),
      template=templateName,
      meta=self.meta,
      page=self,
      site=self.site)
      
  def make(self):
    info("Rendering "+self.get_target_path())
    mkdir(os.path.dirname(self.get_target_path()))
    out = codecs.open(self.get_target_path(),'w',encoding=site.encoding)
    try:
      out.write(self.render())
    finally:
      out.close()
  
# UTILS  

def listfiles(dir):
  "List all files (recursively) under directory"
  # TODO: implement a common list of exclusions
  for root, dirs, files in os.walk(dir):
    # do not walk directories with dot prefix
    dirs[:] = [d for d in dirs if d[0] != '.']
    for f in files:
      # path contains prefix of dir - strip prefix
      path = os.path.join(root,f)[len(dir)+1:]
      yield path

def isuptodate(dest,*sources):
 if not os.path.exists(dest):
   return False
 for src in sources:
   if os.path.getmtime(src) > os.path.getmtime(dest):
     return False
 return True


def mkdir(dir):
 if not os.path.exists(dir):
   os.mkdir(dir)

# Good resource on subprocess
# http://www.doughellmann.com/PyMOTW/subprocess/index.html

def exectool(cmd,*args):
   """Run a program - check for valid return"""
   proc = subprocess.Popen((cmd,)+args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   output = proc.communicate()[0]
   # print output if we have anything
   if output:
     print cmd+": "+output
   # raise error if failed!
   if proc.returncode != 0:
     raise Exception("%s returned err code %i" % (cmd,proc.returncode))

# TASKS

if __name__ == '__main__':
  if len(sys.argv) <= 1:
    cmd = 'brew' 
  else:
    cmd = sys.argv[1]
  site = Site(SITE_CONFIG_PATH)
  if cmd == 'brew':
    site.brew()
  elif cmd == 'run':
    # web.py -  If called from the command line, it will start an HTTP server 
    # on the port named in the first command line argument, or, if there is no
    # argument, on port 8080.
    sys.argv = sys.argv[2:]
    site.run()
  elif cmd == 'clean':
    site.clean()
  else:
    raise Exception("Invalid command %s"  % cmd)