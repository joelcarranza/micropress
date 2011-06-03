"""Unit test for roman.py"""

from micropress import Site,Page
import unittest
import datetime
from micropress import DEFAULT_OUTPUT_DIR

class SiteTest(unittest.TestCase):
  def setUp(self):
    self.site = Site('site.yaml')
  
  def testPage(self):
    site = self.site
    self.assertTrue(site.page('lorem') is not None)
    self.assertTrue(site.page('sub/subpage') is not None)
    self.assertTrue(site.page('lorem-Z') is None)
    
  def testQueryPages(self):
    site = self.site
    self.assertEqual(len(site.querypages()),2);
    self.assertEqual(len(site.querypages(tag='foo')),1);
    self.assertEqual(len(site.querypages(category='alt')),1);
    
  def testBrew(self):
    self.site.brew(DEFAULT_OUTPUT_DIR)
    
  def testGetContents(self):
    self.assertEqual(self.site.getcontents('include/include-me.txt'),"Hello World!")
    
class PageTest(unittest.TestCase):
  def setUp(self):
    self.site = Site('site.yaml')

  def testPageLoad(self):
    p = self.site.page('lorem')
    self.assertEqual(p.title,"Lorem Ipsum")
    self.assertEqual(p.tags,['foo','bar'])
    self.assertTrue(p.category is None)
    self.assertEqual(p.template,'default')
    
    p = self.site.page('sub/subpage')
    self.assertEqual(p.title,"sub/subpage")
    self.assertEqual(p.tags,[])
    self.assertEqual(p.category,'alt')
    self.assertEqual(p.template,'alternate')
    
#    self.assertTrue(isinstance(p.date_created(),types.datetime))

if __name__ == "__main__":
    unittest.main()