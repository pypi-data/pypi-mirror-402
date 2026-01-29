from . import Application
from aiohttp import web
from aridity.config import Config
from datetime import datetime
from diapyr import types
from splut.actor import Spawn
from urllib.parse import urlencode
from urllib.request import urlopen
import logging

log = logging.getLogger(__name__)

class SiteMeter:

    class Worker:

        def __init__(self, url, basedata):
            self.url = url
            self.basedata = basedata

        def send(self, info):
            with urlopen(self.url, urlencode(dict(self.basedata, info = info)).encode('ascii')):
                pass

    @types(Config, Spawn)
    def __init__(self, config, spawn):
        c = config.sitemeter
        args = c.url, dict(env = c.env, site = c.site)
        self.actor = spawn(*(self.Worker(*args) for _ in range(c.workers)))

    @web.middleware
    async def middleware(self, request, handler):
        hitinfo = f"{request.method} {request.path_qs} {request.headers.get('Referer')} {request.headers.get('X-Forwarded-For')} {request.headers.get('User-Agent')}"
        log.debug(hitinfo)
        self.actor.send(f"{datetime.now()} {hitinfo}").andforget(log)
        return await handler(request)

class AIOApplication(web.Application, Application): pass
