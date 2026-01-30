from .bgpconnection import BGPConnectionTable
from .bgpconnection_aggregation import BGPConnectionAggregationTable
from .lldpneighbor import LLDPNeighborTable
from .lldpneighborleaf import LLDPNeighborLeafTable

__all__ = [
    "BGPConnectionTable",
    "BGPConnectionAggregationTable",
    "LLDPNeighborTable",
    "LLDPNeighborLeafTable",
]
