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

from enum import Enum
from typing import List

import requests
from lxml import html
from requests.auth import HTTPDigestAuth


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


class ForwardType(Enum):
    """
    Enumeration of possible protocol types in forwarding rules
    """
    TCP = 1
    UDP = 2
    BOTH = 3

    def __str__(self):
        return self.name


class Forward:
    """
    Describes port forwarding single rule in the router
    """

    def __init__(self, name='', dest_ip_sec='', src_min_port=0, src_max_port=0, dest_min_port=0, dest_max_port=0,
                 enabled=False,
                 type: ForwardType = ForwardType.BOTH):
        self.dest_ip_sec = dest_ip_sec
        self.src_min_port = src_min_port
        self.src_max_port = src_max_port
        self.dest_min_port = dest_min_port
        self.dest_max_port = dest_max_port
        self.name = name
        self.enabled = enabled
        self.type = type

    def __repr__(self):
        return self.__class__.__name__ + "(" + ", ".join(k + "=" + repr(v) for k, v in self.__dict__.items()) + ")"

    def __str__(self):
        return "%s-%s-%s-%s-%s-%s-%s-%s-0-" % (
            1 if self.enabled else 0,
            self.name,
            self.src_min_port,
            self.src_max_port,
            self.type.value,
            self.dest_min_port,
            self.dest_max_port,
            self.dest_ip_sec
        )


class NAT:
    """
    Describes table of port forwarding rules in the router
    """
    URL = '/vs.htm?l0=1&l1=2&l2=0&l3=-1'
    UPDATE = '/setup.cgi?l0=1&l1=2&l2=0&l3=-1'

    def __init__(self, forwards: List[Forward] = None):
        self.forwards = forwards or []

    def parse(self, data):
        """
        Parse content of NAT page and gather info into self structure
        :param data: Content of NAT page info
        """
        fws = []
        for line in data.splitlines():
            if line.startswith('var vs_list'):
                fws = line[15:-3].split(';')
                break
        self.forwards.clear()
        for rule in fws:
            opt = rule.split('-')
            forward = Forward()
            forward.enabled = int(opt[0]) != 0
            forward.name = opt[1]
            forward.src_min_port = int(opt[2])
            forward.src_max_port = int(opt[3])
            forward.type = ForwardType(int(opt[4]))
            forward.dest_min_port = int(opt[5])
            forward.dest_max_port = int(opt[6])
            forward.dest_ip_sec = int(opt[7])
            self.forwards.append(forward)

    def generate_form_fields(self):
        """
        Generate pairs of forms fields
        :return: iterator of (key, value) tuple
        """
        yield ('virtual_server_list', 'Active Worlds')
        yield ('vs_pc_list', '0')
        yield ('if_list', '')
        yield ('clear_entry_list', '')
        for i, forward in enumerate(self.forwards):
            yield ('enable_%s' % i, str(1 if forward.enabled else 0))
            yield ('description_%s' % i, forward.name)
            yield ('inbound_port_low_%s' % i, str(forward.src_min_port))
            yield ('inbound_port_high_%s' % i, str(forward.src_max_port))
            yield ('type_%s' % i, str(forward.type.value))
            yield ('private_port_low_%s' % i, str(forward.dest_min_port))
            yield ('private_port_high_%s' % i, str(forward.dest_max_port))
            yield ('private_ip_%s' % i, str(forward.dest_ip_sec))
            yield ('if_%s' % i, '0')
        yield ('h_vs_list', ";".join(str(f) for f in self.forwards) + ";")
        yield ('fwi_des', '')
        yield ('todo', 'save')
        yield ('this_file', 'vs.htm')
        yield ('next_file', 'vs.htm')
        yield ('message', '')

    def __repr__(self):
        return self.__class__.__name__ + "(" + ",\n   ".join(k + "=" + repr(v) for k, v in self.__dict__.items()) + ")"

    def __str__(self):
        return repr(self)


class Router:
    """
    Provides entry point for any manipulations with router
    """

    def __init__(self, addr, user='admin', password='admin'):
        self.user = user
        self.password = password
        self.url = "http://" + addr

    def __get_and_parse(self, cls):
        instance = cls()
        instance.parse(requests.get(self.url + cls.URL, auth=HTTPDigestAuth(self.user, self.password)).text)
        return instance

    def __post(self, instance):
        from collections import OrderedDict
        assert hasattr(instance, 'UPDATE')
        params = OrderedDict()
        for key, value in instance.generate_form_fields():
            params[key] = value
        resp = requests.post(self.url + instance.UPDATE, data=params, auth=HTTPDigestAuth(self.user, self.password),
                             headers={
                                 'Referer': self.url + instance.URL
                             })
        t = resp.text
        assert resp.status_code == 200, t

    def apply(self):
        """
        Apply changes on the router
        """
        resp = requests.post(self.url + '/setup.cgi?l0=-1&l1=-1&l2=-1&l3=-1', data={
            'todo': 'apply',
            'this_file': 'global_nav.htm',
            'next_file': 'index.html'
        }, auth=HTTPDigestAuth(self.user, self.password),
                             headers={
                                 'Referer': self.url
                             })
        t = resp.text
        assert resp.status_code == 200, t

    def get_info(self) -> Info:
        """
        Gather info from index page and parse it
        """
        return self.__get_and_parse(Info)

    def get_nat(self) -> NAT:
        """
        Gather info from NAT page and parse it
        """
        return self.__get_and_parse(NAT)

    def update_nat(self, value: NAT) -> NAT:
        """
        Post new NAT table to the router
        """
        self.__post(value)
