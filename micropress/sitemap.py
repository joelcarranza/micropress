from micropress import Processor
from micropress.util import exectool
import os.path
import xml.etree.ElementTree as ET

# see http://www.sitemaps.org/protocol.php

def indent(elem, level=0):
    i = "\n" + level*"  "
    if len(elem):
        if not elem.text or not elem.text.strip():
            elem.text = i + "  "
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
        for elem in elem:
            indent(elem, level+1)
        if not elem.tail or not elem.tail.strip():
            elem.tail = i
    else:
        if level and (not elem.tail or not elem.tail.strip()):
            elem.tail = i

def subel(elem,values):
  for (key,value) in values.items():
    ET.SubElement(elem, key).text = value
            
class SitemapProcessor():
    
  def __init__(self,site):
    self.site = site
    
  def resources(self):
    """enumeration of all resources that this processor publishes"""
    return ['sitemap.xml']
  
  def accept(self,rsc):
    return rsc == 'sitemap.xml'
    
  def build(self,rsc,outdir):
    """create the target resource in the output directory"""
    root = ET.Element("urlset",dict(xmlns='http://www.sitemaps.org/schemas/sitemap/0.9'))
    for p in self.site.querypages():
      attr = dict(loc=p.href(),lastmod=p.date_modified('%Y-%m-%d'))
      if 'sitemap-changefreq' in p.header:
        # TODO: validate input
        attr['changefreq'] = p.header['sitemap-changefreq']
      if 'sitemap-priority' in p.header:
        # TODO: validate input
        attr['priority'] = p.header['sitemap-priority']
      subel(ET.SubElement(root, "url"),attr)
    indent(root)
    tree = ET.ElementTree(root)
    tree.write(os.path.join(outdir,rsc))
    
  def make(self,outdir):
    for rsc in self.resources():
      self.build(rsc,outdir)
    
def extend_micropress(site):
  site.processors.append(SitemapProcessor(site))
