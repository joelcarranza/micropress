"""
Adds support for coffescript within the js/ directory. Supported
extension is .coffeescript. Relies on coffee executable being installed
on your path
"""

from micropress import Processor
from micropress.util import exectool
import os.path

class CoffeescriptProcessor(Processor):
  def __init__(self):
    Processor.__init__(self,'js','.coffee')
    
  def resource_from_path(self,path):
    (name,ext) = os.path.splitext(path) 
    return name+".js"

  def path_from_resource(self,rsc):
    (name,ext) = os.path.splitext(rsc) 
    return name+".coffee"
    
  def _dobuild(self,src,dest):
    outdir = os.path.dirname(dest)
    exectool('coffee','-c','-o',outdir,src);
    
def extend_micropress(site):
  site.processors.append(CoffeescriptProcessor())
