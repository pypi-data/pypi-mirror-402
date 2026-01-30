import django_filters
from dcim.models import Device, Interface
from netbox.filtersets import NetBoxModelFilterSet
from tenancy.models import Tenant

from netbox_cesnet_services_plugin.models.bgpconnection import BGPConnection


class BGPConnectionAggregationFilterSet(NetBoxModelFilterSet):
    """FilterSet for BGP Connection Aggregation view"""

    device = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(), field_name="device", label="Device"
    )

    device_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Device.objects.all(),
        field_name="device__id",
        to_field_name="id",
        label="Device (ID)",
    )

    next_hop_interface = django_filters.ModelMultipleChoiceFilter(
        queryset=Interface.objects.all(),
        field_name="next_hop__interface",
        label="Next Hop Interface",
    )

    next_hop_interface_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Interface.objects.all(),
        field_name="next_hop__interface__id",
        to_field_name="id",
        label="Next Hop Interface (ID)",
    )

    bgp_prefix_tenant = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="bgp_prefix__tenant",
        label="BGP Prefix Tenant",
    )

    bgp_prefix_tenant_id = django_filters.ModelMultipleChoiceFilter(
        queryset=Tenant.objects.all(),
        field_name="bgp_prefix__tenant__id",
        to_field_name="id",
        label="BGP Prefix Tenant (ID)",
    )

    has_tenant = django_filters.BooleanFilter(method="_has_tenant", label="Has Tenant")

    def _has_tenant(self, queryset, name, value):
        """Filter by whether the BGP connection has a tenant or not"""
        if value:
            return queryset.exclude(bgp_prefix__tenant__isnull=True)
        else:
            return queryset.filter(bgp_prefix__tenant__isnull=True)

    class Meta:
        model = BGPConnection
        fields = (
            "device",
            "device_id",
            "next_hop_interface",
            "next_hop_interface_id",
            "bgp_prefix_tenant",
            "bgp_prefix_tenant_id",
            "has_tenant",
        )
