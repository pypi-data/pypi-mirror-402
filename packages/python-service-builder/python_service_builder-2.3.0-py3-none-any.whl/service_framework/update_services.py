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

import re
from contextlib import closing, suppress
from datetime import datetime

from absl import app

from service_framework.service_finder import ServiceFinder


def main(unused) -> None:
  del unused

  apis = ServiceFinder().find_all()

  lines = []
  with open('service_framework/services.py', 'r') as services:
    while line := services.readline():
      if re.match('\\s+# SERVICE DEFINITIONS:.*', line):
        lines.append(
            f'  # SERVICE DEFINITIONS: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}\n')
      elif re.match('\\s+[A-Z0-9_]+ = ServiceDefinition.*', line):
        continue
      else:
        lines.append(line)

  with closing(open('service_framework/services.py', 'w')) as services:
    services.writelines(lines)
    [services.write(f'  {k} = {v}  # nopep8\n') for k, v in apis.items()]


if __name__ == '__main__':
  with suppress(SystemExit):
    app.run(main)
