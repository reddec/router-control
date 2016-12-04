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
from typing import List
from datetime import datetime
from rvcm.cli import *
import re
import json


class Abonent:
    """
    Keep IP and phone number
    """

    def __init__(self, phone: str, ip: str):
        self.phone = phone
        self.ip = ip

    def __repr__(self):
        return self.__class__.__name__ + "(" + ",\n   ".join(k + "=" + repr(v) for k, v in self.__dict__.items()) + ")"

    def __str__(self):
        return repr(self)


class Call:
    """
    Describe single call history record
    """

    def __init__(self, line: int, direction: str, calling: Abonent, called: Abonent, duration_seconds: int,
                 stamp: datetime, status: str):
        self.line = line
        self.direction = direction
        self.calling = calling
        self.called = called
        self.duration = duration_seconds
        self.stamp = stamp
        self.status = status

    def __repr__(self):
        return self.__class__.__name__ + "(" + ",\n   ".join(k + "=" + repr(v) for k, v in self.__dict__.items()) + ")"

    def __str__(self):
        return repr(self)


class History:
    """
    Describes collection of calls history
    """
    URL = '/voice_call_logs.htm?l0=3&l1=2&l2=1&l3=-1'

    def __init__(self, calls: List[Call] = None):
        self.calls = calls or []

    def parse(self, page: str):
        keyword = 'var call_logs ='
        line = '[]'
        for ln in page.splitlines():
            index = ln.find(keyword)
            if index != -1:
                line = ln[index + len(keyword):-1]
                break
        records = json.loads(line)
        # Example:
        # "line 0, Answered, IN, Calling:0000000000000;cpc-rus=1;phone-cont(55.66.77.88),
        # Called:+100000000(11.22.33.44), Duration:0h:15m:34s, Mon Nov 28 19:43:31 2016"
        calls = []
        abonent_pattern = re.compile(r'(?P<phone>[0-9\+\-]+).*\((?P<ip>.*?)\)')
        for record in records:
            line, status, direction, source, target, duration, stamp = map(str.strip, record.split(','))
            line_num = int(line.split()[1])
            calling_phone, calling_ip = abonent_pattern.findall(source.split(':')[1])[0]
            called_phone, called_ip = abonent_pattern.findall(target.split(':')[1])[0]
            _, span = duration.split(':', 1)
            h, m, s = span.split(':')
            seconds = int(h[:-1]) * 3600 + int(m[:-1]) * 60 + int(s[:-1])
            calls.append(Call(
                line=line_num,
                direction=direction.upper(),
                calling=Abonent(phone=calling_phone, ip=calling_ip),
                called=Abonent(phone=called_phone, ip=called_ip),
                duration_seconds=seconds,
                stamp=datetime.strptime(stamp, '%a %b %d %H:%M:%S %Y'),
                status=status
            ))
        self.calls = calls

    def retrieve(self, requester: callable):
        """
        Get information about calls from router
        :param requester: function that returns text by url
        :return: self
        """
        resp = requester(self.URL)
        self.parse(resp.text)
        return self

    def __repr__(self):
        return self.__class__.__name__ + "(" + ",\n   ".join(k + "=" + repr(v) for k, v in self.__dict__.items()) + ")"

    def __str__(self):
        return repr(self)


@cli.group()
def calls():
    """
    Calls operations
    """
    pass


@calls.command()
@click.pass_context
def info(ctx):
    """Print calls history"""
    line = "{line:4}" \
           " {direction:9}" \
           " {status:9}" \
           " {calling_phone:13}" \
           " {calling_ip:16}" \
           " {called_phone:16}" \
           " {called_ip:16}" \
           " {duration:8}" \
           " {stamp:19}"
    print(line.format(
        line='LINE',
        direction='DIRECTION',
        status='STATUS',
        calling_phone='CALLING-PHONE',
        calling_ip='CALLING-IP',
        called_phone='CALLED-PHONE',
        called_ip='CALLING-IP',
        duration='DURATION',
        stamp='STAMP'

    ))
    history = History().retrieve(ctx.obj.getter)
    for call in history.calls:
        print(line.format(
            line=call.line,
            direction=call.direction,
            status=call.status,
            calling_phone=call.calling.phone,
            calling_ip=call.calling.ip,
            called_phone=call.called.phone,
            called_ip=call.called.ip,
            duration=call.duration,
            stamp=call.stamp.isoformat('T')
        ))


@calls.command()
@click.pass_context
def export(ctx):
    """Print calls history in JSON"""
    history = History().retrieve(ctx.obj.getter)
    data = []
    from collections import OrderedDict
    for call in history.calls:
        data.append(OrderedDict([
            ("line", call.line),
            ("direction", call.direction),
            ("status", call.status),
            ("calling_phone", call.calling.phone),
            ("calling_ip", call.calling.ip),
            ("called_phone", call.called.phone),
            ("called_ip", call.called.ip),
            ("duration", call.duration),
            ("stamp", call.stamp.isoformat('T'))
        ]
        ))
    print(json.dumps(data, ensure_ascii=False, indent=4))


if __name__ == '__main__':
    cli(obj=None)
