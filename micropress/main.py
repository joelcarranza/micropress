from micropress import Site,SITE_CONFIG_PATH
import sys
import argparse

def brew(args):
  site = Site(SITE_CONFIG_PATH)
  site.brew()
  
def run(args):
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