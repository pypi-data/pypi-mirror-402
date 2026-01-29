from furl import furl

from .. import core


class WebPing(core.WebPing):
    def __init__(self, *, api_key: str = '', monitor_key: str):
        # TODO: actually use the api_key URL version and make sure it works with cronitor.  There
        # are unit tests but I've not actually used the api_key version live yet.
        self.base_url = furl('https://cronitor.link/')
        if api_key:
            self.base_url /= f'p/{api_key}'
        if monitor_key:
            self.base_url /= monitor_key

    def pre_url(self):
        return (self.base_url / 'run').url

    def post_ok_url(self):
        return (self.base_url / 'complete').url

    def post_fail_url(self):
        return (self.base_url / 'fail').url
