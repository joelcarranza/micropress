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
from jinja2 import Template,Environment,PackageLoader
import yaml
import os
import codecs
import os.path
import shutil
import subprocess
import sys
import re

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
    self.env = Environment(loader=PackageLoader('micropress', 'templates'))
  
  def loadTemplate(self,name):
    return self.env.get_template(name+".tmpl")
  
  def renderMarkdown(self,text):
    """Render markdown text into HTML/XHTML"""
    return markdown.markdown(text,self.markdown_opts)
  
  def load(self):
    """Load options from config file"""
    siteconfig = yaml.load(open(self.path))
    if 'markdown' in siteconfig:
      self.markdown_opts = siteconfig['markdown']
    if 'site' in siteconfig:
      self.site_opts = siteconfig['site']
    self.encoding = siteconfig.get('encoding','utf8')
    self.loadts = os.path.getmtime(self.path)
    
  
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
    
  def querypages(self):
    pages = self.pages.values()
    if self.dynamic:
      for p in pages:
        p.refresh()
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
       contentType = dict(html="text/html",css='text/css',jpg='image/jpeg',png='image/png',js="text/javascript")     

       def build(self,path,ext):
         site.refresh()
         if ext == '.html':
           p = site.page(path)
           p.make()
         elif ext == '.js' and path.startswith("js/"):
           trymake("js",path[3:],".js",{".js":copyfile,".coffee":coffee})
         elif ext == '.css' and path.startswith("css/"):
           trymake("css",path[4:],".css",{".css":copyfile,".less":less})

       def GET(self, name):
         if name == '' or name[-1] == '/':
           name += 'index.html'
         (p,ext) = os.path.splitext(name)
         self.build(p,ext)
         # now just look in output!
         path = os.path.join(OUTPUT_DIR,name)
         if os.path.exists(path):
           # TODO: set content type
           web.header('Content-Type', self.contentType[ext[1:]])
           f = open(path,'r')
           return f.read()
         else:
           web.notfound()

    urls = (
        '/(.*)', 'webapp'
    )
    app = web.application(urls, dict(webapp=webapp))
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
     (key,value) = re.split(r':\s*',line,2)
     header[key] = value
     line = f.readline().rstrip()
    # XXX: not reading whole thing?
    # f.read() will not work see http://bugs.python.org/issue8260
    lines = []
    line = 'X'
    while line:
     line = f.readline()
     lines.append(line)
    body = "".join(lines)
    (rest,ext) = os.path.splitext(self.path)
    self.type = ext[1:]
    self.name = os.path.basename(self.path).split('.')[0]
    self.meta = header
    self.title = header.get('title',self.name)
    self.body = body
    self.loadts = os.path.getmtime(self.path)
  
  def getCategory(self):
    return self.meta.get('category')
  
  def getTags(self):
    return self.meta.get('tags')
  
  def getSrcPath(self):
    return 'pages/'+self.name+'.markdown'
  
  def getTemplatePath(self):
    # TODO: parameterize via template!
    return 'templates/default.tmpl'
  
  def getTargetPath(self):
    return 'site/'+self.name+'.html'
    
  def html(self):
    if self.type == 'html':
      return self.body
    else:
      return self.site.renderMarkdown(self.body)
    
  def href(self,page):
    # TODO!
    return page.name+".html"
  
  def refresh(self):
    """Reload configuration if needed"""
    if os.path.getmtime(self.path) != self.loadts:
      self.load()
  
  def render(self):
    template = site.loadTemplate(self.meta.get('template','default'))
    return template.render(
      content=self.html(),
      page=self,
      site=self.site)
      
  def make(self):
    info("Rendering "+self.getTargetPath())
    out = codecs.open(self.getTargetPath(),'w',encoding=site.encoding)
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