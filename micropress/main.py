"""
main.py

module for invoking micropress on the command line

"""

from micropress import Site,SITE_CONFIG_PATH,DEFAULT_OUTPUT_DIR
import sys
import argparse
import shutil
import os.path

def brew(args):
  site = Site(SITE_CONFIG_PATH)
  site.brew(args.outputdir)
  
def preview(args):
  import micropress.web  
  site = Site(SITE_CONFIG_PATH)  
  micropress.web.run(site,args.host,args.port)
  
def clean(args):
  site = Site(SITE_CONFIG_PATH)
  site.clean()

def inventory(args):
  site = Site(SITE_CONFIG_PATH) 
  site.inventory()

def run(argv):
  parser = argparse.ArgumentParser()
  subparsers = parser.add_subparsers()
  # brew
  parser_brew = subparsers.add_parser('brew',help="build site")
  parser_brew.add_argument('-d', metavar='DIR', type=str,
                      default=DEFAULT_OUTPUT_DIR,dest='outputdir',
                      help='Alternate output dir')
  parser_brew.set_defaults(cmd=brew)
  
  # preview
  parser_preview = subparsers.add_parser('preview',help="preview site with embedded web server")
  parser_preview.add_argument('--host', metavar='HOST', type=str,
                      default='localhost',dest='host',
                      help='Bind host')
  parser_preview.add_argument('-p', metavar='PORT', type=int,
                      default=8080,dest='port',
                      help='Server port')
  
  parser_preview.set_defaults(cmd=preview)

  # clean
  parser_clean = subparsers.add_parser('clean',help="remove site output")
  parser_clean.set_defaults(cmd=clean)
  
  # inventory
  parser_inventory = subparsers.add_parser('inventory',help="list site contents")
  parser_inventory.set_defaults(cmd=inventory)
  
  args = parser.parse_args(argv[1:])
  args.cmd(args)
      
if __name__ == '__main__':
  run(sys.argv)