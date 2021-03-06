# -*- coding: utf-8 -*-

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
        self.assertEqual(len(urls), len(result_urls))
        self.assertSequenceEqual(urls, result_urls)

    #redirect and big file
    def test_url3(self):
        result_urls = ['http://goo.gl/gHzZIE', 'http://apache.mirror.cdnetworks.com/hadoop/common/hadoop-2.5.0/hadoop-2.5.0.tar.gz']

        ok, urls = self.request.go("http://goo.gl/gHzZIE")
        self.assertEqual(len(urls), len(result_urls))
        self.assertSequenceEqual(urls, result_urls)

    #redirect twice
    def test_url4(self):
        result_urls = ['http://bit.ly/1qAE4Ks', 'http://goo.gl/nwRmI', 'http://charsyam.wordpress.com/2011/08/22/memcached%EB%A5%BC-%EC%9D%B4%EC%9A%A9%ED%95%9C-simple-%EB%B6%84%EC%82%B0-%EB%9D%BD%EC%97%90-%EB%8C%80%ED%95%9C-%EC%A7%A7%EC%9D%80-%EA%B3%A0%EC%B0%B0/']

        ok, urls = self.request.go("http://bit.ly/1qAE4Ks")
        self.assertEqual(len(urls), len(result_urls))
        self.assertSequenceEqual(urls, result_urls)

    #frameset test
    def test_url5(self):
        result_urls = ['http://idol.zcc.kr', 'http://moum.kr/idol', 'http://moum.kr/idol/', 'http://www.toptoon.com/comic/ep_list/idoltwo/?p_id=page']

        ok, urls = self.request.go("http://idol.zcc.kr")
        self.assertSequenceEqual(urls, result_urls)

    #han.lk test
    def test_url6(self):
        result_urls = ['http://han.lk/묘낳발론마', 'http://www.naver.com']

        ok, urls = self.request.go("http://han.lk/묘낳발론마")
        self.assertSequenceEqual(urls, result_urls)

    #over limit times
    def test_url7(self):
        result_urls = ['http://bugs.kr/EZvRy', 'http://music.bugs.co.kr/track/3626773']

        ok, urls = self.request.go("http://bugs.kr/EZvRy")
        self.assertEqual(len(urls), len(result_urls))
        self.assertSequenceEqual(urls, result_urls)

    #concat error
    def test_url8(self):
        result_urls = ['http://buy.lh.or.kr', 'http://buy.lh.or.kr/index.jsp', 'http://buy.lh.or.kr//main.jsp', 'http://buy.lh.or.kr///../comm/topmenu02.jsp']

        ok, urls = self.request.go("http://buy.lh.or.kr")
        self.assertSequenceEqual(urls, result_urls)

    #remove onclick javascript location change
    def test_url9(self):
        result_urls = ['http://www.humorschool.co.kr/test/64']

        ok, urls = self.request.go("http://www.humorschool.co.kr/test/64")
        self.assertEqual(len(urls), len(result_urls))
        self.assertSequenceEqual(urls, result_urls)

    #case for return 403, invalid user-agent
    def test_url10(self):
        result_urls = ['http://me2.do/GN2XbdXQ', 'http://eaf.kr/43Q565', 'http://dw231.dq.to', 'http://bozi.xam.kr', 'http://www.bondisk.com/?ad=asdfg1234&join=Y', 'http://www.bondisk.com/main/doc.php?doc=join_regist']
        ok, urls = self.request.go("http://me2.do/GN2XbdXQ")
        self.assertSequenceSome(result_urls, urls, 6)

    #case for prefer url 
    def test_url11(self):
        result_urls = ['http://cox.kr/7511', 'http://cox.kr/shorturl_ok.php?no=7511', 'http://freeavii.net/index.php?u=pks1470&c=3', 'http://clickhere.kr/index_bon.php', 'http://clickhere.kr/index_bonpc.php', 'http://www.bondisk.com/?ad=phps&join=Y']
        ok, urls = self.request.go("http://cox.kr/7511")
        self.assertSequenceEqual(result_urls, urls)

    def assertSequenceSome(self, expected, results, count):
        limited_urls = expected[0:count]
        self.assertSequenceEqual(limited_urls, results)

if __name__ == '__main__':
    unittest.main()
