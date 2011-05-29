# allows up to import json even though we are called json
# See: http://docs.python.org/whatsnew/2.5.html#pep-328
from __future__ import absolute_import
import urllib2
import json as jsonlib

def loadjson(url):
  """load url from JSON"""
  if url.startswith("http:"):
    response = urllib2.urlopen(url)
    return jsonlib.load(response)
  else:
    return jsonlib.load(open(url,'r'))

def extend_micropress(site):
  site.util['json'] = loadjson