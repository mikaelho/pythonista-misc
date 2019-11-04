#coding: utf-8
import bottle, threading, requests, functools

def wrap(obj, port=8080, quiet=True):
  server = MyWSGIRefServer(port=port)
  app = Proxy()
  
  threading.Thread(group=None, target=app.run, name=None, args=(), kwargs={'server': server, 'quiet': quiet}).start()
  

class _MyWSGIRefServer(bottle.ServerAdapter):
  server = None

  def run(self, handler):
    from wsgiref.simple_server import make_server, WSGIRequestHandler
    if self.quiet:
      class QuietHandler(WSGIRequestHandler):
        def log_request(*args, **kw): pass
      self.options['handler_class'] = QuietHandler
    self.server = make_server(self.host, self.port, handler, **self.options)
    self.server.serve_forever()

  def stop(self):
    self.server.shutdown()

        
class _ProxyApp(bottle.Bottle):
  
  def __init__(self, *args, **kwargs):
    pass

        
class _ProxyClient:
  
  def __init__(self, obj):
    self._obj = obj
    
  def call_method(self, name, func, *args, **kwargs):
    return func(*args, **kwargs)
  
  def __getattr__(self, key, go=object.__getattribute__):
    target = getattr(go(self, '_obj'), key)
    return functools.partial(go(self, 'call_method'), key, target)
    
if __name__ == '__main__':
  l = ['a']
  pl = _ProxyClient(l)
  pl.append('b')
  print(l)
  
  

  
