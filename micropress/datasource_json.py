import urllib2
import json

def loadjson(url):
  """load url from JSON"""
  if url.startswith("http:"):
    response = urllib2.urlopen(url)
    return json.load(response)
  else:
    return json.load(open(url,'r'))

def extend_micropress(site):
  site.util['json'] = loadjson