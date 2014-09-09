import sys
import os
sys.path.insert(1, os.path.join(sys.path[0], '..'))

from traceurl import TraceUrl
import unittest

class TestTraceUrl(unittest.TestCase):
    def setUp(self):
        self.request = TraceUrl()

    def test_url1(self):
        ok, urls = self.request.go("http://www.naver.com")
        self.assertEqual(len(urls), 1)
        self.assertEqual(urls[0], "http://www.naver.com")

    def test_url2(self):
        result_urls = ['http://goo.gl/4TMs2e', 'http://www.naver.com/']

        ok, urls = self.request.go("http://goo.gl/4TMs2e")
        self.assertEqual(len(urls), 2)
        self.assertSequenceEqual(urls, result_urls)

    def test_url3(self):
        result_urls = ['http://goo.gl/gHzZIE', 'http://apache.mirror.cdnetworks.com/hadoop/common/hadoop-2.5.0/hadoop-2.5.0.tar.gz']

        ok, urls = self.request.go("http://goo.gl/gHzZIE")
        self.assertEqual(len(urls), 2)
        self.assertSequenceEqual(urls, result_urls)

    def test_url4(self):
        result_urls = ['http://bit.ly/1qAE4Ks', 'http://goo.gl/nwRmI', 'http://charsyam.wordpress.com/2011/08/22/memcached%EB%A5%BC-%EC%9D%B4%EC%9A%A9%ED%95%9C-simple-%EB%B6%84%EC%82%B0-%EB%9D%BD%EC%97%90-%EB%8C%80%ED%95%9C-%EC%A7%A7%EC%9D%80-%EA%B3%A0%EC%B0%B0/']

        ok, urls = self.request.go("http://bit.ly/1qAE4Ks")
        self.assertEqual(len(urls), 3)
        self.assertSequenceEqual(urls, result_urls)

if __name__ == '__main__':
    unittest.main()

