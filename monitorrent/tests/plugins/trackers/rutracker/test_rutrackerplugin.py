# coding=utf-8
from __future__ import unicode_literals
from mock import patch
from monitorrent.plugins.trackers import LoginResult, TrackerSettings
from monitorrent.plugins.trackers.rutracker import RutrackerPlugin, RutrackerLoginFailedException, RutrackerTopic
from monitorrent.tests import use_vcr, DbTestCase
from monitorrent.tests.plugins.trackers.rutracker.rutracker_helper import RutrackerHelper


class RutrackerPluginTest(DbTestCase):
    def setUp(self):
        super(RutrackerPluginTest, self).setUp()
        self.tracker_settings = TrackerSettings(10)
        self.plugin = RutrackerPlugin()
        self.plugin.init(self.tracker_settings)
        self.helper = RutrackerHelper()
        self.urls_to_check = [
            "http://rutracker.org/forum/viewtopic.php?t=5062041",
            "http://www.rutracker.org/forum/viewtopic.php?t=5062041"
        ]

    def test_can_parse_url(self):
        for url in self.urls_to_check:
            self.assertTrue(self.plugin.can_parse_url(url))

        bad_urls = [
            "http://rutracker.com/forum/viewtopic.php?t=5062041",
            "http://beltracker.org/forum/viewtopic.php?t=5062041"
        ]
        for url in bad_urls:
            self.assertFalse(self.plugin.can_parse_url(url))

    @use_vcr
    def test_parse_url(self):
        parsed_url = self.plugin.parse_url("http://rutracker.org/forum/viewtopic.php?t=5062041")
        self.assertEqual(
            parsed_url['original_name'], 'Бeзyмный Мaкс: Дoрoга яpоcти в 3Д / Mаd Mаx: Furу Rоad 3D '
                                         '(Джoрдж Миллер / Geоrge Millеr) [2015, Боевик, Фантастика, '
                                         'Приключения, BDrip-AVC] Half OverUnder / Вертикальная анаморфная стереопара')

    @use_vcr
    def test_parse_not_found_url(self):
        parsed_url = self.plugin.parse_url('http://rutracker.org/forum/viewtopic.php?t=5018612')
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
                          side_effect=RutrackerLoginFailedException(1, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.IncorrentLoginPassword)

    def test_login_failed_exceptions_173(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login',
                          side_effect=RutrackerLoginFailedException(173, 'Invalid login or password')):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_login_unexpected_exceptions(self):
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'login', side_effect=Exception):
            credentials = {'username': self.helper.real_login, 'password': self.helper.real_password}
            self.assertEqual(self.plugin.update_credentials(credentials), LoginResult.Unknown)

    def test_prepare_request(self):
        cookies = {'bb_data': '1-4301487-ZdJuaHIfHpaJiVn8VPKU-0-1461694123-1461698647-4135149312-1'}
        # noinspection PyUnresolvedReferences
        with patch.object(self.plugin.tracker, 'get_cookies', result=cookies):
            url = 'http://rutracker.org/forum/viewtopic.php?t=5062041'
            request = self.plugin._prepare_request(RutrackerTopic(url=url))
            self.assertIsNotNone(request)
            self.assertEqual(request.headers['referer'], url)
            self.assertEqual(request.headers['host'], 'dl.rutracker.org')
            self.assertEqual(request.url, 'http://dl.rutracker.org/forum/dl.php?t=5062041')
