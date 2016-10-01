#!/usr/bin/env python3
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
import argparse

from router import *


def cli():
    # This is full CLI utility to control NAT in the router

    parser = argparse.ArgumentParser(description='Control RVCM router')
    parser.add_argument('-i', '--ip', required=True, help='IP address of the router')
    cmds = parser.add_subparsers(help='<sub-command> help', dest='command')

    info_cmd = cmds.add_parser('info', help='Get information about router')

    apply_cmd = cmds.add_parser('apply', help='Apply changes to the router')

    nat_cmd = cmds.add_parser('nat', help='Get current NAT table')

    nat_create_cmd = cmds.add_parser('create', help='Create port forwarding rule')
    nat_create_cmd.add_argument('name', type=str, help='Rule name')
    nat_create_cmd.add_argument('min_pub_port', type=int, help='Public min port number')
    nat_create_cmd.add_argument('max_pub_port', type=int, help='Public max port number')
    nat_create_cmd.add_argument('min_dest_port', type=int, help='Local target min port number')
    nat_create_cmd.add_argument('max_dest_port', type=int, help='Local target max port number')
    nat_create_cmd.add_argument('target', type=int, help='Last section of target IP (last 3 digits)')
    nat_create_cmd.add_argument('protocol', type=lambda x: ForwardType[x.upper()], help='Protocol',
                                choices=[ForwardType.BOTH, ForwardType.TCP, ForwardType.UDP], default=ForwardType.BOTH,
                                nargs='?')

    nat_enable_cmd = cmds.add_parser('enable', help='Enable single port forwarding rule')
    nat_enable_cmd.add_argument('name', type=str, help='Name of forwarding rule')

    nat_disable_cmd = cmds.add_parser('disable', help='Disable single port forwarding rule')
    nat_disable_cmd.add_argument('name', type=str, help='Name of forwarding rule')

    nat_update_cmd = cmds.add_parser('update', help='Update single port forwarding rule')
    nat_update_cmd.add_argument('name', type=str, help='Name of forwarding rule')
    nat_update_cmd.add_argument('--min_pub_port', type=int, help='Public min port number')
    nat_update_cmd.add_argument('--max_pub_port', type=int, help='Public max port number')
    nat_update_cmd.add_argument('--min_dest_port', type=int, help='Local target min port number')
    nat_update_cmd.add_argument('--max_dest_port', type=int, help='Local target max port number')
    nat_update_cmd.add_argument('--target', type=int, help='Last section of target IP (last 3 digits)')
    nat_update_cmd.add_argument('--protocol', type=lambda x: ForwardType[x.upper()], help='Protocol',
                                choices=[ForwardType.BOTH, ForwardType.TCP, ForwardType.UDP])

    nat_rename_cmd = cmds.add_parser('rename', help='Rename port forwarding rule')
    nat_rename_cmd.add_argument('name', type=str, help='Name of forwarding rule')
    nat_rename_cmd.add_argument('new_name', type=str, help='New name of forwarding rule')

    nat_remove_cmd = cmds.add_parser('remove', help='Remove port forwarding rule')
    nat_remove_cmd.add_argument('name', type=str, help='Name of forwarding rule')

    args = parser.parse_args()
    router = Router(args.ip)
    if args.command == 'info' or args.command is None:
        info = router.get_info()
        print(info.pretty())
    elif args.command == 'nat':
        info = router.get_info()
        nat = router.get_nat()
        preip = info.local_ip.split('.')[:-1]
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
    elif args.command == 'disable':
        nat = router.get_nat()
        upd = False
        for frw in nat.forwards:
            if frw.name == args.name and frw.enabled:
                frw.enabled = False
                upd = True
                print("disabling " + str(frw))
        if upd:
            router.update_nat(nat)
        else:
            print("nothing to disable")
    elif args.command == 'enable':
        nat = router.get_nat()
        upd = False
        for frw in nat.forwards:
            if frw.name == args.name and not frw.enabled:
                frw.enabled = True
                upd = True
                print("enabling " + str(frw))
        if upd:
            router.update_nat(nat)
        else:
            print("nothing to enable")
    elif args.command == 'apply':
        router.apply()
    elif args.command == 'create':
        forward = Forward(name=args.name, dest_ip_sec=args.target)
        forward.src_min_port = args.min_pub_port
        forward.src_max_port = args.max_pub_port
        forward.dest_min_port = args.min_dest_port
        forward.dest_max_port = args.max_dest_port
        forward.enabled = False
        forward.type = args.protocol
        nat = router.get_nat()
        nat.forwards.append(forward)
        router.update_nat(nat)
    elif args.command == 'update':
        upd = False
        nat = router.get_nat()
        for frw in nat.forwards:
            if frw.name == args.name:

                if args.max_dest_port is not None and frw.dest_max_port != args.max_dest_port:
                    frw.dest_max_port = args.max_dest_port
                    upd = True
                if args.min_dest_port is not None and frw.dest_min_port != args.min_dest_port:
                    frw.dest_min_port = args.min_dest_port
                    upd = True
                if args.min_pub_port is not None and frw.src_min_port != args.min_pub_port:
                    frw.src_min_port = args.min_pub_port
                    upd = True
                if args.max_pub_port is not None and frw.src_max_port != args.max_pub_port:
                    frw.src_max_port = args.max_pub_port
                    upd = True
                if args.protocol is not None and frw.type != args.protocol:
                    frw.type = args.protocol
                    upd = True
                if upd:
                    print("updating " + str(frw))

        if upd:
            router.update_nat(nat)
        else:
            print("Nothing to update")
    elif args.command == 'remove':
        upd = False
        nat = router.get_nat()
        items = []
        for frw in nat.forwards:
            if frw.name != args.name:
                items.append(frw)
            else:
                upd = True
                print("removing " + str(frw))
        nat.forwards = items
        if upd:
            router.update_nat(nat)
        else:
            print("nothing to remove")
    elif args.command == 'rename':
        nat = router.get_nat()
        upd = False
        for frw in nat.forwards:
            if frw.name == args.name:
                print("renaming " + str(frw))
                upd = True
                frw.name = args.new_name
        if upd:
            router.update_nat(nat)
        else:
            print("nothing to rename")


if __name__ == '__main__':
    cli()
