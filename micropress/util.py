"""
micropress.util

An assortment of utility routines for working within micropress
"""

import os
import os.path
import hashlib
import subprocess
from datetime import datetime

# logging
# TODO: remove camel case
debug_level = 0

def info(msg):
  """Print log message"""
  if debug_level >= 0:
    print msg

def debug(msg):
  """Print log message if debug level is set > 1"""
  if debug_level >= 1:
    print msg

def trace(msg):
  """Print log message if debug level is set > 2"""
  if debug_level >= 2:
    print msg
    
def listfiles(dir):
  "List all files (recursively) under directory"
  # TODO: implement a common list of exclusions
  for root, dirs, files in os.walk(dir):
    # do not walk directories with dot prefix
    dirs[:] = [d for d in dirs if d[0] != '.']
    for f in files:
      # path contains prefix of dir - strip prefix
      path = os.path.join(root,f)[len(dir)+1:]
      yield path

def isuptodate(dest,*sources):
  """
  Check a source file for modification against a numer of other files
  """
  if not os.path.exists(dest):
   return False
  for src in sources:
   if os.path.getmtime(src) > os.path.getmtime(dest):
     return False
  return True

# http://stackoverflow.com/questions/1131220/get-md5-hash-of-a-files-without-open-it-in-python
def md5_for_file(filename, block_size=2**20):
   "get the md5 hash of a file"
   f = open(filename,'r')
   md5 = hashlib.md5()
   while True:
       data = f.read(block_size)
       if not data:
           break
       md5.update(data)
   return md5.digest()
     
def mkdir(dir):
 "Create a directory if it does not exist"
 if not os.path.exists(dir):
   os.makedirs(dir)

def parse_datetime(value):
 """
 Parse datetime as string
 """
 # TODO: extension to replace
 # TODO: should handle time
 return datetime.strptime(value,'%m/%d/%Y')


# Good resource on subprocess
# http://www.doughellmann.com/PyMOTW/subprocess/index.html

def exectool(cmd,*args):
   """Run a program - check for valid return"""
   proc = subprocess.Popen((cmd,)+args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
   output = proc.communicate()[0]
   # print output if we have anything
   if output:
     print cmd+": "+output
   # raise error if failed!
   if proc.returncode != 0:
     raise Exception("%s returned err code %i" % (cmd,proc.returncode))