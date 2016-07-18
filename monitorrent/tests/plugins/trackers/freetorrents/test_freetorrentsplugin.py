# coding=utf-8
from __future__ import unicode_literals
from mock import patch
from monitorrent.plugins.trackers import LoginResult, TrackerSettings
from monitorrent.plugins.trackers.freetorrents import FreeTorrentsOrgPlugin, FreeTorrentsOrgTopic, \
    FreeTorrentsLoginFailedException
from monitorrent.tests import DbTestCase, use_vcr
from monitorrent.tests.plugins.trackers.freetorrents.freetorrentstracker_helper import FreeTorrentsHelper


class FreeTorrentsPluginTest(DbTestCase):
    def setUp(self):
        super(FreeTorrentsPluginTest, self).setUp()
        plugin_settings = TrackerSettings(10)
        self.plugin = FreeTorrentsOrgPlugin()
        self.plugin.init(plugin_settings)
        self.helper = FreeTorrentsHelper()
        self.urls_to_check = [
            "http://free-torrents.org/forum/viewtopic.php?t=207456",
            "http://www.free-torrents.org/forum/viewtopic.php?t=207456"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.plugin.can_parse_url(url))

        bad_urls = [
            "http://free-torrents.com/forum/viewtopic.php?t=207456",
            "http://beltracker.org/forum/viewtopic.php?t=5062041"
        ]
        for url in bad_urls:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.plugin.parse_url("http://free-torrents.org/forum/viewtopic.php?t=207456")
        self.assertEqual(
            parsed_url['original_name'], 'Мистер Робот / Mr. Robot [Сезон 1 (1-9 из 10)]'
                                         '[2015, Драма, криминал, WEB-DLRip] [MVO (LostFilm)]')

    @use_vcr
    def test_parse_not_found_url(self):
        parsed_url = self.plugin.parse_url('http://free-torrent.org/forum/viewtopic.php?t=312015')
        self.assertIsNone(parsed_url)

    @use_vcr
    def test_login_verify(self):
        self.assertFalse(self.plugin.verify())
        self.assertEqual(self.plugin.login(), LoginResult.CredentialsNotSpecified)

        credentials = {'username': '', 'password': ''}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.CredentialsNotSpecified)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': self.helper.fake_login, 'password': self.helper.fake_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)
        self.assertFalse(self.plugin.verify())

        credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
        self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Ok)
        self.assertTrue(self.plugin.verify())

    def test_login_failed_exceptions_1(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=FreeTorrentsLoginFailedException(1, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)

    def test_login_failed_exceptions_173(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=FreeTorrentsLoginFailedException(173, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_login_unexpected_exceptions(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=Exception):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    @use_vcr
    def test_prepare_request(self):
        self.plugin.tracker.bbe_data = 'bbe-data'
        url = 'http://free-torrents.org/forum/viewtopic.php?t=207456'
        request = self.plugin._prepare_request(FreeTorrentsOrgTopic(url=url))
        self.assertIsNotNone(request)
        self.assertEqual(request.headers['referer'], url)
        self.assertEqual(request.headers['host'], 'dl.free-torrents.org')
        self.assertEqual(request.url, 'http://bRikuAgOaPat.com/RikuAgOaPa')
