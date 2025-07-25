"""Compute components for TradeRamp infrastructure."""

from .ecs_cluster import ECSClusterComponent
from .ecs_service import ECSServiceComponent

__all__ = [
    "ECSClusterComponent",
    "ECSServiceComponent"
]