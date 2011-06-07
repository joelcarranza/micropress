"""
main.py

module for invoking micropress on the command line

"""

from micropress import Site,SITE_CONFIG_PATH,DEFAULT_OUTPUT_DIR
import sys
import argparse
import shutil
import os.path

def brew(argv):
  parser = argparse.ArgumentParser(description='build site')
  # -d outputdir
  parser.add_argument('-d', metavar='DIR', type=str,
                     default=DEFAULT_OUTPUT_DIR,dest='outputdir',
                     help='Alternate output dir')
  args = parser.parse_args(argv)
  site = Site(SITE_CONFIG_PATH)
  # TODO: provide way to set config parameters
  site.brew(args.outputdir)
  
def preview(args):
  import micropress.web  
  site = Site(SITE_CONFIG_PATH)  
  micropress.web.run(site)
  
def clean(args):
  site = Site(SITE_CONFIG_PATH)
  site.clean()

def inventory(args):
  site = Site(SITE_CONFIG_PATH) 
  site.inventory()
  
def help(args):
  print """usage: micropress <command>
  
  Available commands:
  brew - build site
  preview - preview site on localhost
  clean - remote site output
  inventory - list site contents
  """

def run(argv):
  if len(argv) <= 1:
    cmd = 'brew' 
  else:
    cmd = argv[1]
    argv = argv[2:]
    
  if cmd == 'brew':
    brew(argv)
  elif cmd == 'preview':
    preview(argv)
  elif cmd == 'clean':
    clean(argv)
  elif cmd == 'inventory':
    inventory(argv)
  elif cmd == 'help':
    help(argv)
  else:
    print "Invalid command %s"  % cmd
    help([])
    
if __name__ == '__main__':
  run(sys.argv)