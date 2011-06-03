from micropress import Site,SITE_CONFIG_PATH,DEFAULT_OUTPUT_DIR
import sys
import argparse
import shutil
import os.path

def brew(args):
  site = Site(SITE_CONFIG_PATH)
  site.brew(DEFAULT_OUTPUT_DIR)
  
def run(args):
  import micropress.web  
  site = Site(SITE_CONFIG_PATH)  
  micropress.web.run(site)
  
def clean(args):
  if not os.path.exists(SITE_CONFIG_PATH):
    print "No site.yaml file. Clean skipped for safety reasons"
    return
  dir = DEFAULT_OUTPUT_DIR
  if os.path.exists(dir):
    shutil.rmtree(dir)
  else:
    print "No such output directory \"%s\" exists." %dir

def inventory(args):
  site = Site(SITE_CONFIG_PATH) 
  site.inventory()
  
def help(args):
  pass

def run(argv):
  if len(argv) <= 1:
    cmd = 'brew' 
  else:
    cmd = argv[1]
    argv = argv[1:]
    
  if cmd == 'brew':
    brew(argv)
  elif cmd == 'run':
    run(argv)
  elif cmd == 'clean':
    clean(argv)
  elif cmd == 'inventory':
    inventory(argv)
  elif cmd == 'inventory':
    inventory(argv)    
  elif cmd == 'help':
    help(argv)
  else:
    print "Invalid command %s"  % cmd
    
if __name__ == '__main__':
  run(sys.argv)