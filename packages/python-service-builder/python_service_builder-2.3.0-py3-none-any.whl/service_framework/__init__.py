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
from typing import Any, Mapping

import dataclasses_json


def metadata(base: Mapping[str, Any], **custom) -> Mapping[str, Any]:
  """Merges properties into the metadata and returns the merged result.

  Args:
      base (Mapping[str, Any]): the existing metadata

  Returns:
      Mapping[str, Any]: the merged result
  """
  for key in custom:
    if not custom[key] and key in base:
      del base[key]

    elif custom[key]:
      base.update({key: custom[key]})

  return base


def field(default: Any = None,
          default_factory: Any = None, **kwargs) -> dataclasses.field:
  """A generic dataclass field.

  Only one of `default` or `default_factory` should be supplied. If both are
  given, `default_factory` will take precedence.

  Args:
      default (Any, optional): the default field value. Defaults to None.
      default_factory (Any, optional): the default field factory. Defaults to None.
      **kwargs (Any...): any extra metadata args.

  Returns:
      dataclasses.field: the field
  """
  base = {
      'exclude': lambda x: not x
  }

  if default_factory:
    f = dataclasses.field(default_factory=default_factory,
                          metadata=dataclasses_json.config(
                              **metadata(base=base, **kwargs)))
  else:
    f = dataclasses.field(default=default,
                          metadata=dataclasses_json.config(
                              **metadata(base=base, **kwargs)))

  return f


def snake_field(default: Any = None,
                default_factory: Any = None, **kwargs) -> dataclasses.field:
  """Defines a generic dataclass field with a `camelCase` rendered name.

  Args:
      default (Any, optional): the default field value. Defaults to None.
      default_factory (Any, optional): the default field factory. Defaults to None.
      **kwargs (Any...): any extra metadata args.

  Returns:
      dataclasses.field: the field
  """
  return field(default=default, default_factory=default_factory,
               letter_case=dataclasses_json.LetterCase.SNAKE, **kwargs)


def camel_field(default: Any = None,
                default_factory: Any = None, **kwargs) -> dataclasses.field:
  """Defines a generic dataclass field with a `camelCase` rendered name.

  Args:
      default (Any, optional): the default field value. Defaults to None.
      default_factory (Any, optional): the default field factory. Defaults to None.
      **kwargs (Any...): any extra metadata args.

  Returns:
      dataclasses.field: the field
  """
  return field(default=default, default_factory=default_factory,
               letter_case=dataclasses_json.LetterCase.CAMEL, **kwargs)


@dataclasses_json.dataclass_json
@dataclasses.dataclass
class ServiceDefinition(object):
  """Defines a Google Service for the builder."""
  service_name: str = camel_field()
  version: str = camel_field()
  discovery_service_url: str = camel_field()
