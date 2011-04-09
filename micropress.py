#!/usr/bin/env python
# encoding: utf-8
"""
micropress.py

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

# constants
SITE_CONFIG_PATH = 'site.yaml'
TEMPLATE_DIR = 'templates'
PAGE_DIR = 'pages'
OUTPUT_DIR = 'site'

# globals
markdown_opts = {}
site = None
env = Environment(loader=PackageLoader('micropress', 'templates'))

class Site():
  """
  A single site object is created for the entire site. You can use
  methods on site to extract global information (see querypages)
  """
  
  def __init__(self,opt):
    self.pages = []
    self.encoding = opt.get('encoding','utf8')
    
  def addPage(self,page):
    self.pages.append(page)
    
  def querypages(self):
    return self.pages

class Page():
  """
  A page is created for each markdown/html file in your pages/ 
  directory
  """
  # TODO: excerpt
  
  def __init__(self,path,meta,body):
    self.path = path
    self.name = os.path.basename(path).split('.')[0]
    self.meta = meta
    self.title = self.meta.get('title',self.name)
    self.body = body
  
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
    return markdown.markdown(self.body,**markdown_opts)
    
  def href(self,page):
    # TODO!
    return page.name+".html"

def loadTemplate(name):
  return env.get_template(name+".tmpl")
  
def loadPage(page):
  f = codecs.open(page, mode="r",encoding=site.encoding)
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
  return Page(page,header,body)

def renderPage(page):
  template = loadTemplate(page.meta.get('template','default'))
  return template.render(
    content=page.html(),
    page=page,
    site=site)

def isuptodate(dest,*sources):
  if not os.path.exists(dest):
    return False
  for src in sources:
    if os.path.getmtime(src) > os.path.getmtime(dest):
      return False
  return True

def clean():
  # TODO: remove output dir
  pass

def brew():
  global markdown_opts
  global site_opts
  global site
  
  # configure()
  siteconfig = yaml.load(open(SITE_CONFIG_PATH))
  if 'markdown' in siteconfig:
    markdown_opts = siteconfig['markdown']
  if 'site' in siteconfig:
    site_opts = siteconfig['site']
  site = Site(siteconfig)
  
  for page in os.listdir('pages'):
    p = loadPage('pages/'+page)
    site.addPage(p)
  
  # create output dir if it doesn't exist
  if not os.path.exists(OUTPUT_DIR):
    os.mkdir(OUTPUT_DIR)
  
  for p in site.pages:
    print "Rendering "+p.getTargetPath()
    out = codecs.open(p.getTargetPath(),'w',encoding=site.encoding)
    out.write(renderPage(p))
    
  # TODO: render modified tags
  # TODO: render modified categories
  # TODO: render sitemap if changed
  

if __name__ == '__main__':
  brew()