#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib
import json
import re
import web
import settings
import models

debug = web.config.debug = settings.DE_BUG
render = web.template.render(settings.TEMPLATE_DIR,
                             base=settings.BASE_TEMPLATE)
app = web.application(settings.URLS, globals())
DB_R = settings.DATABASES_READ
DB_W = settings.DATABASES_WRITE
db = models.DB(db_read_kwargs=DB_R, db_write_kwargs=DB_W)


class Index(object):
    def GET(self):
        return render.index()
        #return web.input()


class Shorten(object):
    def __init__(self):
        self.db = db

    def add_scheme(self, url):
        """add_scheme(url) -> url

        给 URL 添加 scheme(qq.com -> http://qq.com)
        """
        # 支持的 URL 协议
        scheme2 = re.compile(r'(?i)(?:^[a-z][a-z.+\-]*://)')
        scheme3 = ('git@', 'mailto:', 'javascript:', 'about:', 'opera:',
                   'afp:', 'aim:', 'apt:', 'attachment:', 'bitcoin:',
                   'callto:', 'cid:', 'data:', 'dav:', 'dns:', 'fax:', 'feed:',
                   'gg:', 'go:', 'gtalk:', 'h323:', 'iax:', 'im:', 'itms:',
                   'jar:', 'magnet:', 'maps:', 'message:', 'mid:', 'msnim:',
                   'mvn:', 'news:', 'palm:', 'paparazzi:', 'platform:',
                   'pres:', 'proxy:', 'psyc:', 'query:', 'session:', 'sip:',
                   'sips:', 'skype:', 'sms:', 'spotify:', 'steam:', 'tel:',
                   'things:', 'urn:', 'uuid:', 'view-source:', 'ws:', 'xfire:',
                   'xmpp:', 'ymsgr:', 'doi:',
                   )
        url_lower = url.lower()

        scheme = scheme2.match(url_lower)
        if scheme:
            #url = scheme.group()
            #url += urllib.quote(''.join(url_lower.split('//')[1:]))
            pass
        else:
            for scheme in scheme3:
                url_splits = url_lower.split(scheme)
                if len(url_splits) > 1:
                    #url = scheme + urllib.quote(''.join(url_splits[1:]))
                    break
            else:
                url = 'http://' + url
                #url = 'http://' + urllib.quote(url)
        return url

    def POST(self, get_json=False):
        url = web.input(url='').url.encode('utf8').strip()
        if not url:
            return web.badrequest()

        url = self.add_scheme(url)
        if debug: print repr(url)

        exists = self.db.exist_expand(url)
        if exists:
            shorten = exists.shorten
        else:
            shorten = self.db.add_url(url).shorten
        shorten = web.ctx.homedomain + '/' + shorten
        if get_json:
            web.header('Content-Type', 'application/json')
            return json.dumps({'shorten': shorten, 'expand': url})
        else:
            qr_api = 'http://qrcode101.duapp.com/qr?chl=%s&chs=200x200&chld=M|0'
            shortens = web.storage({'url': shorten,
                                    'qr': qr_api % urllib.quote(shorten),
                                    })
            return render.shorten(shortens)


class Expand(object):
    def __init__(self):
        self.db = db

    def get_expand(self, shorten):
        result = self.db.get_expand(shorten)
        if result:
            return result.expand

    def GET(self, shorten):
        if not shorten:
            return web.seeother('/')
        expand = self.get_expand(shorten)
        print repr(expand)
        if expand:
            return web.redirect(expand)
        else:
            return web.notfound()

    def POST(self):
        shorten = web.input(shorten='').shorten.encode('utf8').strip()
        web.header('Content-Type', 'application/json')
        if shorten and re.match('[a-zA-Z0-9]{5,}$', str(shorten)):
            expand = self.get_expand(shorten)
            if debug: print repr(expand)
            if expand:
                return json.dumps({'shorten': shorten, 'expand': expand})
            else:
                return json.dumps({'shorten': '', 'expand': ''})
        else:
            return json.dumps({'shorten': '', 'expand': ''})


if __name__ == '__main__':
    app.run()
