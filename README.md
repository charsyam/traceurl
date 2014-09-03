traceurl
========

Tracing url address
 * follow 30x 
 * follow meta tag
 * can't follow javascript location change
 * support http_proxy

install traceurl
 * pip install traceurl

example
```python
import traceurl

request = traceurl.TraceUrl()
request.go('http://charsyam.wordpress.com')
```

```python
import traceurl

request = traceurl.TraceUrl()
request.use_proxy = True
request.go('http://charsyam.wordpress.com')
```

```python
import traceurl

request = traceurl.TraceUrl()
request.set_proxy_info('proxy.iwilab.com', 8088)
request.go('http://charsyam.wordpress.com')
```
