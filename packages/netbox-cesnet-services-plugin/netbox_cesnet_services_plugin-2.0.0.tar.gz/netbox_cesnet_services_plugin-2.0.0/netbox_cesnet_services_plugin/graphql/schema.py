from typing import List

import strawberry
import strawberry_django

from .types import LLDPNeighborType, LLDPNeighborLeafType, BGPConnectionType


@strawberry.type(name="Query")
class CESNETServicesQuery:
    lldp_neighbor: LLDPNeighborType = strawberry_django.field()
    lldp_neighbor_list: List[LLDPNeighborType] = strawberry_django.field()

    lldp_neighbor_leaf: LLDPNeighborLeafType = strawberry_django.field()
    lldp_neighbor_leaf_list: List[LLDPNeighborLeafType] = strawberry_django.field()

    bgp_connection: BGPConnectionType = strawberry_django.field()
    bgp_connection_list: List[BGPConnectionType] = strawberry_django.field()
