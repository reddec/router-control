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
from rvcm.cli import *


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

    def retrieve(self, requester: callable):
        """
        Get information about NAT from router
        :param requester: function that returns text by url
        :return: self
        """
        resp = requester(self.URL)
        self.parse(resp.text)
        return self

    def save(self, poster: callable):
        """
        Save information about NAT in router
        :param poster: function that post data to router by URL
        """
        from collections import OrderedDict
        params = OrderedDict()
        for key, value in self.generate_form_fields():
            params[key] = value
        poster(self.UPDATE, params, self.URL)

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


@cli.group()
def nat():
    """
    NAT operations
    """
    pass


@nat.command()
@click.pass_context
def info(ctx):
    """
    Print forwarding table
    """
    nat = NAT().retrieve(ctx.obj.getter)
    preip = ctx.obj.ip.split('.')[:-1]
    print("{name:21s} {state:10s} {srcmin:10s} {srcmax:10s} {dstmin:10s} {dstmax:10s} {proto:5s} {ip:4s}".format(
        name="NAME",
        state="STATUS",
        srcmin="S-MIN-PRT",
        srcmax="S-MAX-PRT",
        dstmin="D-MIN-PRT",
        dstmax="D-MAX-PRT",
        proto="PROTO",
        ip="IP"

    ))
    for forward in nat.forwards:
        line = "{name:21s} {state:10s} {srcmin:10s} {srcmax:10s} {dstmin:10s} {dstmax:10s} {proto:5s} {ip:4s}".format(
            name=forward.name,
            state='active' if forward.enabled else 'inactive',
            srcmin=str(forward.src_min_port),
            srcmax=str(forward.src_max_port),
            proto=str(forward.type.name),
            dstmin=str(forward.dest_min_port),
            dstmax=str(forward.dest_max_port),
            ip=".".join(preip + [str(forward.dest_ip_sec)])
        )
        print(line)


@nat.command()
@click.argument('name')
@click.argument('dest-ip-section')
@click.argument('min-src-port')
@click.argument('max-src-port')
@click.argument('min-dst-port')
@click.argument('max-dst-port')
@click.option('--proto', default=ForwardType.BOTH.name,
              type=click.Choice([ForwardType.BOTH.name, ForwardType.TCP.name, ForwardType.UDP.name]),
              help='Protocol type to forward')
@click.pass_context
def create(ctx, name: str, dest_ip_section: str, min_src_port: int, max_src_port: int, min_dst_port: int, max_dst_port,

           proto: ForwardType):
    """
    Create forwarding rule
    """
    assert 0 < len(dest_ip_section) <= 3, "IP last section required"

    forward = Forward(name=name, dest_ip_sec=dest_ip_section)
    forward.src_min_port = min_src_port
    forward.src_max_port = max_src_port
    forward.dest_min_port = min_dst_port
    forward.dest_max_port = max_dst_port
    forward.enabled = False
    forward.type = ForwardType[proto]
    nat = NAT().retrieve(ctx.obj.getter)
    nat.forwards.append(forward)
    nat.save(ctx.obj.poster)


@nat.command()
@click.argument('name')
@click.option('--dest-ip-section', type=int)
@click.option('--min-src-port', type=int)
@click.option('--max-src-port', type=int)
@click.option('--min-dst-port', type=int)
@click.option('--max-dst-port', type=int)
@click.option('--proto', default=ForwardType.BOTH.name,
              type=click.Choice([ForwardType.BOTH.name, ForwardType.TCP.name, ForwardType.UDP.name]),
              help='Protocol type to forward')
@click.pass_context
def update(ctx, name: str, dest_ip_section: str, min_src_port: int, max_src_port: int, min_dst_port: int, max_dst_port,
           proto: ForwardType):
    """Update forwarding record"""
    upd = False
    nat = NAT().retrieve(ctx.obj.getter)
    for frw in nat.forwards:
        if frw.name == name:
            if max_dst_port is not None and frw.dest_max_port != max_dst_port:
                frw.dest_max_port = max_dst_port
                upd = True
            if min_dst_port is not None and frw.dest_min_port != min_dst_port:
                frw.dest_min_port = min_dst_port
                upd = True
            if min_src_port is not None and frw.src_min_port != min_src_port:
                frw.src_min_port = min_src_port
                upd = True
            if max_src_port is not None and frw.src_max_port != max_src_port:
                frw.src_max_port = max_src_port
                upd = True
            if dest_ip_section is not None and frw.dest_ip_sec != dest_ip_section:
                frw.dest_ip_sec = dest_ip_section
                upd = True
            if proto is not None and frw.type != proto:
                frw.type = ForwardType[proto]
                upd = True
            if upd:
                print("updating " + str(frw))

    if upd:
        nat.save(ctx.obj.poster)
    else:
        print("Nothing to update")


@nat.command()
@click.argument('name')
@click.pass_context
def remove(ctx, name: str):
    """Remove forwarding rule"""
    upd = False
    nat = NAT().retrieve(ctx.obj.getter)
    items = []
    for frw in nat.forwards:
        if frw.name != name:
            items.append(frw)
        else:
            upd = True
            print("removing " + str(frw))
    nat.forwards = items
    if upd:
        nat.save(ctx.obj.poster)
    else:
        print("nothing to remove")


@nat.command()
@click.argument('name')
@click.pass_context
def disable(ctx, name: str):
    """Disable (but not remove) rule"""
    nat = NAT().retrieve(ctx.obj.getter)
    upd = False
    for frw in nat.forwards:
        if frw.name == name and frw.enabled:
            frw.enabled = False
            upd = True
            print("disabling " + str(frw))
    if upd:
        nat.save(ctx.obj.poster)
    else:
        print("nothing to disable")


@nat.command()
@click.argument('name')
@click.pass_context
def enable(ctx, name: str):
    """Enable rule"""
    nat = NAT().retrieve(ctx.obj.getter)
    upd = False
    for frw in nat.forwards:
        if frw.name == name and not frw.enabled:
            frw.enabled = True
            upd = True
            print("enabling " + str(frw))
    if upd:
        nat.save(ctx.obj.poster)
    else:
        print("nothing to enable")


@nat.command()
@click.argument('old_name')
@click.argument('new_name')
@click.pass_context
def rename(ctx, old_name, new_name):
    """Rename forwarding rule"""
    nat = NAT().retrieve(ctx.obj.getter)
    upd = False
    for frw in nat.forwards:
        if frw.name == old_name:
            print("renaming " + str(frw))
            upd = True
            frw.name = new_name
    if upd:
        nat.save(ctx.obj.poster)
    else:
        print("nothing to rename")


if __name__ == '__main__':
    cli(obj=None)
