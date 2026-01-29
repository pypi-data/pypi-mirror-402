from .util import canon, patch
from aiohttp import web
from aridity.model import Resource
from email.message import EmailMessage
from foyndation import Forkable, singleton, solo
from multidict import CIMultiDict
from werkzeug.http import _hop_by_hop_headers

class Application: pass

class Headers(Forkable):

    @singleton
    class Null:

        def safedict(self):
            return {}

    @classmethod
    def fromresponse(cls, response):
        md = CIMultiDict()
        for k, x in response.getheaders():
            if canon(k) not in _hop_by_hop_headers:
                md.add(k, x)
        return cls(md)

    def __init__(self, md):
        self.md = md

    def contentcharset(self):
        msg = EmailMessage()
        msg['Content-Type'], = self.md.getall('content-type')
        return msg.get_content_charset()

    def copy(self):
        return self._of(self.md.copy())

    def getlist(self, key):
        return self.md.getall(key, [])

    def safedict(self):
        canonkeys = set()
        d = {}
        for realk, v in self.md.items():
            canonk = canon(realk)
            assert canonk not in canonkeys
            canonkeys.add(canonk)
            d[realk] = v
        return d

    def uniqornone(self, key):
        if vals := self.getlist(key):
            return solo(vals)

@patch(Resource)
def htmlresponse(resource, cc, **kwargs):
    return web.Response(content_type = 'text/html', text = resource.processtemplate(cc.scope).textvalue, **kwargs)
