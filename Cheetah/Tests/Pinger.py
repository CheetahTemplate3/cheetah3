from __future__ import absolute_import

from Cheetah.Template import Template


class Pinger(Template):
    def ping(self):
        return 'pong'
