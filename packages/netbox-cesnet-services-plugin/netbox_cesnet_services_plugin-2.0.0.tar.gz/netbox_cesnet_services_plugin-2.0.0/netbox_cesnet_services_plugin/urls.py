from django.urls import include, path
from utilities.urls import get_model_urls

from netbox_cesnet_services_plugin.views.bgpconnection import (
    BGPConnectionDeleteView,
    BGPConnectionEditView,
    BGPConnectionListView,
    BGPConnectionView,
)
from netbox_cesnet_services_plugin.views.bgpconnection_aggregation import (
    BGPConnectionAggregationView,
)
from netbox_cesnet_services_plugin.views.lldpneighbor import (
    LLDPNeigborView,
    LLDPNeighborBulkDeleteView,
    LLDPNeighborDeleteView,
    LLDPNeighborEditView,
    LLDPNeighborListView,
)
from netbox_cesnet_services_plugin.views.lldpneighborleaf import (
    LLDPNeigborLeafView,
    LLDPNeighborLeafBulkDeleteView,
    LLDPNeighborLeafDeleteView,
    LLDPNeighborLeafEditView,
    LLDPNeighborLeafListView,
)

urlpatterns = (
    path(
        "bgp-connections/", BGPConnectionListView.as_view(), name="bgpconnection_list"
    ),
    path(
        "bgp-connections/aggregation/",
        BGPConnectionAggregationView.as_view(),
        name="bgpconnection_aggregation",
    ),
    path(
        "bgp-connections/add/",
        BGPConnectionEditView.as_view(),
        name="bgpconnection_add",
    ),
    path(
        "bgp-connections/<int:pk>/", BGPConnectionView.as_view(), name="bgpconnection"
    ),
    path(
        "bgp-connections/<int:pk>/edit/",
        BGPConnectionEditView.as_view(),
        name="bgpconnection_edit",
    ),
    path(
        "bgp-connections/<int:pk>/delete/",
        BGPConnectionDeleteView.as_view(),
        name="bgpconnection_delete",
    ),
    # Adds Changelog, Journal, and Attachment tabs
    path(
        "bgp-connections/",
        include(
            get_model_urls(
                "netbox_cesnet_services_plugin", "bgpconnection", detail=False
            )
        ),
    ),
    path(
        "bgp-connections/<int:pk>/",
        include(get_model_urls("netbox_cesnet_services_plugin", "bgpconnection")),
    ),
    path("lldp-neighbors/", LLDPNeighborListView.as_view(), name="lldpneighbor_list"),
    path(
        "lldp-neighbors/add/",
        LLDPNeighborEditView.as_view(),
        name="lldpneighbor_add",
    ),
    path("lldp-neighbors/<int:pk>/", LLDPNeigborView.as_view(), name="lldpneighbor"),
    path(
        "lldp-neighbors/<int:pk>/edit/",
        LLDPNeighborEditView.as_view(),
        name="lldpneighbor_edit",
    ),
    path(
        "lldp-neighbors/<int:pk>/delete/",
        LLDPNeighborDeleteView.as_view(),
        name="lldpneighbor_delete",
    ),
    path(
        "lldp-neighbors/delete/",
        LLDPNeighborBulkDeleteView.as_view(),
        name="lldpneighbor_bulk_delete",
    ),
    # Adds Changelog, Journal, and Attachment tabs
    path(
        "lldp-neighbors/",
        include(
            get_model_urls(
                "netbox_cesnet_services_plugin", "lldpneighbor", detail=False
            )
        ),
    ),
    path(
        "lldp-neighbors/<int:pk>/",
        include(get_model_urls("netbox_cesnet_services_plugin", "lldpneighbor")),
    ),
    path(
        "lldp-neighbor-leafs/",
        LLDPNeighborLeafListView.as_view(),
        name="lldpneighborleaf_list",
    ),
    path(
        "lldp-neighbor-leafs/add/",
        LLDPNeighborLeafEditView.as_view(),
        name="lldpneighborleaf_add",
    ),
    path(
        "lldp-neighbor-leafs/<int:pk>/",
        LLDPNeigborLeafView.as_view(),
        name="lldpneighborleaf",
    ),
    path(
        "lldp-neighbor-leafs/<int:pk>/edit/",
        LLDPNeighborLeafEditView.as_view(),
        name="lldpneighborleaf_edit",
    ),
    path(
        "lldp-neighbor-leafs/<int:pk>/delete/",
        LLDPNeighborLeafDeleteView.as_view(),
        name="lldpneighborleaf_delete",
    ),
    path(
        "lldp-neighbor-leafs/delete/",
        LLDPNeighborLeafBulkDeleteView.as_view(),
        name="lldpneighborleaf_bulk_delete",
    ),
    # Adds Changelog, Journal, and Attachment tabs
    path(
        "lldp-neighbor-leafs/",
        include(
            get_model_urls(
                "netbox_cesnet_services_plugin", "lldpneighborleaf", detail=False
            )
        ),
    ),
    path(
        "lldp-neighbor-leafs/<int:pk>/",
        include(get_model_urls("netbox_cesnet_services_plugin", "lldpneighborleaf")),
    ),
)
