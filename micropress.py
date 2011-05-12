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

# Provides ways to pull in external data
class DataSource():
  # TODO: xml
  # each data "flavor" should support either http or path relative to site
  # root
  # also caching for non-interactive sites
  def feed(self,url):
    """load an rss feed"""
    import feedparser
    return feedparser.parse(url)
  
  def json(self,url):
    """load url from JSON"""
    if url.startswith("http:"):
      import urllib2
      response = urllib2.urlopen(url)
      import json
      return json.load(response)
    else:
      return json.load(open(url,'r'))
  
  def yaml(self,url):
    """load url from YAML"""
    if url.startswith("http:"):
      import urllib2
      response = urllib2.urlopen(url)
      return yaml.load(response)
    else:
      return yaml.load(open(url,'r'))

datasource = DataSource()

class Site():
  """
  A single site object is created for the entire site. You can use
  methods on site to extract global information (see querypages)
  """
  
  def __init__(self,path):
    self.pages = {}
    self.path = path
    self.load()
    self.loadpages()
    self.markdown_opts = {}
    self.site_opts = {}
    self.dynamic = False
    self.env = Environment(loader=FileSystemLoader(os.getcwd()+'/templates'))
  
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
           newpages[rest] = Page(self,path)
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
      elif order == 'date_modified':
        pages.sort(key=lambda p:p.date_modified())
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

    # copy everything from resources
    if os.path.exists(RESOURCES_DIR):
      for f in listfiles(RESOURCES_DIR):
        dest = os.path.join(OUTPUT_DIR,f)
        dirname = os.path.dirname(dest)
        if not os.path.exists(dirname):
          os.mkdir(dirname)
        # root include resources - needs to 
        shutil.copyfile(os.path.join(RESOURCES_DIR,f),dest)

    # make javascript
    make("js",".js",{".js":copyfile,".coffee":coffee})
    # make css
    # TODO: support SASS
    make("css",".css",{".css":copyfile,".less":less})

    # make pages
    for p in site.querypages():
      p.make()
      
  def clean(self):
    # TODO: remove output dir
    pass

  def run(self):
    "launches a web server for site. uses web.py"
    # web.py - http://webpy.org/
    import web
    site = self
    site.dynamic = True
    class webapp:   
      # TODO: no camelcase
       content_type = dict(html="text/html",css='text/css',jpg='image/jpeg',png='image/png',js="text/javascript")     

       def build(self,path,ext):
         site.refresh()
         if ext == '.html':
           p = site.page(path)
           p.make()
         elif ext == '.js' and path.startswith("js/"):
           trymake("js",path[3:],".js",{".js":copyfile,".coffee":coffee})
         elif ext == '.css' and path.startswith("css/"):
           trymake("css",path[4:],".css",{".css":copyfile,".less":less})
         # XXX: resources/ dir ignored!

       def GET(self, name):
         if name == '' or name[-1] == '/':
           name += 'index.html'
         print "GET "+name
         (p,ext) = os.path.splitext(name)
         self.build(p,ext)
         # now just look in output!
         path = os.path.join(OUTPUT_DIR,name)
         if os.path.exists(path):
           # TODO: set content type
           web.header('Content-Type', self.content_type[ext[1:]])
           f = open(path,'rb')
           # 408 request timeout
           # http://groups.google.com/group/webpy/tree/browse_frm/month/2009-10?_done=%2Fgroup%2Fwebpy%2Fbrowse_frm%2Fmonth%2F2009-10%3Ffwc%3D1%26&fwc=1
           # key is to use 'rb'
           try:
            return f.read()
           finally:
             f.close()
         else:
           web.notfound()

    urls = (
        '/(.*)', 'webapp'
    )
    app = web.application(urls, dict(webapp=webapp))
    web.webapi.internalerror = web.debugerror
    app.run()

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
      datasource=datasource,
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

def trymake(dir,name,targetext,rules):
  for (ext,rule) in rules.items():
    src = os.path.join(dir,name+ext)
    if os.path.exists(src):
      dest = os.path.join(OUTPUT_DIR,dir+"/"+name+targetext)
      debug("trymake src=%s dest=%s" % (src,dest))
      rule(src,dest)

def make(dir,targetext,rules):
  if os.path.exists(dir):
     for f in listfiles(dir):
       (name,ext) = os.path.splitext(f)
       if ext in rules:
         rule = rules[ext]
         dest = os.path.join(OUTPUT_DIR,os.path.join(dir,name+targetext))
         src = os.path.join(dir,f)
         mkdir(os.path.dirname(dest))
         rule(src,dest)
       else:
         debug("Ignoring: "+f)

def isuptodate(dest,*sources):
 if not os.path.exists(dest):
   return False
 for src in sources:
   if os.path.getmtime(src) > os.path.getmtime(dest):
     return False
 return True

# RULES

def coffee(src,dest):
 outdir = os.path.dirname(dest)
 exectool('coffee','-c','-o',outdir,src);

# just use shutil
copyfile = shutil.copyfile

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

def less(src,dest):
 exectool('lessc',src,dest)

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