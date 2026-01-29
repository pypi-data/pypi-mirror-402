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
import dataclasses
import unittest
from dataclasses import Field, dataclass

from dataclasses_json import dataclass_json

from service_framework import camel_field


class CamelFieldTest(unittest.TestCase):
  def test_base_camel_field(self) -> None:
    @dataclass_json
    @dataclass
    class Base(object):
      _field: str = camel_field()

    base = Base()
    base._field = 'foo'

    f: Field = base.__dataclass_fields__.get('_field')
    self.assertIsNone(f.default)
    self.assertTrue(isinstance(f.default_factory, dataclasses._MISSING_TYPE))
    self.assertIsNotNone(f.metadata)
    self.assertIn('letter_case', f.metadata['dataclasses_json'])
    self.assertIn('exclude', f.metadata['dataclasses_json'])

  def test_field_with_metadata_removed(self) -> None:
    @dataclass_json
    @dataclass
    class Base(object):
      _field: str = camel_field(exclude=None)

    base = Base()
    base._field = 'foo'

    f = base.__dataclass_fields__.get('_field')
    self.assertIsNone(f.default)
    self.assertTrue(isinstance(f.default_factory, dataclasses._MISSING_TYPE))
    self.assertIsNotNone(f.metadata)
    self.assertIn('letter_case', f.metadata['dataclasses_json'])
    self.assertNotIn('exclude', f.metadata['dataclasses_json'])

  def test_field_with_metadata_edited(self) -> None:
    @dataclass_json
    @dataclass
    class Base(object):
      _field: str = camel_field(exclude=True)

    base = Base()
    base._field = 'foo'

    f = base.__dataclass_fields__.get('_field')
    self.assertIsNone(f.default)
    self.assertTrue(isinstance(f.default_factory, dataclasses._MISSING_TYPE))
    self.assertIsNotNone(f.metadata)
    self.assertIn('letter_case', f.metadata['dataclasses_json'])
    self.assertTrue(f.metadata['dataclasses_json']['exclude'])

  def test_field_with_default(self) -> None:
    @dataclass_json
    @dataclass
    class Base(object):
      _field: str = camel_field(default='Princess Buttercup')

    base = Base()

    f = base.__dataclass_fields__.get('_field')
    self.assertIsNotNone(f.default)
    self.assertTrue(isinstance(f.default_factory, dataclasses._MISSING_TYPE))
    self.assertEqual(base._field, 'Princess Buttercup')

  def test_field_with_no_value_is_excluded(self) -> None:
    @dataclass_json
    @dataclass
    class Base(object):
      _field: str = camel_field()
      _other_field: str = camel_field()

    base = Base()
    base._field = None
    base._other_field = 'foo'

    print(base.to_json())

    f = base.__dataclass_fields__.get('_field')
    self.assertIsNone(f.default)
    self.assertTrue(isinstance(f.default_factory, dataclasses._MISSING_TYPE))
    self.assertIsNotNone(f.metadata)
    self.assertIn('letter_case', f.metadata['dataclasses_json'])
    self.assertTrue(f.metadata['dataclasses_json']['exclude'])
