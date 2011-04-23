#!/usr/bin/env python
# encoding: utf-8
"""
micropress.py

micropress is a extremely simple tool for generating [[static]] websites. It is not extremely flexibile, it picks a core set of technologies and best-practices and does them and no more. If you want something entirely different - look somewhere else. Static HTML sites are cheap and efficient. You can push them onto S3 or do whatever you like. 

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

# constants
SITE_CONFIG_PATH = 'site.yaml'
TEMPLATE_DIR = 'templates'
PAGE_DIR = 'pages'
RESOURCES_DIR = 'resources'
OUTPUT_DIR = 'site'
PAGES_DIR = 'pages'

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
    self.env = Environment(loader=PackageLoader('micropress', 'templates'))
  
  def loadTemplate(self,name):
    return self.env.get_template(name+".tmpl")
  
  def renderMarkdown(self,body):
    """docstring for renderMarkdown"""
    return markdown.markdown(body,self.markdown_opts)
  
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
    """pages"""
    # TODO: remove pages?
    for page in listfiles(PAGES_DIR):
       (path,ext) = os.path.splitext(page)
       if ext == '.markdown' or ext == '.html':
         path = os.path.join(PAGES_DIR,page)
         (rest,ext) = os.path.splitext(page)
         if rest not in self.pages:
           self.pages[rest] = Page(self,path)
  
  def page(self,path):
    return self.pages.get(path)
    
  def querypages(self):
    return self.pages.values()
  
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
      print "Rendering "+p.getTargetPath()
      out = codecs.open(p.getTargetPath(),'w',encoding=site.encoding)
      out.write(p.render())
      
  def clean(self):
    # TODO: remove output dir
    pass

  def run(self):
    "launches a web server for site. uses web.py"
    # web.py - http://webpy.org/
    import web
    site = self
    class webapp:   
       contentType = dict(html="text/html",css='text/css',jpg='image/jpeg',png='image/png',js="text/javascript")     

       def build(self,path,ext):
         site.refresh()
         if ext == '.html':
           print "Build: %s" % path
           p = site.page(path)
           p.refresh()
           out = codecs.open(p.getTargetPath(),'w',encoding=site.encoding)
           out.write(p.render())
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
     (key,value) = line.split(':',2)
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
      print "trymake src=%s dest=%s" % (src,dest)
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
         print "Ignoring: "+f

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
 subprocess.Popen(['coffee','-c','-o',outdir,src],stderr=subprocess.PIPE,stdout=subprocess.PIPE)

# just use shutil
copyfile = shutil.copyfile

def mkdir(dir):
 if not os.path.exists(dir):
   os.mkdir(dir)

def less(src,dest):
  subprocess.Popen(['less',src],stdout=open(dest,'w'),stderr=subprocess.PIPE)

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