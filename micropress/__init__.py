#!/usr/bin/env python
# encoding: utf-8
"""
micropress.py

class Processor()
  # docstring for Processor
    
  def resources(self):
    # enumeration of all resources that this processor publishes
    
  def accept(self,rsc):
    # determine if the processor can handle this resource
    
  def build(self,rsc,outdir):
    # create the resource in the specified directory

Created by Joel Carranza on 2011-04-09.
Copyright (c) 2011 Joel Carranza. All rights reserved.
"""

__version_info__ = ('0', '1')
__version__ = '.'.join(__version_info__)

import os
import codecs
import os.path
import shutil
import sys
import re
import hashlib
from datetime import datetime

import markdown
from jinja2 import Template,Environment,FileSystemLoader
import yaml

from micropress.util import *

# constants
SITE_CONFIG_PATH = 'site.yaml'
TEMPLATE_DIR = 'templates'
RESOURCES_DIR = 'resources'
PAGES_DIR = 'pages'
DEFAULT_OUTPUT_DIR = 'site'
DEFAULT_PREVIEW_DIR = '.preview'

# TODO: template functions! - what do we need here?

class Processor():
  """
  Processor copies all files from a specified
  directory into the output directory. Subclasses
  may add additional file processing. Path is
  untranslated unless a subclass overrides
  resource_from_path/path_from_resource
  
  abc/foo.css -> abc/foo.css
  """
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
        if f[0] == '.': # skip invisible
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
    """
    Perform the build on a source file with a target destination. By
    default simply performs a copy of the source file. Subclasses may
    override to implement processing of some kind
    """
    shutil.copyfile(src,dest)
    
  def build(self,rsc,outdir):
    """create the specified resource in the output directory"""
    dest = os.path.join(outdir,rsc)
    dirname = os.path.dirname(dest)
    mkdir(dirname)
    src = self.path_from_resource(rsc)
    if not isuptodate(dest,src):
      # root include resources - needs to
      info("copying to %s " % dest)
      self._dobuild(src,dest)
    else:
      debug("skipping %s" % dest)
    
      
class StaticResourcesProcessor(Processor):
  """
  Processor copies all files from a specified
  directory. Path is translated to the source
  directory (indir). So for example
  
  indir/a/foo.css -> a/foo.css
  """
  
  def resource_from_path(self,path):
    # strip leading directory prefix
    n = len(self.indir)+1
    return path[n:]
    
  def path_from_resource(self,rsc):
    return os.path.join(self.indir,rsc)
    
class ResourceFactory():
  """
  Processor which creates a single resource by name
  """
  def __init__(self,site,name):
    self.site = site
    self.name = name

  def resources(self):
    return [self.name]

  def accept(self,rsc):
    return rsc == self.name

  def _dobuild(dest):
    "Subclasses must implement this method"
    pass
    
  def build(self,rsc,outdir):
    dest = os.path.join(outdir,rsc)
    dirname = os.path.dirname(dest)
    if not os.path.exists(dirname):
      os.mkdir(dirname)
    self._dobuild(dest)
    
class Site():
  """
  Singleton describing the info for building a site. Contains implicitly
  a number of pages and a series of processors which produce rsources
  
  Attributes:
    path - path to YAML config file
    config - instantiated config file
    processors - list of processors
    encoding - defined encoding from config file
    domain - URL where site will ultimately be deployed from config
    root - path name for where site is deployed (default /)
    hooks - List of function that will be invoked with specified hooks
    
  Hook events:
    load
    pre-brew
    post-brew
  """
  
  def __init__(self,path):
    self.hooks = []
    self._loaded_ext = []
    self.ext = {}
    self.pages = {}
    self.path = path
    self.markdown_opts = {}
    self.config = {}
    self.dynamic = False
    self.page_decorators = []
    self.processors = [
      StaticResourcesProcessor("resources"),
      Processor("css",".css"),
      Processor("js",".js")      
    ]
    # extension should be able to add to templates too!
    self.load()
    self.env = Environment(loader=FileSystemLoader(os.getcwd()+'/templates'))
    self.loadpages()
    self._fire_hook('load')
    
  # TODO: we need to be really clear here about absolute/relative links
  # URL might be a good term to use
  def url(self):
    "Absolute path to the site root"
    if self.domain is None:
      raise Exception("No domain configured")
    return self.domain+self.root

  def resource_href(self,rsc):
    "Lookup a resource by name, and returns the path to that resource"
    for proc in self.processors:
       if proc.accept(rsc):
         return self.root+rsc
    raise Exception("No resource %s found" %rsc)  
    
  def getcontents(self,file):
    "read the contents of a file. Useful for template includes"
    f = codecs.open(file, mode="r",encoding=self.encoding)
    return f.read()
    
  def load_extension(self,module):
    """
    Load an extension into the site. An extension is a module which
    contains a function with the signature:
    
    def extend_micropress(site):
      pass
    """
    if module not in self._loaded_ext:
      # http://docs.python.org/library/functions.html#__import__
      # If you simply want to import a module (potentially within a package) by name, you can call __import__() and then look it up in sys.modules:
      __import__(module)
      ext = sys.modules[module]
      ext.extend_micropress(self)
      self._loaded_ext.append(module)
  
  def load_template(self,name):
    return self.env.get_template(name+".tmpl")

  def _fire_hook(self,event):
    "Invoke all hooks with the specified event"
    for h in self.hooks:
      h(self,event)

  def load(self):
    """Load options from config file"""
    self.config = yaml.load(open(self.path))
    for ext in self.config.get('extensions',[]):
      self.load_extension(ext)
    self.encoding = self.config.get('encoding','utf8')
    self.domain = self.config.get('domain')
    self.root = self.config.get('root','/')
    self.markdown = markdown.Markdown(**(self.config.get('markdown',{})))
    # alright we're loaded
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
           p = Page(self,path)
           for decorators in self.page_decorators:
            decorators.extend_page()
           newpages[rest] = p
    self.pages = newpages
  
  def page(self,path):
    "Return a page by name. Returns None if no such page exists"
    p = self.pages.get(path)
    if p and self.dynamic:
      p.refresh()
    return p
    
  # this is inspired by the wordpress loop!
  # http://codex.wordpress.org/Template_Tags/get_posts
  # TODO: is tag/category really necessary? ... hmmmm
  def querypages(self,tag=None,category=None,maxitems=None,order=None):
    """
    Return a list of defined pages, optionally filter by particular
    attributes and/or sorted in some particular way
    """
    
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
    self._fire_hook('load')
  
  def brew(self,outputdir):
    "Create the site in the specified output directory"
    
    self._fire_hook('pre-brew')
    # create output dir if it doesn't exist
    mkdir(outputdir)

    for p in self.processors:
        for rsc in p.resources():
          p.build(rsc,outputdir)

    # make pages
    for p in self.querypages():
      p.make(outputdir)
    self._fire_hook('post-brew')
      
  def inventory(self):
    "list the contents of the site to stdout"
    for p in self.processors:
      for r in p.resources():
        print r
    for p in self.querypages():
      print p.name+".html"

class Page():
  """
  A page is created for each markdown/html file in your pages/ 
  directory
  
  Attributes:
  site - parent
  header - dictionary of key/value pairs specifed in page file header
  path - file path to source file
  """
  # TODO: excerpt
  
  def __init__(self,site,path):
    self.site = site
    self.path = path
    self.load()
  
  # TODO: move the parsing of a page out of Page itself
  # and into the site - !
  def _read(self):
    "read the target file and parse returning header (dict) and content"
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
    return (header,body)
    
  def load(self):
    (header,body) = self._read()
    (rest,ext) = os.path.splitext(self.path)
    self.type = ext[1:] # markdown or html
    # strip leading page dir 
    # TODO: this is just a little fragile
    self.name = self.path[6:].split('.')[0]
    self.header = header
    self.title = header.get('title',self.name)
    self.template = header.get('template','default')
    self.tags = re.split(r'\s*,\s*',header['tags']) if 'tags' in header else []
    self.category = header.get('category')
    self.body = body
    self.loadts = os.path.getmtime(self.path)
  
  def url(self):
    "Absolute path to this page"
    return self.site.url()+self.name+".html"
    
  def href(self,base=None):
    "Path to this page"
    return self.name+'.html'
    
  def date_created(self,fmt=None):
    """
    Creation date of this page. Uses the ctime of the source file
    or the header value 'date-created'
    TODO: describe date format
    """
    if 'date-created' in self.header:
      dt = parse_datetime(self.header['date-created'])
    else:
      dt = datetime.fromtimestamp(os.path.getctime(self.path))
    if fmt:
      return dt.strftime(fmt)
    else:
      return dt
  
  def date_modified(self,fmt=None):
    """
    Modification date of this page. Uses the mtime of the source
    file
    """
    # TODO: allow to set date_modified on header?
    dt = datetime.fromtimestamp(os.path.getmtime(self.path))
    if fmt:
      return dt.strftime(fmt)
    else:
      return dt
    
  def content(self):
    "Access the HTML content (without template) of this page"
    if self.type == 'html':
      return self.body
    else:
      return self.site.markdown.convert(self.body)
    
  def refresh(self):
    """Reload configuration if needed"""
    if os.path.getmtime(self.path) != self.loadts:
      self.load()
  
  def render(self):
    "Get the final HTML contents of the page and template as a string"
    t = self.site.load_template(self.template)
    return t.render(
      content=self.content(),
      page=self,
      site=self.site)
      
  def make(self,outputdir):
    "Create the rendered page in the specified directory"
    f = os.path.join(outputdir,self.name+'.html')
    info("Rendering "+f)
    mkdir(os.path.dirname(f))
    result = self.render()
    if os.path.exists(f):
      md5 = hashlib.md5()
      md5.update(result.encode(self.site.encoding))
      if md5.digest() == md5_for_file(f):
        debug("Nothing changed %s" %f)
        return
    out = codecs.open(f,'w',encoding=self.site.encoding)
    try:
      out.write(result)
    finally:
      out.close()