"""
Generate an RSS feed for you site at feed.xml

Configuration parameters:
  rss-title: title of RSS feed
  rss-description: description of RSS feed
"""

from micropress import ResourceFactory
import os.path
import datetime
import PyRSS2Gen

def feed_link(site):
  return """<link href="%s" rel="alternate" type="application/rss+xml" title="%s" />""" % (site.resource_href('feed.xml'),site.config.get('rss-title','RSS Feed'))
  
class FeedProcessor(ResourceFactory):
    
  def __init__(self,site):
    ResourceFactory.__init__(self,site,'feed.xml')
    
  def _dobuild(self,out):
    site = self.site
    rss = PyRSS2Gen.RSS2(
        # TODO: are title/description required fields?
        title = site.config.get('rss-title'),
        link = site.url(),
        description = site.config.get('rss-description'),
        lastBuildDate = datetime.datetime.utcnow())
    for p in site.querypages():
      url = p.url()
      rss.items.append( PyRSS2Gen.RSSItem(
         title = p.title,
         link = url, 
         description = p.content(),
         guid = PyRSS2Gen.Guid(url),
         pubDate = p.date_created()))
    # TODO: encoding
    rss.write_xml(open(out, "w"))
    
def extend_micropress(site):
  site.ext['feed_link'] = feed_link
  site.processors.append(FeedProcessor(site))
