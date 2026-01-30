import strawberry_django
from netbox.graphql.filters import NetBoxModelFilter
from strawberry_django import FilterLookup

from netbox_cesnet_services_plugin.models import (
    BGPConnection,
    LLDPNeighbor,
    LLDPNeighborLeaf,
)


@strawberry_django.filter_type(LLDPNeighbor, lookups=True)
class LLDPNeighborFilter(NetBoxModelFilter):
    status: FilterLookup[str] | None = strawberry_django.filter_field()
    status_detail: FilterLookup[str] | None = strawberry_django.filter_field()


@strawberry_django.filter_type(LLDPNeighborLeaf, lookups=True)
class LLDPNeighborLeafFilter(NetBoxModelFilter):
    status: FilterLookup[str] | None = strawberry_django.filter_field()


@strawberry_django.filter_type(BGPConnection, lookups=True)
class BGPConnectionFilter(NetBoxModelFilter):
    role: FilterLookup[str] | None = strawberry_django.filter_field()
