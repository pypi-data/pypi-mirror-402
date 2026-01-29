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
import unittest

from service_framework import services

SA360_DEFINITION = \
    services.ServiceDefinition(
        service_name='doubleclicksearch',
        discovery_service_url='https://doubleclicksearch.googleapis.com/$discovery/rest?version=v2',
        version='v2')
GMAIL_ARGS = {
    'serviceName': 'gmail',
    'discoveryServiceUrl': 'https://gmail.googleapis.com/$discovery/rest?version=v1',
    'version': 'v1',
}


class ServicesTest(unittest.TestCase):
  def test_valid_service(self):
    self.assertNotEqual(services.Service.CHAT.value, None)

  def test_single_definition(self):
    self.assertEqual(SA360_DEFINITION, services.Service.DOUBLECLICKSEARCH.definition)
