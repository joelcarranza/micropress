"""
Adds support for the less CSS processing engine within the css/ directory. Supported extension is .less. Relies on lessc executable being installed
on your path

See http://lesscss.org/ for more details

TODO: optionally minify CSS
"""

from micropress import Processor
from micropress.util import exectool
import os.path

class LessProcessor(Processor):
  """docstring for CoffeescriptProcessor"""
  def __init__(self,site):
    Processor.__init__(self,'css','.less')
    self.site = site
    
  def resource_from_path(self,path):
    """docstring for outputrsc"""
    (name,ext) = os.path.splitext(path) 
    return name+".css"

  def path_from_resource(self,rsc):
    (name,ext) = os.path.splitext(rsc) 
    return name+".less"
    
  def _dobuild(self,src,dest):
    args = [src,dest]
    # output compressed unless in preview mode
    if not self.site.preview_mode:
      args.append('-x') 
    exectool('lessc',*args);
    
def extend_micropress(site):
  site.processors.append(LessProcessor(site))
