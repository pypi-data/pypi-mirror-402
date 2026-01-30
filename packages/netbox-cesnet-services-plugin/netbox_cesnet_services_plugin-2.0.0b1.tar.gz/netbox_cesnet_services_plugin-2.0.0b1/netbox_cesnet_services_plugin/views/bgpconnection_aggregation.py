from django.db.models import Count
from netbox.views import generic

from ..filtersets.bgpconnection_aggregation import BGPConnectionAggregationFilterSet
from ..forms.bgpconnection_aggregation import BGPConnectionAggregationFilterForm
from ..models.bgpconnection import BGPConnection
from ..tables.bgpconnection_aggregation import BGPConnectionAggregationTable


class BGPConnectionAggregationView(generic.ObjectListView):
    """
    BGP Connection aggregation view. Uses the regular BGPConnection model for now.
    """

    queryset = BGPConnection.objects.all()
    table = BGPConnectionAggregationTable
    filterset = BGPConnectionAggregationFilterSet
    filterset_form = BGPConnectionAggregationFilterForm
    template_name = "netbox_cesnet_services_plugin/bgpconnection/bgpconnection_aggregation_list.html"

    actions = {
        # "import": {"add"},
        "export": set(),
        # "bulk_edit": {"change"},
        # "bulk_delete": {"delete"},
    }

    def get_queryset(self, request):
        base_queryset = super().get_queryset(request)
        return (
            base_queryset.select_related(
                "device", "next_hop__interface", "bgp_prefix__tenant"
            )
            .values(
                "device",
                "device__name",
                "next_hop__interface",
                "next_hop__interface__name",
                "bgp_prefix__tenant",
                "bgp_prefix__tenant__name",
            )
            .annotate(connection_count=Count("id"))
            .order_by(
                "device__name",
                "next_hop__interface__name",
                "bgp_prefix__tenant__name",
            )
        )
