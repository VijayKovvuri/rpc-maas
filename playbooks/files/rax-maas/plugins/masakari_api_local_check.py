#!/usr/bin/env python3

# Copyright 2014, Rackspace US, Inc.
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

import argparse
import collections
import ipaddr

from maas_common import generate_local_endpoint
from maas_common import get_openstack_client
from maas_common import metric
from maas_common import metric_bool
from maas_common import print_output
from maas_common import status_err
from maas_common import status_ok
from requests import exceptions as exc



def check(args):
    masakari = get_openstack_client('ha')

    try:
        masakari_local_endpoint = generate_local_endpoint(
            str(masakari.get_endpoint()), args.ip, args.port,
            args.protocol, '/segments'
        )
        resp = masakari.session.get(masakari_local_endpoint, timeout=180)

    except (exc.ConnectionError, exc.HTTPError, exc.Timeout):
        is_up = False
        metric_bool('client_success', False, m_name='maas_masakari')
    # Any other exception presumably isn't an API error
    except Exception as e:
        metric_bool('client_success', False, m_name='maas_masakari')
        status_err(str(e), m_name='maas_masakari')
    else:
        is_up = resp.ok
        milliseconds = resp.elapsed.total_seconds() * 1000
        metric_bool('client_success', True, m_name='maas_masakari')

    status_ok(m_name='maas_masakari')
    metric_bool('masakari_api_local_status', is_up, m_name='maas_masakari')

    # only want to send other metrics if api is up
    if is_up:
        metric('masakari_api_local_response_time',
               'double',
               '%.3f' % milliseconds,
               'ms')


def main(args):
    check(args)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description='Check Masakari API against local or remote address')
    parser.add_argument('ip', nargs='?',
                        type=ipaddr.IPv4Address,
                        help='Optional Masakari API server address')
    parser.add_argument('--telegraf-output',
                        action='store_true',
                        default=False,
                        help='Set the output format to telegraf')
    parser.add_argument('--port',
                        action='store',
                        default='15868',
                        help='Port to use for Masakari API check')
    parser.add_argument('--protocol',
                        action='store',
                        default='http',
                        help='Protocol to use for local Masakari API')
    args = parser.parse_args()
    with print_output(print_telegraf=args.telegraf_output):
        main(args)
