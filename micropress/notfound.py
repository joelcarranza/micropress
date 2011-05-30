"""
Adds a resource named errors/404.html to your site, allowing you to 
construct a not found error page from a template called templates/404.tmpl
"""

from micropress import ResourceFactory
from micropress.util import exectool
import os.path
import xml.etree.ElementTree as ET

class ErrorProcessor(ResourceFactory):
    
  def __init__(self,site):
    ResourceFactory.__init__(self,site,'errors/404.html')
    
  def _dobuild(self,out):
    tmpl = self.site.load_template('404')
    f = open(out,'w')
    f.write(tmpl.render(
      site=self.site))
    
    
def extend_micropress(site):
  site.processors.append(ErrorProcessor(site))
