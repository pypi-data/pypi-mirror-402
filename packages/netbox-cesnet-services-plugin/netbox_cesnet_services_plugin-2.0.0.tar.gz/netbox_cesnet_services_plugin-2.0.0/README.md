# NetBox cesnet_services Plugin

NetBox plugin for CESNET services.

* Free software: MIT
* Documentation: https://kani999.github.io/netbox-cesnet-services-plugin/


## Features

Enables CESNET services in Netbox. BGP connections, LLDP Neigbors, LLDP Leafs

## Compatibility

| NetBox Version | Plugin Version | Notes |
|----------------|----------------|-------|
|     4.5.0+     |      2.0.0     | **Breaking change**: Filter system updated, NOT compatible with 4.4.x |
|     4.4.x      |      1.2.8     | Last version compatible with NetBox 4.4.x |
|     4.4.0      |      1.2.5     | |
|     4.3.1      |      1.2.4     | |
|     4.3.1      |      1.2.3     | |
|     4.2.8      |      1.2.2     | |

## Installing

For adding to a NetBox Docker setup see
[the general instructions for using netbox-docker with plugins](https://github.com/netbox-community/netbox-docker/wiki/Using-Netbox-Plugins).

### Prerequisites

- **NetBox 4.5.0 or higher** (for plugin version 2.0.0)
  - **Important**: Plugin version 2.0.0 is NOT compatible with NetBox 4.4.x due to filter system changes
  - If you're running NetBox 4.4.x, use plugin version 1.2.8 or earlier

### Installation

You can install with pip:

```bash
pip install netbox-cesnet-services-plugin
```

or by adding to your `local_requirements.txt` or `plugin_requirements.txt` (netbox-docker):

```bash
# For NetBox 4.5.0+
netbox-cesnet-services-plugin==2.0.0

# For NetBox 4.4.x (use 1.2.8 or earlier)
# netbox-cesnet-services-plugin==1.2.8
```

### Configuration

Enable the plugin in `/opt/netbox/netbox/netbox/configuration.py`,
or if you use netbox-docker, your `/configuration/plugins.py` file.

You can optionally set device platforms for filtering choices in LLDPNeighbor form: 

```python
PLUGINS = [
    'netbox_cesnet_services_plugin'
]

PLUGINS_CONFIG = {
    "netbox_cesnet_services_plugin": {
        "platforms" : ["ios", "iosxe", "iosxr", "nxos", "nxos_ssh"],
    },
}
```

## Credits

Based on the NetBox plugin tutorial:

- [demo repository](https://github.com/netbox-community/netbox-plugin-demo)
- [tutorial](https://github.com/netbox-community/netbox-plugin-tutorial)

This package was created with [Cookiecutter](https://github.com/audreyr/cookiecutter) and the [`netbox-community/cookiecutter-netbox-plugin`](https://github.com/netbox-community/cookiecutter-netbox-plugin) project template.
