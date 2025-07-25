"""ECS Cluster component for TradeRamp infrastructure."""

from typing import Dict, Optional, List
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions, Output

from config.constants import LogDriver


class ECSClusterComponent(ComponentResource):
    """
    ECS Cluster component with Container Insights.
    
    This component creates:
    - ECS Cluster with Container Insights
    - CloudWatch Log Group for container logs
    - Optional capacity providers
    """
    
    def __init__(
        self,
        name: str,
        enable_container_insights: bool = True,
        log_retention_days: int = 30,
        capacity_providers: Optional[List[str]] = None,
        tags: Dict[str, str] = None,
        opts: ResourceOptions = None
    ) -> None:
        """
        Initialize ECS Cluster component.
        
        Args:
            name: Cluster name
            enable_container_insights: Enable Container Insights
            log_retention_days: CloudWatch log retention period
            capacity_providers: List of capacity providers (FARGATE, FARGATE_SPOT)
            tags: Resource tags
            opts: Pulumi resource options
        """
        super().__init__("traderamp:compute:ECSCluster", name, None, opts)
        
        self.name = name
        self.enable_container_insights = enable_container_insights
        self.log_retention_days = log_retention_days
        self.capacity_providers = capacity_providers or ["FARGATE", "FARGATE_SPOT"]
        self.tags = tags or {}
        
        # Create resources
        self.log_group = self._create_log_group()
        self.cluster = self._create_cluster()
        
        # Set up capacity providers
        if self.capacity_providers:
            self._setup_capacity_providers()
        
        # Register outputs
        self.register_outputs({
            "cluster_id": self.cluster.id,
            "cluster_arn": self.cluster.arn,
            "cluster_name": self.cluster.name,
            "log_group_name": self.log_group.name,
            "log_group_arn": self.log_group.arn
        })
    
    def _create_log_group(self) -> aws.cloudwatch.LogGroup:
        """Create CloudWatch Log Group for container logs."""
        return aws.cloudwatch.LogGroup(
            f"{self.name}-logs",
            name=f"/ecs/{self.name}",
            retention_in_days=self.log_retention_days,
            tags={
                **self.tags,
                "Name": f"{self.name}-logs"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_cluster(self) -> aws.ecs.Cluster:
        """Create ECS Cluster."""
        settings = []
        if self.enable_container_insights:
            settings.append({
                "name": "containerInsights",
                "value": "enabled"
            })
        
        return aws.ecs.Cluster(
            f"{self.name}-cluster",
            name=f"{self.name}-cluster",
            settings=settings,
            tags={
                **self.tags,
                "Name": f"{self.name}-cluster"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _setup_capacity_providers(self) -> None:
        """Set up cluster capacity providers."""
        # Define default capacity provider strategy
        default_strategy = []
        
        if "FARGATE" in self.capacity_providers:
            default_strategy.append({
                "capacity_provider": "FARGATE",
                "weight": 1,
                "base": 1
            })
        
        if "FARGATE_SPOT" in self.capacity_providers:
            default_strategy.append({
                "capacity_provider": "FARGATE_SPOT",
                "weight": 4,  # Prefer SPOT for cost savings
                "base": 0
            })
        
        aws.ecs.ClusterCapacityProviders(
            f"{self.name}-capacity-providers",
            cluster_name=self.cluster.name,
            capacity_providers=self.capacity_providers,
            default_capacity_provider_strategies=default_strategy,
            opts=ResourceOptions(parent=self)
        )
    
    def create_log_stream_prefix(self, service_name: str) -> str:
        """
        Create a consistent log stream prefix for a service.
        
        Args:
            service_name: Name of the ECS service
            
        Returns:
            Log stream prefix string
        """
        return f"ecs/{service_name}"
    
    def get_log_configuration(self, stream_prefix: str) -> Dict[str, any]:
        """
        Get log configuration for container definitions.
        
        Args:
            stream_prefix: CloudWatch log stream prefix
            
        Returns:
            Log configuration dictionary
        """
        return {
            "logDriver": LogDriver.AWSLOGS.value,
            "options": {
                "awslogs-group": self.log_group.name,
                "awslogs-region": aws.get_region().name,
                "awslogs-stream-prefix": stream_prefix
            }
        }