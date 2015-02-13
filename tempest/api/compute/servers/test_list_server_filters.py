# Copyright 2012 OpenStack Foundation
# All Rights Reserved.
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

from tempest_lib import decorators
from tempest_lib import exceptions as lib_exc

from tempest.api.compute import base
from tempest.api import utils
from tempest.common.utils import data_utils
from tempest import config
from tempest import test

CONF = config.CONF


class ListServerFiltersTestJSON(base.BaseV2ComputeTest):

    @classmethod
    def resource_setup(cls):
        cls.set_network_resources(network=True, subnet=True, dhcp=True)
        super(ListServerFiltersTestJSON, cls).resource_setup()
        cls.client = cls.servers_client

        # Check to see if the alternate image ref actually exists...
        images_client = cls.images_client
        images = images_client.list_images()

        if cls.image_ref != cls.image_ref_alt and \
            any([image for image in images
                 if image['id'] == cls.image_ref_alt]):
            cls.multiple_images = True
        else:
            cls.image_ref_alt = cls.image_ref

        # Do some sanity checks here. If one of the images does
        # not exist, fail early since the tests won't work...
        try:
            cls.images_client.get_image(cls.image_ref)
        except lib_exc.NotFound:
            raise RuntimeError("Image %s (image_ref) was not found!" %
                               cls.image_ref)

        try:
            cls.images_client.get_image(cls.image_ref_alt)
        except lib_exc.NotFound:
            raise RuntimeError("Image %s (image_ref_alt) was not found!" %
                               cls.image_ref_alt)

        cls.s1_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s1 = cls.create_test_server(name=cls.s1_name,
                                        wait_until='ACTIVE')

        cls.s2_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s2 = cls.create_test_server(name=cls.s2_name,
                                        image_id=cls.image_ref_alt,
                                        wait_until='ACTIVE')

        cls.s3_name = data_utils.rand_name(cls.__name__ + '-instance')
        cls.s3 = cls.create_test_server(name=cls.s3_name,
                                        flavor=cls.flavor_ref_alt,
                                        wait_until='ACTIVE')

        cls.fixed_network_name = CONF.compute.fixed_network_name
        if CONF.service_available.neutron:
            if hasattr(cls.isolated_creds, 'get_primary_network'):
                network = cls.isolated_creds.get_primary_network()
                cls.fixed_network_name = network['name']

    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    @test.attr(type='gate')
    def test_list_servers_filter_by_image(self):
        # Filter the list of servers by image
        params = {'image': self.image_ref}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    def test_list_servers_filter_by_flavor(self):
        # Filter the list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertNotIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    def test_list_servers_filter_by_server_name(self):
        # Filter the list of servers by server name
        params = {'name': self.s1_name}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    def test_list_servers_filter_by_server_status(self):
        # Filter the list of servers by server status
        params = {'status': 'active'}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    def test_list_servers_filter_by_shutoff_status(self):
        # Filter the list of servers by server shutoff status
        params = {'status': 'shutoff'}
        self.client.stop(self.s1['id'])
        self.client.wait_for_server_status(self.s1['id'],
                                           'SHUTOFF')
        resp, body = self.client.list_servers(params)
        self.client.start(self.s1['id'])
        self.client.wait_for_server_status(self.s1['id'],
                                           'ACTIVE')
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    def test_list_servers_filter_by_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 1}
        resp, servers = self.client.list_servers(params)
        self.assertEqual(1, len([x for x in servers['servers'] if 'id' in x]))

    @test.attr(type='gate')
    def test_list_servers_filter_by_zero_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 0}
        resp, servers = self.client.list_servers(params)
        self.assertEqual(0, len(servers['servers']))

    @test.attr(type='gate')
    def test_list_servers_filter_by_exceed_limit(self):
        # Verify only the expected number of servers are returned
        params = {'limit': 100000}
        resp, servers = self.client.list_servers(params)
        resp, all_servers = self.client.list_servers()
        self.assertEqual(len([x for x in all_servers['servers'] if 'id' in x]),
                         len([x for x in servers['servers'] if 'id' in x]))

    @utils.skip_unless_attr('multiple_images', 'Only one image found')
    @test.attr(type='gate')
    def test_list_servers_detailed_filter_by_image(self):
        # Filter the detailed list of servers by image
        params = {'image': self.image_ref}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    def test_list_servers_detailed_filter_by_flavor(self):
        # Filter the detailed list of servers by flavor
        params = {'flavor': self.flavor_ref_alt}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertNotIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertNotIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))

    @test.attr(type='gate')
    def test_list_servers_detailed_filter_by_server_name(self):
        # Filter the detailed list of servers by server name
        params = {'name': self.s1_name}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    def test_list_servers_detailed_filter_by_server_status(self):
        # Filter the detailed list of servers by server status
        params = {'status': 'active'}
        resp, body = self.client.list_servers_with_detail(params)
        servers = body['servers']
        test_ids = [s['id'] for s in (self.s1, self.s2, self.s3)]

        self.assertIn(self.s1['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s2['id'], map(lambda x: x['id'], servers))
        self.assertIn(self.s3['id'], map(lambda x: x['id'], servers))
        self.assertEqual(['ACTIVE'] * 3, [x['status'] for x in servers
                                          if x['id'] in test_ids])

    @test.attr(type='gate')
    def test_list_servers_filtered_by_name_wildcard(self):
        # List all servers that contains '-instance' in name
        params = {'name': '-instance'}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

        # Let's take random part of name and try to search it
        part_name = self.s1_name[6:-1]

        params = {'name': part_name}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    def test_list_servers_filtered_by_name_regex(self):
        # list of regex that should match s1, s2 and s3
        regexes = ['^.*\-instance\-[0-9]+$', '^.*\-instance\-.*$']
        for regex in regexes:
            params = {'name': regex}
            resp, body = self.client.list_servers(params)
            servers = body['servers']

            self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
            self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
            self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

        # Let's take random part of name and try to search it
        part_name = self.s1_name[-10:]

        params = {'name': part_name}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    def test_list_servers_filtered_by_ip(self):
        # Filter servers by ip
        # Here should be listed 1 server
        self.s1 = self.client.get_server(self.s1['id'])
        ip = self.s1['addresses'][self.fixed_network_name][0]['addr']
        params = {'ip': ip}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertNotIn(self.s3_name, map(lambda x: x['name'], servers))

    @decorators.skip_because(bug="1182883",
                             condition=CONF.service_available.neutron)
    @test.attr(type='gate')
    def test_list_servers_filtered_by_ip_regex(self):
        # Filter servers by regex ip
        # List all servers filtered by part of ip address.
        # Here should be listed all servers
        self.s1 = self.client.get_server(self.s1['id'])
        ip = self.s1['addresses'][self.fixed_network_name][0]['addr'][0:-3]
        params = {'ip': ip}
        resp, body = self.client.list_servers(params)
        servers = body['servers']

        self.assertIn(self.s1_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s2_name, map(lambda x: x['name'], servers))
        self.assertIn(self.s3_name, map(lambda x: x['name'], servers))

    @test.attr(type='gate')
    def test_list_servers_detailed_limit_results(self):
        # Verify only the expected number of detailed results are returned
        params = {'limit': 1}
        resp, servers = self.client.list_servers_with_detail(params)
        self.assertEqual(1, len(servers['servers']))
