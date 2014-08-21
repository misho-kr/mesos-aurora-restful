
python_library(
  name = 'web',
  sources = [ 'application.py', 'application_async.py',
              'coroutine_executor.py', 'mt_executor.py', 'mp_executor.py',
              'external_executor.py', 'internal_executor.py' ],
  dependencies = [
    pants('3rdparty/python:tornado'),
    pants('3rdparty/python:twitter.common.app'),
    pants('3rdparty/python:twitter.common.log'),
    pants('src/main/python/apache/aurora/client/commands:all'),
    pants('src/main/python/apache/aurora/client:base'),
  ]
)
