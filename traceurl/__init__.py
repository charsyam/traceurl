import httplib2
import re

#Using GET ONLY
DETAIL_TRACE_MODE = 0

#Using HEAD sometimes GET
BEST_TRACE_MODE = 1

DEFAULT_TRACE_NUMBER = 5
DEFAULT_TRACE_MODE = BEST_TRACE_MODE

meta_redirect_pattern = re.compile("<meta\s+(http-equiv|content)=['\"]?([^'\"]+)['\"]?\s+(http-equiv|content)=['\"]?([^'\"]*)['\"]?\s*/?>")

class TraceUrl(object):

    def __init__(self):
        self.TRACE_NUMBER   = DEFAULT_TRACE_NUMBER
        self.TRACE_MODE     = DEFAULT_TRACE_MODE
        self.trace_urls     = []
        self.use_proxy      = False
        self.proxy_type     = httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL;
        self.proxy_host     = None
        self.proxy_port     = 80

    def set_proxy_info(self, host, port, proxy_type = httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL):
        self.use_proxy = True
        self.proxy_type = proxy_type
        self.proxy_host = host
        self.proxy_port = port

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
                    url = item[pos+4:]
                    break

            if (find == True):
                break

        return find, url

    def append_url(self, url):
        self.trace_urls.append(url)

    def go(self, url, callback=None):
        self.trace_urls = []

        for i in xrange(self.TRACE_NUMBER):
            status, request, headers, body = self.trace(url)
            if status == True:
                if int(headers['status']) in [300, 301, 302, 303, 307]:
                    if headers.has_key('location'):
                        headers['content-length'] = headers['location']

                    self.append_url(url)
                    url = headers['content-length']
                    continue

                if int(headers['status']) in [200]:
                    status, request, headers, body = self.trace(url, request)
                    is_meta_redirect, new_url = self.get_meta_redirection_info(body)
                    if is_meta_redirect:
                        self.append_url(url)
                        url = new_url
                        continue
                    else:
                        self.append_url(url)
                        return True, self.trace_urls
                
                return False, self.trace_urls
            else:
                return False, self.trace_urls

    def get_trace_method(self, first_chance):
        if self.TRACE_MODE == BEST_TRACE_MODE and first_chance == True:
            return "HEAD"

        return "GET"

    def get_proxy_info(self):
        if self.proxy_host is None:
            pi = httplib2.proxy_info_from_environment()
            if not (hasattr(httplib2, 'socks') and
                    hasattr(httplib2.socks, 'PROXY_TYPE_HTTP_NO_TUNNEL')):
                return pi
        else:
            pi = httplib2.ProxyInfo(proxy_type = self.proxy_type,
                                    proxy_host = host,
                                    proxy_port = port)

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
