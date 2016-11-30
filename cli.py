"""
This is library and CLI utils for controlling RV6688BCM router
It is required python 3.5 or higher and requests library (due to Digest HTTP auth)

The MIT License (MIT)
Copyright (c) 2016 Baryshnikov Alexander <dev@baryshnikov.net>

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to
permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions
of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""
import click
import requests
from requests.auth import HTTPDigestAuth


class Context:
    def __init__(self, ip, user, password):
        self.auth = HTTPDigestAuth(user, password)
        self.url = "http://" + ip
        self.ip = ip

    def getter(self, url):
        resp = requests.get(self.url + url, auth=self.auth)
        assert resp.status_code == 200, resp.text
        return resp

    def poster(self, url, data, referer=""):
        resp = requests.post(self.url + url, data=data, auth=self.auth,
                             headers={
                                 'Referer': self.url + referer
                             })
        t = resp.text
        assert resp.status_code == 200, t


@click.group()
@click.option('--ip', default="", help='Router IP')
@click.option('--user', default="admin", help='Login name')
@click.option('--password', default="admin", help='Password')
@click.pass_context
def cli(ctx, ip, user, password):
    ctx.obj = Context(ip, user, password)
