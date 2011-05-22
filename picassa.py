import gdata.photos.service
import gdata.media
import gdata.geo
import StringIO

class Picassa():
  def __init__(self):
    gd_client = gdata.photos.service.PhotosService()
    gd_client.email = 'joel.carranza@gmail.com'
    gd_client.password = 'IE2XApY7FAVf'
    gd_client.source = 'exampleCo-exampleApp-1'
    gd_client.ProgrammaticLogin()
    self.client = gd_client

  def albums(self):
    albums = self.client.GetUserFeed(user='carranza.collective@gmail.com')
    ids = []
    for album in albums.entry:
      print "****"
      print "title: %s\nnumber of photos: %s\npicasa: %s" % (album.title.text,
          album.numphotos.text, album.gphoto_id.text)
    return ids
          
  def get_photo_link(self,p):
    for l in p.link:
        if l.type == 'text/html' and l.rel == 'http://schemas.google.com/photos/2007#canonical':
          return l.href
    return None
    
  def album_html(self,id):
    f = StringIO.StringIO()
    print id
    url =  "https://picasaweb.google.com/data/feed/api/user/carranza.collective/albumid/%s?kind=photo" % id
    result = self.client.GetFeed(url)
    for p in result.entry:
      t = p.media.thumbnail[-1]
      c = p.media.content[0]
      f.write("""
  <div class="frame">
    <a href="%s">
      <img src="%s" width="%s" height="%s"></a>
  </div>""" % (self.get_photo_link(p),t.url,t.width,t.height))
    return f.getvalue()

if __name__ == '__main__':
  p = Picassa()
  p.albums()
