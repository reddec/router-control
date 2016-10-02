# Programatic control for RV6688BCM (or similar) router

[⟹ Releases are here ⟸](https://github.com/reddec/router-control/releases)

This is library and CLI utils to control the router. It depends on python *3.5* and requests library.

See API in source code - it's really simple and short.

CLI also have a `--help` for options =). You may start from this command: `python router.pyz --help`, where `python` must be python 3.5 or higher.

Example:

Command: `python router.pyz -i 192.168.100.1 --help`

provides this output:

```
usage: router.pyz [-h] -i IP [-u USER] [-p PASSWORD]
                  {info,apply,nat,create,enable,disable,update,rename,remove}
                  ...

Control RVCM router

positional arguments:
  {info,apply,nat,create,enable,disable,update,rename,remove}
                        <sub-command> help
    info                Get information about router
    apply               Apply changes to the router
    nat                 Get current NAT table
    create              Create port forwarding rule
    enable              Enable single port forwarding rule
    disable             Disable single port forwarding rule
    update              Update single port forwarding rule
    rename              Rename port forwarding rule
    remove              Remove port forwarding rule

optional arguments:
  -h, --help            show this help message and exit
  -i IP, --ip IP        IP address of the router
  -u USER, --user USER  Username of web panel in the router
  -p PASSWORD, --password PASSWORD
                        Password of web panel in the router
```

