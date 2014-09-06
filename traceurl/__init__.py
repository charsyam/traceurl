# -*- coding:utf-8 -*-

import httplib2
from encodings.punycode import punycode_encode
from encodings import idna
import re
from urlparse import urlparse 

#Using GET ONLY
DETAIL_TRACE_MODE = 0

#Using HEAD sometimes GET
FAST_TRACE_MODE = 1

DEFAULT_TRACE_NUMBER = 7
DEFAULT_TRACE_MODE = DETAIL_TRACE_MODE

meta_redirect_pattern = re.compile("<meta\s+(http-equiv|content)=['\"]?([^'\"]+)['\"]?\s+(http-equiv|content)=['\"]?([^'\"]*)['\"]?\s*/?>")
js1_redirect_pattern = re.compile("location.href\s*=\s*['\"]?([^'\"]*)['\"]?\s*/?")
js2_redirect_pattern = re.compile("location.replace\s*\(\s*['\"]?([^'\"]*)[,]?['\"]?\s*/?\)")

CANT_REDIRECT_TYPE = 0
META_REDIRECT_TYPE = 1
JS_REDIRECT_TYPE = 2

class TraceUrl(object):

    def __init__(self):
        self.TRACE_NUMBER   = DEFAULT_TRACE_NUMBER
        self.TRACE_MODE     = DEFAULT_TRACE_MODE
        self.trace_urls     = []
        self.use_proxy      = False
        self.proxy_type     = httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL;
        self.proxy_host     = None
        self.proxy_port     = 80
        self.use_punycode   = True

    def set_proxy_info(self, host, port, proxy_type = httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL):
        self.use_proxy = True
        self.proxy_type = proxy_type
        self.proxy_host = host
        self.proxy_port = port

    def extract_rediection_info_from_body(self, body):
        ok, url = self.get_meta_redirection_info(body)
        if ok == True:
            return META_REDIRECT_TYPE, url

        ok, url = self.get_js1_redirection_info(body)
        if ok == True:
            return JS_REDIRECT_TYPE, url

        ok, url = self.get_js2_redirection_info(body)
        if ok == True:
            return JS_REDIRECT_TYPE, url

        return False, ""

    def get_js_redirection_info(self, body, pattern):
        groups = pattern.findall(body)

        find = False
        url = ""
        if len(groups) > 0:
            find = True
            parts = re.split(';|\t|\n| ', groups[0].strip())
            url = parts[0]
            if len(parts) > 1:
                find = False
                url = ""

        return find, url

    def get_js1_redirection_info(self, body):
        global js1_redirect_pattern
        return self.get_js_redirection_info(body, js1_redirect_pattern)

    def get_js2_redirection_info(self, body):
        global js2_redirect_pattern
        return self.get_js_redirection_info(body, js2_redirect_pattern)

    def get_meta_redirection_info(self, body):
        global meta_redirect_pattern
        groups = meta_redirect_pattern.findall(body)

        find = False
        url = ""
        for group in groups:
            for item in group:
                pos = item.find("url=")
                if (pos >= 0):
                    find = True
                    url = item[pos+4:].strip()
                    break

            if (find == True):
                break

        return find, url

    def append_url(self, url):
        self.trace_urls.append(url)

    def get_new_url(self, urlinfo, url):
        new_url = ""
        if url.startswith('http://') == True or \
           url.startswith('https://') == True:
               new_url = url
        else:
            if url.startswith('/') == True:
                new_url = "%s://%s%s"%(urlinfo.scheme, urlinfo.netloc, url)
            else:
                new_url = "%s://%s%s/%s"%(urlinfo.scheme, urlinfo.netloc, urlinfo.path, url)

        return new_url

    def is_same_url(self, url, new_url):
        if(url == new_url):
            return True

        return False

    def go(self, url, callback=None):
        self.trace_urls = []
        if self.use_punycode:
            url = self.get_punycode_url(url)

        for i in xrange(self.TRACE_NUMBER):
            self.append_url(url)
            status, request, headers, body = self.trace(url)
            if status == True:
                if int(headers['status']) in [300, 301, 302, 303, 307]:
                    if headers.has_key('location'):
                        headers['content-length'] = headers['location']

                    url = headers['content-length']
                    continue

                if int(headers['status']) in [200]:
                    status, request, headers, body = self.trace(url, request)
                    redirect_type, new_url = self.extract_rediection_info_from_body(body)
                    if redirect_type in [META_REDIRECT_TYPE, JS_REDIRECT_TYPE]:
                        o = urlparse(url)
                        new_url = self.get_new_url(o, new_url)
                        if self.is_same_url(url, new_url):
                            return True, self.trace_urls

                        url = new_url
                        continue
                    else:
                        return True, self.trace_urls

                return True, self.trace_urls
            else:
                return True, self.trace_urls

    def get_trace_method(self, first_chance):
        if self.TRACE_MODE == FAST_TRACE_MODE and first_chance == True:
            return "HEAD"

        return "GET"

    def need_punycode(self, string):
        for ch in string:
            if ord(ch) > 127:
                return True

        return False

    def get_punycode_url(self, url):
        if self.need_punycode(url) == False:
            return url

        o = urlparse(url)
        ret_parts = []
        parts = idna.dots.split(o.netloc)

        for part in parts:
            if self.need_punycode(part) == True:
                part = "xn--%s"%(punycode_encode(part.decode('utf8')))

            ret_parts.append(part)

        if o.query == "":
            target_url = "%s://%s%s"%(o.scheme, '.'.join(ret_parts), o.path)
        else:
            target_url = "%s://%s%s?%s"%(o.scheme, '.'.join(ret_parts), o.path, o.query)

        return target_url

    def get_proxy_info(self):
        if self.proxy_host is None:
            pi = httplib2.proxy_info_from_environment()
            if not (hasattr(httplib2, 'socks') and
                    hasattr(httplib2.socks, 'PROXY_TYPE_HTTP_NO_TUNNEL')):
                return pi
        else:
            pi = httplib2.ProxyInfo(proxy_type = self.proxy_type,
                                    proxy_host = self.proxy_host,
                                    proxy_port = self.proxy_port)

        pi.proxy_type = self.proxy_type
        return pi

    def trace(self, url, request = None):
        first_chance = True
        if request is None:
            request = httplib2.Http()
            if self.use_proxy:
                request.proxy_info = self.get_proxy_info()
            request.follow_redirects = False
        else:
            first_chance = False

        try:
            resp = request.request(url, self.get_trace_method(first_chance))
            return True, request, resp[0], resp[1]
        except:
            return False, None, None, None

if __name__=='__main__':
    request = TraceUrl()
    print request.go('http://goo.gl/Ib9pjA')
