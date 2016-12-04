# Programatic control for RV6688BCM (or similar) router

[![Development Status](https://img.shields.io/pypi/status/rvcm.svg)](https://pypi.python.org/pypi/rvcm/)
 [![PyPI version](https://img.shields.io/pypi/v/rvcm.svg)](https://pypi.python.org/pypi/rvcm/)
[![Python version](https://img.shields.io/pypi/pyversions/rvcm.svg)](https://pypi.python.org/pypi/rvcm/)

This is library and CLI utils to control the router. It depends on python *3.5* and requests library.

See API in source code - it's really simple and short.

CLI also have a `--help` for options =). You may start from this command: `rvcm --help`, where `python` must be python 3.5 or higher.

provides this output:

```
usage: rvcm [OPTIONS] COMMAND [ARGS]...

Options:
  --ip TEXT        Router IP
  --user TEXT      Login name
  --password TEXT  Password
  --help           Show this message and exit.

Commands:
  calls   Calls operations
  nat     NAT operations
  router  Direct router operations
```

The router-control supports basic environment variables (in addition to command line arguments):

* `RC_IP` - IP address to router
* `RC_USER` - Login name to router (default: admin)
* `RC_PASSWORD` - Password to router (default: admin)


## Router operations

```
Usage: rvcm router [OPTIONS] COMMAND [ARGS]...

  Direct router operations

Options:
  --help  Show this message and exit.

Commands:
  apply   Apply changes on the router
  export  Print details about router in json
  info    Print details about router

```

Example:

Command: `python rvcm --ip 192.168.100.1 router info`

## NAT operations

```
Usage: rvcm nat [OPTIONS] COMMAND [ARGS]...

  NAT operations

Options:
  --help  Show this message and exit.

Commands:
  create   Create forwarding rule
  disable  Disable (but not remove) rule
  enable   Enable rule
  info     Print forwarding table
  remove   Remove forwarding rule
  rename   Rename forwarding rule
  update   Update forwarding record

```

## Calls operations

```
Usage: rvcm calls [OPTIONS] COMMAND [ARGS]...

  Calls operations

Options:
  --help  Show this message and exit.

Commands:
  export  Print calls history in JSON
  info    Print calls history
```
