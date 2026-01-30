"""Top-level package for NetBox cesnet_services Plugin."""

__author__ = """Jan Krupa"""
__email__ = "jan.krupa@cesnet.cz"
__version__ = "2.0.0b1"


from netbox.plugins import PluginConfig


class CesnetServicesConfig(PluginConfig):
    name = "netbox_cesnet_services_plugin"
    verbose_name = "NetBox cesnet_services Plugin"
    description = "NetBox plugin for CESNET services."
    version = __version__
    base_url = "netbox-cesnet-services-plugin"
    author = __author__
    author_email = __email__
    min_version = "4.5.0"
    max_version = "4.5.99"


config = CesnetServicesConfig
