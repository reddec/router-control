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
from rvcm.cli import *
from lxml import html
import json


class Info:
    """
    Describes full information about router status
    """
    # URL to page with full information
    URL = '/index.htm'

    def __init__(self, ip='', gateway='', mac='', sip_user='', local_ip='', dns1='', dns2='', firmware='', model='',
                 gpon_serial='', phone_line_up=False, wan_line_up=False, lan_line_up=False, apply_required=False):
        self.ip = ip
        self.gateway = gateway
        self.mac = mac
        self.sip_user = sip_user
        self.local_ip = local_ip
        self.dns1 = dns1
        self.dns2 = dns2
        self.firmware = firmware
        self.model = model
        self.gpon_serial = gpon_serial
        self.phone_line_up = phone_line_up
        self.wan_line_up = wan_line_up
        self.lan_line_up = lan_line_up
        self.apply_required = apply_required

    def parse(self, page: str):
        """
        Parse index HTML page and gather info
        :param page: Content of index page
        """
        root = html.fromstring(page)
        form = root.find('.//form[@action="setup.cgi"]')

        self.wan_line_up = '"Up"' in form.find('.//table/tr[2]/td/table/tr[2]/td[4]/script').text
        self.ip = form.find('.//table/tr[2]/td/table/tr[3]/td[2]').text
        self.gateway = form.find('.//table/tr[2]/td/table/tr[3]/td[4]').text
        self.dns1 = form.find('.//table/tr[2]/td/table/tr[4]/td[2]').text
        self.dns2 = form.find('.//table/tr[2]/td/table/tr[4]/td[4]').text

        self.phone_line_up = '"Up"' in form.find('.//table/tr[4]/td/table/tr[3]/td[2]/script').text
        self.sip_user = form.find('.//table/tr[4]/td/table/tr[4]/td[2]').text

        self.model = form.find('.//table/tr[6]/td/table/tr[2]/td[2]').text
        self.firmware = form.find('.//table/tr[6]/td/table/tr[2]/td[4]').text
        self.gpon_serial = form.find('.//table/tr[6]/td/table/tr[3]/td[2]').text
        self.mac = form.find('.//table/tr[6]/td/table/tr[3]/td[4]').text

        self.local_ip = form.find('.//table/tr[8]/td/table/tr[2]/td[2]').text
        self.lan_line_up = '"Connected"' in form.find('.//table/tr[8]/td/table/tr[2]/td[4]/script').text

        self.apply_required = False
        for line in page.splitlines():
            if line == 'var headMsg = "Please do Apply to make the changes take effect.";':
                self.apply_required = True
                break

    def retrieve(self, requester: callable):
        """
        Get information about NAT from router
        :param requester: function that returns text by url
        :return: self
        """
        resp = requester(self.URL)
        self.parse(resp.text)
        return self

    def pretty(self):
        """
        Make pretty-printed text with router info
        :return: text
        """

        lines = []
        lines += ["Model           : {}".format(self.model)]
        lines += ["IP              : {}".format(self.ip)]
        lines += ["Gateway         : {}".format(self.gateway)]
        lines += ["MAC             : {}".format(self.mac)]
        lines += ["Local IP        : {}".format(self.local_ip)]
        lines += ["DNS1            : {}".format(self.dns1)]
        lines += ["DNS2            : {}".format(self.dns2)]
        lines += ["SIP             : {}".format(self.sip_user)]
        lines += ["GPON            : {} ".format(self.gpon_serial)]
        lines += ["Firmware        : {} ".format(self.firmware)]
        lines += ["Phone status    : {}".format("OK" if self.phone_line_up else "Unavailable")]
        lines += ["WAN status      : {}".format("OK" if self.wan_line_up else "Unavailable")]
        lines += ["LAN status      : {}".format("OK" if self.lan_line_up else "Unavailable")]
        lines += ["Unsaved changes : {}".format("Yes" if self.apply_required else "No")]
        return "\n".join(lines)

    def __repr__(self):
        return self.__class__.__name__ + "(" + ",\n   ".join(k + "=" + repr(v) for k, v in self.__dict__.items()) + ")"

    def __str__(self):
        return repr(self)


@cli.group()
def router():
    """
    Direct router operations
    """
    pass


@router.command()
@click.pass_context
def apply(ctx):
    """
    Apply changes on the router
    """
    ctx.obj.poster('/setup.cgi?l0=-1&l1=-1&l2=-1&l3=-1', {
        'todo': 'apply',
        'this_file': 'global_nav.htm',
        'next_file': 'index.html'
    })


@router.command()
@click.pass_context
def info(ctx):
    """Print details about router"""
    info = Info().retrieve(ctx.obj.getter)
    print(info.pretty())


@router.command()
@click.pass_context
def export(ctx):
    """Print details about router in json"""
    info = Info().retrieve(ctx.obj.getter)
    data = {
        "model": info.model,
        "ip": info.ip,
        "gateway": info.gateway,
        "mac": info.mac,
        "local_ip": info.local_ip,
        "dns1": info.dns1,
        "dns2": info.dns2,
        "sip": info.sip_user,
        "gpon": info.gpon_serial,
        "firmware": info.firmware,
        "phone_status": info.phone_line_up,
        "wan_status": info.wan_line_up,
        "lan_status": info.lan_line_up,
        "unsaved_changes": info.apply_required,
    }
    print(json.dumps(data, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    cli(obj=None)
