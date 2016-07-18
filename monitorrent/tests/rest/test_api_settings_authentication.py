from __future__ import unicode_literals
import json
import falcon
from mock import MagicMock
from ddt import ddt, data
from monitorrent.tests import RestTestBase
from monitorrent.rest.settings_authentication import SettingsAuthentication
from monitorrent.settings_manager import SettingsManager


@ddt
class SettingsAuthenticationTest(RestTestBase):
    @data(True, False)
    def test_is_authentication_enabled(self, value):
        settings_manager = SettingsManager()
        settings_manager.get_is_authentication_enabled = MagicMock(return_value=value)
        settings_authentication_resource = SettingsAuthentication(settings_manager)
        self.api.add_route('/api/settings/authentication', settings_authentication_resource)

        body = self.simulate_request("/api/settings/authentication", decode='utf-8')

        self.assertEqual(self.srmock.status, falcon.HTTP_OK)
        self.assertTrue('application/json' in self.srmock.headers_dict['Content-Type'])

        result = json.loads(body)

        self.assertEqual(result, {'is_authentication_enabled': value})

    @data(True, False)
    def test_set_is_authentication_enabled(self, value):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value='monitorrent')
        settings_manager.set_is_authentication_enabled = MagicMock()
        settings_authentication_resource = SettingsAuthentication(settings_manager)
        self.api.add_route('/api/settings/authentication', settings_authentication_resource)

        request = {'password': 'monitorrent', 'is_authentication_enabled': value}
        self.simulate_request("/api/settings/authentication", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_NO_CONTENT)

    @data(True, False)
    def test_set_is_authentication_enabled_wrong_password(self, value):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value='monitorrent')
        settings_manager.set_is_authentication_enabled = MagicMock()
        settings_authentication_resource = SettingsAuthentication(settings_manager)
        self.api.add_route('/api/settings/authentication', settings_authentication_resource)

        request = {'password': 'MonITorrenT', 'is_authentication_enabled': value}
        self.simulate_request("/api/settings/authentication", method="PUT", body=json.dumps(request))

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)

    @data({'password': 'monitorrent'},
          {'is_authentication_enabled': True},
          {'password': 'monitorrent', 'is_authentication_enabled': 'string'},
          {'wrong_param1': 'param1', 'wrong_param2': 'param2'},
          None)
    def test_set_is_authentication_enabled_bad_request(self, body):
        settings_manager = SettingsManager()
        settings_manager.get_password = MagicMock(return_value='monitorrent')
        settings_manager.set_is_authentication_enabled = MagicMock()
        settings_authentication_resource = SettingsAuthentication(settings_manager)
        self.api.add_route('/api/settings/authentication', settings_authentication_resource)

        self.simulate_request("/api/settings/authentication", method="PUT", body=json.dumps(body) if body else None)

        self.assertEqual(self.srmock.status, falcon.HTTP_BAD_REQUEST)
