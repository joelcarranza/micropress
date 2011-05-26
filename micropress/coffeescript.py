from micropress import Processor
from micropress import exectool
import os.path

class CoffeescriptProcessor(Processor):
  """docstring for CoffeescriptProcessor"""
  def __init__(self):
    Processor.__init__(self,'js','.coffee')
    
  def resource_from_path(self,path):
    """docstring for outputrsc"""
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
