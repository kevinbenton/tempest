# Copyright 2015 NEC Corporation.  All rights reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

node = {
    'type': 'object',
    'properties': {
        'id': {'type': 'string'},
        'interfaces': {'type': 'array'},
        'host': {'type': 'string'},
        'task_state': {'type': ['string', 'null']},
        'cpus': {'type': 'integer'},
        'memory_mb': {'type': 'integer'},
        'disk_gb': {'type': 'integer'},
    },
    'required': ['id', 'interfaces', 'host', 'task_state', 'cpus', 'memory_mb',
                 'disk_gb']
}

list_baremetal_nodes = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'nodes': {
                'type': 'array',
                'items': node
            }
        },
        'required': ['nodes']
    }
}

get_baremetal_node = {
    'status_code': [200],
    'response_body': {
        'type': 'object',
        'properties': {
            'node': node
        },
        'required': ['node']
    }
}
