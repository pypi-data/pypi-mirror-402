from dcim.models import Device, Interface
from django import forms
from netbox.forms import NetBoxModelForm
from tenancy.models import Tenant

from netbox_cesnet_services_plugin.models import BGPConnection


class BGPConnectionAggregationFilterForm(NetBoxModelForm):
    """Filter form for BGP Connection Aggregation view"""

    device_id = forms.ModelMultipleChoiceField(
        queryset=Device.objects.filter(
            id__in=BGPConnection.objects.values_list("device_id", flat=True)
        ),
        required=False,
        label="Device",
        help_text="Filter by device",
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    next_hop_interface_id = forms.ModelMultipleChoiceField(
        queryset=Interface.objects.filter(
            id__in=BGPConnection.objects.values_list("next_hop__interface", flat=True)
        ).select_related("device"),
        required=False,
        label="Next Hop Interface",
        help_text="Filter by next hop interface",
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    bgp_prefix_tenant_id = forms.ModelMultipleChoiceField(
        queryset=Tenant.objects.filter(
            id__in=BGPConnection.objects.values_list("bgp_prefix__tenant_id", flat=True)
        ),
        required=False,
        label="BGP Prefix Tenant",
        help_text="Filter by BGP prefix tenant",
        widget=forms.SelectMultiple(attrs={"class": "form-control"}),
    )

    has_tenant = forms.BooleanField(
        required=False,
        label="Has Tenant",
        help_text="Show only connections with or without tenant assignment",
        widget=forms.Select(
            choices=[
                ("", "All"),
                ("True", "With Tenant"),
                ("False", "Without Tenant"),
            ]
        ),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Customize the interface field to show device info
        self.fields[
            "next_hop_interface_id"
        ].label_from_instance = self.interface_label_from_instance

    def interface_label_from_instance(self, obj):
        """Custom label for interface that includes device name"""
        return f"{obj.device.name} - {obj.name} - {obj.description or 'No Description'}"

    class Meta:
        model = BGPConnection
        fields = (
            "device_id",
            "next_hop_interface_id",
            "bgp_prefix_tenant_id",
            "has_tenant",
        )
