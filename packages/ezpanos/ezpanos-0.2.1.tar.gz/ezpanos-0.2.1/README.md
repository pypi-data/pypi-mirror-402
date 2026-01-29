# EZPanos

#### An Ergonomic and lightweight PanOS Utility Library

## Installation
``` bash
pip install ezpanos
```

## Quick Start
You may provide a username and password, or an API key.

If the username and password parameters are not populated without an API key, you will be prompted for them.

``` python
from ezpanos.ezpanos import EzPanOS
import getpass

creds = {
    "username": input("Username: "),
    "password": getpass.getpass("Password: ")
}
endpoint = "<Management interface IP"
connection = EzPanOS(endpoint, username=creds["username"], password=creds["password"])
print(connection.execute("show system info"))

```
## Using an API token

By default, the EzPanOS class will use username/password to generate an authentication token from PanOS. This can however, be overridden if you already have it.

``` python
from ezpanos.ezpanos import EzPanOS

endpoint = "x.x.x.x"
connection = EzPanOS(endpoint, api_key="xxxxxxxxxxxx")
print(connection.execute("show system info"))
```

## Retrieving a Device Configuration:
`Warning`: Each configuration can exceed 80+Mb each. Be mindful of memory leaks.

Memory utilization has been optimized during configuration retrieval using streaming output and tempfile utilization.

```
configuration_dictionary = connection.get_configuration()
```


## Saving a Device Configuration to Disk
To save a configuration to a file, use the `export_configuration` method.

``` python
from ezpanos.ezpanos import PanOS

endpoint = "x.x.x.x"
# or username/password outlined above
connection = EzPanOS(endpoint, api_key="xxxxxxxxxxxx") 
connection.export_configuration(output_filename="my_panos_configuration.json")
# if output_filename is null, default is:
# ./<endpoint_name>_yyy:mm:dd_hh:mm:ss.json 
```

## Getting the entire Device Configuration as a dictionary

for random access to a particular configuration item in the configuration, ruleset, network, interfaces, etc. Use the `get_configuration` method.

```python
from ezpanos.ezpanos import PanOS
from getpass import getpass
endpoint = "x.x.x.x"

# do NOT use this method on an untrusted system.
connection = EzPanOS(endpoint, username="user", password=getpass(f"Password: ")) 
configuration = connection.get_configration()
```

Currently an ideal platform for executing arbitrary PanOS commands against firewalls and Panorama instances for a wide variety of use cases.
