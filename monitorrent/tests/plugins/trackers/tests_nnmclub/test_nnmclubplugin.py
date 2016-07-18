# coding=utf-8
from __future__ import unicode_literals
from mock import patch
from monitorrent.plugins.trackers import LoginResult, TrackerSettings
from monitorrent.plugins.trackers.nnmclub import NnmClubPlugin, NnmClubTopic, NnmClubLoginFailedException
from monitorrent.tests import DbTestCase, use_vcr
from monitorrent.tests.plugins.trackers.tests_nnmclub.nnmclub_helper import NnmClubTrackerHelper

#helper = NnmClubTrackerHelper.login('login@gmail.com', 'p@$$w0rd')
helper = NnmClubTrackerHelper()


class FreeTorrentsPluginTest(DbTestCase):
    def setUp(self):
        super(FreeTorrentsPluginTest, self).setUp()
        plugin_settings = TrackerSettings(10)
        self.plugin = NnmClubPlugin()
        self.plugin.init(plugin_settings)
        self.urls_to_check = [
            "http://nnmclub.to/forum/viewtopic.php?t=409969",
            "http://nnm-club.me/forum/viewtopic.php?t=409969"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.plugin.can_parse_url(url))

        bad_urls = [
            "http://nnmclub.ty/forum/viewtopic.php?t=1",
            "http://not-nnmclub.to/forum/viewtopic.php?t=409969"
        ]
        for url in bad_urls:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.plugin.parse_url(self.urls_to_check[0])
        self.assertEqual(parsed_url['original_name'], 'Легенда о Тиле (1976) DVDRip')

    @use_vcr
    def test_parse_not_found_url(self):
        parsed_url = self.plugin.parse_url('http://nnmclub.to/forum/viewtopic.php?t=1')
        self.assertIsNone(parsed_url)

    @helper.use_vcr()
    def test_login_verify(self):
        self.assertFalse(self.plugin.verify())
        self.assertEqual(self.plugin.login(), LoginResult.CredentialsNotSpecified)

        credentials = {'username': '', 'password': ''}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.CredentialsNotSpecified)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': helper.fake_username, 'password': helper.fake_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': helper.real_username, 'password': helper.real_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Ok)
        self.assertTrue(self.plugin.verify())

    def test_login_failed_exceptions_1(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=NnmClubLoginFailedException(1, 'Invalid login or password')):
            credentials = {'username': helper.real_username, 'password': helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)

    def test_login_failed_exceptions_173(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=NnmClubLoginFailedException(173, 'Invalid login or password')):
            credentials = {'username': helper.real_username, 'password': helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_login_unexpected_exceptions(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=Exception):
            credentials = {'username': helper.real_username, 'password': helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    @use_vcr
    def test_prepare_request(self):
        self.plugin.tracker.sid = helper.real_sid
        url = self.urls_to_check[0]
        request = self.plugin._prepare_request(NnmClubTopic(url=url))
        self.assertIsNotNone(request)
        self.assertEqual(request.url, 'http://nnmclub.to/forum/download.php?id=370059')
