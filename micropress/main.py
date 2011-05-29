from micropress import Site,SITE_CONFIG_PATH
import sys

def run(argv):
  if len(argv) <= 1:
    cmd = 'brew' 
  else:
    cmd = argv[1]
  site = Site(SITE_CONFIG_PATH)
  if cmd == 'brew':
    site.brew()
  elif cmd == 'run':
    # web.py -  If called from the command line, it will start an HTTP server 
    # on the port named in the first command line argument, or, if there is no
    # argument, on port 8080.
    #sys.argv = sys.argv[2:]
    site.run()
  elif cmd == 'clean':
    site.clean()
  elif cmd == 'inventory':
    site.inventory()
  else:
    raise Exception("Invalid command %s"  % cmd)
    
if __name__ == '__main__':
  run(sys.argv)