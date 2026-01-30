from typing import Annotated

import strawberry
import strawberry_django

from netbox.graphql.types import NetBoxObjectType

from netbox_cesnet_services_plugin.models import LLDPNeighbor, LLDPNeighborLeaf, BGPConnection

from .filters import LLDPNeighborFilter, LLDPNeighborLeafFilter, BGPConnectionFilter

__all__ = (
    "LLDPNeighborType",
    "LLDPNeighborLeafType",
    "BGPConnectionType",
)


@strawberry_django.type(LLDPNeighbor, filters=LLDPNeighborFilter, pagination=True)
class LLDPNeighborType(NetBoxObjectType):
    device_a: Annotated["DeviceType", strawberry.lazy("dcim.graphql.types")] | None
    interface_a: Annotated["InterfaceType", strawberry.lazy("dcim.graphql.types")] | None
    device_b: Annotated["DeviceType", strawberry.lazy("dcim.graphql.types")] | None
    interface_b: Annotated["InterfaceType", strawberry.lazy("dcim.graphql.types")] | None
    imported_data: strawberry.auto
    status: strawberry.auto
    status_detail: strawberry.auto
    last_seen: strawberry.auto
    comments: strawberry.auto


@strawberry_django.type(LLDPNeighborLeaf, filters=LLDPNeighborLeafFilter, pagination=True)
class LLDPNeighborLeafType(NetBoxObjectType):
    device_nb: Annotated["DeviceType", strawberry.lazy("dcim.graphql.types")] | None
    interface_nb: Annotated["InterfaceType", strawberry.lazy("dcim.graphql.types")] | None
    device_ext: strawberry.auto
    interface_ext: strawberry.auto
    status: strawberry.auto
    imported_data: strawberry.auto


@strawberry_django.type(BGPConnection, filters=BGPConnectionFilter, pagination=True)
class BGPConnectionType(NetBoxObjectType):
    device: Annotated["DeviceType", strawberry.lazy("dcim.graphql.types")] | None
    next_hop: Annotated["IPAddressType", strawberry.lazy("ipam.graphql.types")] | None
    bgp_prefix: Annotated["PrefixType", strawberry.lazy("ipam.graphql.types")] | None
    vrf: Annotated["VRFType", strawberry.lazy("ipam.graphql.types")] | None
    role: strawberry.auto
    import_data: strawberry.auto
    comments: strawberry.auto
    raw_next_hop: str
    raw_bgp_prefix: str
    raw_vrf: str


# Type aliases for lazy imports
if False:  # TYPE_CHECKING equivalent that doesn't import at runtime
    from dcim.graphql.types import DeviceType, InterfaceType
    from ipam.graphql.types import IPAddressType, PrefixType, VRFType
