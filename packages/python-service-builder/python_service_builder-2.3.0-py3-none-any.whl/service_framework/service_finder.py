# Copyright 2022 David Harcombe
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     https://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import urllib.parse
import urllib.request
from collections import namedtuple
from contextlib import closing
from typing import Mapping
from urllib.request import urlopen

from service_framework import ServiceDefinition


class ServiceFinder(object):
  """ServiceFinder
  """
  def __call__(cls, value, *args, **kwargs) -> ServiceDefinition:
    """What to do when the `ServiceFinder` is invoked

    Usage:
        ```
        finder = ServiceFinder()
        finder('CHAT')
        ```

    Args:
        value (str): the name of the service to find

    Raises:
        Exception: No valid Google service of this name exists

    Returns:
        ServiceDefinition: the service definition
    """
    if api := ServiceFinder.find(name=value.lower()):
      return api[value.upper()]

    else:
      raise Exception(f'No Google service found with the name {value.upper()}')

  @classmethod
  def find_all(cls) -> Mapping[str, ServiceDefinition]:
    return cls.find(None)

  @classmethod
  def find(cls, name: str) -> Mapping[str, ServiceDefinition]:
    Components = namedtuple(
        typename='Components',
        field_names=['scheme', 'netloc', 'url', 'path', 'query', 'fragment']
    )

    apis = {}

    parameters = {'preferred': 'true'}
    if name:
      parameters |= {'name': name}

    url = urllib.parse.urlunparse(
        Components(
            scheme='https',
            netloc='www.googleapis.com',
            query=urllib.parse.urlencode(parameters),
            path='',
            url='/discovery/v1/apis',
            fragment=None
        )
    )

    r = urllib.request.Request(url)
    with closing(urlopen(r)) as _api_list:
      api_list = json.loads(_api_list.read())
      if items := api_list.get('items', None):
        for api in items:
          apis[api['name'].upper()] = ServiceDefinition(
              api['name'], api['version'], api['discoveryRestUrl'])

    return apis
