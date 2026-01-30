import django_tables2 as tables
from django.utils.html import format_html
from netbox.tables import NetBoxTable

from ..models.bgpconnection import BGPConnection


class BGPConnectionAggregationTable(NetBoxTable):
    """Table for displaying BGP Connections"""

    device = tables.Column(
        verbose_name="Device", orderable=True, accessor="device__name"
    )
    next_hop_interface = tables.Column(
        verbose_name="Next Hop Interface",
        orderable=True,
        accessor="next_hop__interface__name",
    )
    bgp_prefix_tenant = tables.Column(
        verbose_name="BGP Prefix Tenant",
        orderable=True,
        accessor="bgp_prefix__tenant__name",
    )
    connection_count = tables.Column(verbose_name="Connection Count", orderable=True)

    def render_device(self, value, record):
        """Render the device with proper link"""
        if record.get("device") and record.get("device__name"):
            device_id = record["device"]
            device_name = record["device__name"]
            return format_html(
                '<a href="/dcim/devices/{}/">{}</a>',
                device_id,
                device_name,
            )
        return value

    def render_next_hop_interface(self, value, record):
        """Render the next hop interface with proper link"""
        if record.get("next_hop__interface") and record.get(
            "next_hop__interface__name"
        ):
            interface_id = record["next_hop__interface"]
            interface_name = record["next_hop__interface__name"]
            return format_html(
                '<a href="/dcim/interfaces/{}/">{}</a>',
                interface_id,
                interface_name,
            )
        return value

    def render_bgp_prefix_tenant(self, value, record):
        """Render the BGP prefix tenant with proper link"""
        if record.get("bgp_prefix__tenant") and record.get("bgp_prefix__tenant__name"):
            tenant_id = record["bgp_prefix__tenant"]
            tenant_name = record["bgp_prefix__tenant__name"]
            return format_html(
                '<a href="/tenancy/tenants/{}/">{}</a>',
                tenant_id,
                tenant_name,
            )
        return "No Tenant"

    class Meta(NetBoxTable.Meta):
        model = BGPConnection
        orderable = True
        fields = (
            "device",
            "next_hop_interface",
            "bgp_prefix_tenant",
            "connection_count",
        )
        default_columns = (
            "device",
            "next_hop_interface",
            "bgp_prefix_tenant",
            "connection_count",
        )
