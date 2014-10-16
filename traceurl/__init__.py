# -*- coding:utf-8 -*-

import httplib2
from encodings.punycode import punycode_encode
from encodings import idna
import re
from urlparse import urlparse
import urllib

USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_9_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/37.0.2062.124 Safari/537.36"
#Using GET ONLY
DETAIL_TRACE_MODE = 0

#Using HEAD sometimes GET
FAST_TRACE_MODE = 1

DEFAULT_TRACE_NUMBER = 7
DEFAULT_TRACE_MODE = FAST_TRACE_MODE

PARSE_NONE = 0
PARSE_TAG = 1
PARSE_STRING1 = 2
PARSE_STRING2 = 3
PARSE_HTMLCOMMENT = 4

meta_redirect_pattern = re.compile("<meta\s+(http-equiv|content)=['\"]?([^'\"]+)['\"]?\s+(http-equiv|content)=['\"]?([^'\"]*)['\"]?\s*/?>")
js1_redirect_pattern = re.compile("location.href\s*=\s*['\"]?([^'\"]*)['\"]?\s*/?")
js2_redirect_pattern = re.compile("location.replace\s*\(\s*['\"]?([^'\"]*)[,]?['\"]?\s*/?\)")
frameset_pattern = re.compile("(?im)<frame\s+(name|src)=['\"]?([^'\"]+)['\"]?\s+(?im)(name|src)=['\"]?([^'\"]*)['\"]?\s*/?>")

CANT_REDIRECT_TYPE = 0
META_REDIRECT_TYPE = 1
JS_REDIRECT_TYPE = 2
FRAMESET_REDIRECT_TYPE = 3

REDIRECT_LIST = [
        META_REDIRECT_TYPE,
        JS_REDIRECT_TYPE,
        FRAMESET_REDIRECT_TYPE
]

GET_ONLY = {
        "me2.do": 1
}

class TraceUrl(object):

    def __init__(self):
        self.TRACE_NUMBER   = DEFAULT_TRACE_NUMBER
        self.TRACE_MODE     = DEFAULT_TRACE_MODE
        self.trace_urls     = []
        self.use_proxy      = False
        self.proxy_type     = httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL
        self.proxy_host     = None
        self.proxy_port     = 80
        self.use_punycode   = True
        self.current_method = ""

    def set_proxy_info(self, host, port, proxy_type = httplib2.socks.PROXY_TYPE_HTTP_NO_TUNNEL):
        self.use_proxy = True
        self.proxy_type = proxy_type
        self.proxy_host = host
        self.proxy_port = port

    def extract_script(self, body):
        state = PARSE_NONE
        sub_state = 0
        in_tag = 0

        tag_start = -1
        result = ""

        length = len(body)

        start_tag_length = len("<script>")
        end_tag_length = len("</script>")

        i = 0;
        while (i < length):
            ch = body[i]
            if state == PARSE_NONE and sub_state == PARSE_NONE and ch == '<':
                if in_tag == 0 and (length - i >= start_tag_length):
                    tag = body[i:i+start_tag_length-1].lower()
                    if tag == "<script":
                        in_tag = 1
                        i += (start_tag_length - 1 - 1)
                        state = PARSE_TAG
                elif in_tag == 1 and (length - i >= end_tag_length):
                    tag = body[i:i+end_tag_length].lower()
                    if tag == "</script>":
                        in_tag = 0
                        state = PARSE_NONE
                        content = body[tag_start:i]
                        result += content
                        i += (end_tag_length - 1)
            elif state == PARSE_TAG and sub_state == PARSE_NONE and ch == '>':
                tag_start = i+1
                state = PARSE_NONE
            elif sub_state not in [PARSE_STRING1, PARSE_STRING2] and ch == '"':
                sub_state = PARSE_STRING1
            elif sub_state not in [PARSE_STRING1, PARSE_STRING2] and ch == '\'':
                sub_state = PARSE_STRING2
            elif sub_state == PARSE_STRING1 and ch == '"':
                sub_state = PARSE_NONE
            elif sub_state == PARSE_STRING2 and ch == '\'':
                sub_state = PARSE_NONE

            i += 1

        return result

    def get_prefer_url(self, url1, url2):
        prefer_url = ""
        if url1 != "" and self.is_not_url(url1) == False:
            return url1
        elif url2 != "" and self.is_not_url(url2) == False:
            return url2

        return prefer_url

    def get_js_redirection_info(self, body):
        script_body = self.extract_script(body)
        if body == "":
            return False, None

        ret = False
        prefer_url = ""
        ok1, url1 = self.get_js1_redirection_info(script_body)
        ok2, url2 = self.get_js2_redirection_info(script_body)

        if ok1 == True or ok2 == True:
            ret = True

        if ret == True:
            prefer_url = self.get_prefer_url(url1, url2)
            if prefer_url is "":
                if url1 is not "":
                    prefer_url = url1
                elif url2 is not "":
                    prefer_url = url2

        return ret, prefer_url


    def extract_rediection_info_from_body(self, body):
        ok, url = self.get_meta_redirection_info(body)
        if ok == True:
            return META_REDIRECT_TYPE, url

        ok, url = self.get_frameset_redirection_info(body)
        if ok == True:
            return FRAMESET_REDIRECT_TYPE, url

        ok, url = self.get_js_redirection_info(body)
        if ok == True:
            return JS_REDIRECT_TYPE, url

        return False, ""

    def get_frameset_redirection_info(self, body):
        global frameset_pattern
        groups = frameset_pattern.findall(body)

        find = False
        url = ""
        if len(groups) > 0:
            for group in groups:
                if group[0].lower() == "name":
                    url = group[3]
                    find = True
                    break

                elif group[0].lower() == "src":
                    if group[1] == "":
                        continue

                    url = group[1]
                    find = True
                    break
                else:
                    find = False

        return find, url

    def get_js_redirection_info_internal(self, body, pattern):
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
        return self.get_js_redirection_info_internal(body, js1_redirect_pattern)

    def get_js2_redirection_info(self, body):
        global js2_redirect_pattern
        return self.get_js_redirection_info_internal(body, js2_redirect_pattern)

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
        if url not in self.trace_urls:
            self.trace_urls.append(url)

    def get_new_url(self, urlinfo, url):
        new_url = ""
        if url.startswith('http://') == True or \
           url.startswith('https://') == True:
               new_url = url
        elif url.startswith('market://') == True:
            new_url = url
        else:
            if url.startswith('/') == True:
                new_url = "%s://%s%s"%(urlinfo.scheme, urlinfo.netloc, url)
            else:
                paths = urlinfo.path.split('/')
                paths[-1] = url
                new_path = '/'.join(paths)
                new_url = "%s://%s/%s"%(urlinfo.scheme, urlinfo.netloc, new_path)

        return new_url

    def encode_url_path(self, urlinfo, url):
        if self.need_encode(urlinfo.path) == False:
            return url

        parts = urlinfo.path.split('/')
        ret_parts = []
        for part in parts:
            if self.need_encode(part) == True:
                part = urllib.quote_plus(part)

            ret_parts.append(part)

        new_path = '/'.join(ret_parts)
        if urlinfo.query == "":
            new_url = "%s://%s%s"%(urlinfo.scheme, urlinfo.netloc, new_path)
        else:
            new_url = "%s://%s%s?%s"%(urlinfo.scheme, urlinfo.netloc, new_path, urlinfo.query)

        return new_url

    def go(self, url, callback=None):
        self.trace_urls = []
        if self.use_punycode:
            url = self.get_punycode_url(url)

        request = None
        add_url = True
        for i in xrange(self.TRACE_NUMBER):
            if add_url is True:
                self.append_url(url)

            o = urlparse(url)
            url = self.encode_url_path(o, url)
            add_url = True
            status, request, headers, body = self.trace(url, o.netloc, request)
            if headers == None:
                return True, self.trace_urls

            if 'content-type' not in headers:
                headers['content-type'] = "unknown"

            if status == True:
                if int(headers['status']) in [300, 301, 302, 303, 307]:
                    if headers.has_key('location'):
                        new_url = headers['location']
                        new_url = self.get_new_url(o, new_url)
                        if new_url in self.trace_urls:
                            return True, self.trace_urls

                        url = new_url
                    else:
                        return True, self.trace_urls

                    request = None
                    continue

                elif int(headers['status']) in [200]:
                    if headers['content-type'].startswith("text/html") is False:
                        return True, self.trace_urls

                    if self.current_method == 'HEAD':
                        add_url = False
                        continue
#                        status, request, headers, body = self.trace(url, o.netloc, request)

                    redirect_type, new_url = self.extract_rediection_info_from_body(body)
                    if redirect_type in REDIRECT_LIST:
                        new_url = self.get_new_url(o, new_url)
                        if new_url in self.trace_urls:
                            return True, self.trace_urls

                        url = new_url
                        continue
                    else:
                        return True, self.trace_urls

                elif self.current_method == 'HEAD' and int(headers['status']) in [404]:
                    add_url = False
                    continue;

                return True, self.trace_urls
            else:
                self.append_url(url)
                break

        return True, self.trace_urls

    def get_trace_method(self, first_chance, wanted):
        if wanted is not None:
            return wanted

        if self.TRACE_MODE == FAST_TRACE_MODE and first_chance == True:
            return "HEAD"

        return "GET"

    def need_encode(self, string):
        for ch in string:
            if ord(ch) > 127:
                return True

        return False

    def get_punycode_url(self, url):
        if self.need_encode(url) == False:
            return url

        o = urlparse(url)
        ret_parts = []
        parts = idna.dots.split(o.netloc)

        for part in parts:
            if self.need_encode(part) == True:
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

    def method(self, host):
        if host in GET_ONLY:
            return "GET"

        return None

    def is_not_url(self, url):
        if url.startswith('market://') == True:
            return True

        return False

    def trace(self, url, host, request = None):
        if self.is_not_url(url) == True:
            return False, None, None, None

        first_chance = True
        if request is None:
            request = httplib2.Http()
            if self.use_proxy:
                request.proxy_info = self.get_proxy_info()
            request.follow_redirects = False
        else:
            first_chance = False

        try:
            self.current_method = self.get_trace_method(first_chance, self.method(host))
            resp = request.request(url, self.current_method, headers={'user-agent': USER_AGENT})
            return True, request, resp[0], resp[1]
        except:
            return False, None, None, None

if __name__=='__main__':
    request = TraceUrl()
    print request.go('http://goo.gl/Ib9pjA')
