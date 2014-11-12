#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#

python_binary(
  name = 'aurora_rest',
  entry_point = 'apache.aurora.rest.bin.server:proxy_main',
  dependencies = [
    ':aurora_rest_lib'
  ]
)

python_library(
  name = 'aurora_rest_lib',
  sources = [ 'server.py' ],
  dependencies = [
    'src/main/python/apache/aurora/rest/3rdparty/python:tornado',
    '3rdparty/python:twitter.common.app',
    '3rdparty/python:twitter.common.log',
    'src/main/python/apache/aurora/rest/apps',
    'src/main/python/apache/aurora/rest/executors',
  ]
)
