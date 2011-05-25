from micropress import Processor
from micropress import exectool
import os.path

class LessProcessor(Processor):
  """docstring for CoffeescriptProcessor"""
  def __init__(self):
    Processor.__init__(self,'css','.less')
    
  def resource_from_path(self,path):
    """docstring for outputrsc"""
    (name,ext) = os.path.splitext(path) 
    return name+".css"

  def path_from_resource(self,rsc):
    (name,ext) = os.path.splitext(rsc) 
    return name+".less"
    
  def _dobuild(self,src,dest):
    exectool('less',src,dest);
    
def extend_micropress(site):
  site.processors.append(LessProcessor())
