"""
Generate an RSS feed for you site at feed.xml
"""

from micropress import ResourceFactory
import os.path
import datetime
import PyRSS2Gen

def feed_link():
  return """<link href="feed.xml" rel="alternate" type="application/rss+xml" title="" />"""
  
class FeedProcessor(ResourceFactory):
    
  def __init__(self,site):
    ResourceFactory.__init__(self,site,'feed.xml')
    
  def _dobuild(self,out):
    site = self.site
    rss = PyRSS2Gen.RSS2(
        # TODO!
        title = site.config.get('rss-title'),
        link = site.abshref(),
        description = site.config.get('rss-descrioption'),
        lastBuildDate = datetime.datetime.utcnow())
    for p in site.querypages():
      url = p.abshref()
      rss.items.append( PyRSS2Gen.RSSItem(
         title = p.title,
         link = url, 
         description = p.content(),
         guid = PyRSS2Gen.Guid(url),
         pubDate = p.date_created()))

    rss.write_xml(open(out, "w"))
    
def extend_micropress(site):
  site.processors.append(FeedProcessor(site))
