traceurl
========

Tracing url address
 * follow 30x 
 * follow meta tag
 * can't follow javascript location change

install traceurl
 * pip install traceurl

example
```python
import traceurl

request = traceurl.TraceUrl()
request.go('http://charsyam.wordpress.com')
```
