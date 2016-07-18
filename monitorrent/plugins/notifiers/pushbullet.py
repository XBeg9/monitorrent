# coding=utf-8
from __future__ import unicode_literals
import requests
from sqlalchemy import Column, String, Integer, ForeignKey
from monitorrent.plugin_managers import register_plugin
from monitorrent.plugins.notifiers import NotificationException, NotifierPlugin, Notifier

PLUGIN_NAME = 'pushbullet'


class PushbulletException(NotificationException):
    pass


class PushbulletSettings(Notifier):
    __tablename__ = "pushbullet_settings"

    id = Column(Integer, ForeignKey('notifiers.id'), primary_key=True)
    access_token = Column(String)

    __mapper_args__ = {
        'polymorphic_identity': PLUGIN_NAME
    }


class PushbulletNotifierPlugin(NotifierPlugin):
    form = [{
        'type': 'row',
        'content': [{
            'type': 'text',
            'label': 'Access Token',
            'model': 'access_token',
            'flex': 50
        }]
    }]

    def get_headers(self, access_token):
        return {
            'Access-Token': access_token
        }

    @property
    def settings_class(self):
        return PushbulletSettings

    def notify(self, header, body, url=None):
        settings = self.get_settings()
        if not settings or not settings.access_token:
            raise PushbulletException(1, "Access Token was not specified")
        type = 'link' if url else 'note'
        parameters = {
            'type': type,
            'title': header,
            'body': body,
            'url': url
        }

        request = requests.post('https://api.pushbullet.com/v2/pushes', data=parameters,
                                headers=self.get_headers(settings.access_token))
        if request.status_code != 200:
            raise PushbulletException(2, 'Failed to send Pushbullet notification')
        return True


register_plugin('notifier', 'pushbullet', PushbulletNotifierPlugin())
