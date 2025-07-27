"""
Core interfaces for infrastructure components.

Following Dependency Inversion Principle - high-level modules should not depend 
on low-level modules. Both should depend on abstractions.
"""

from abc import ABC, abstractmethod
from typing import Protocol, List, Dict, Optional, Any
from dataclasses import dataclass
from pulumi import Input, Output


class ILoadBalancer(Protocol):
    """Interface for load balancer implementations."""
    
    @property
    def dns_name(self) -> Output[str]:
        """Get the DNS name of the load balancer."""
        ...
    
    @property
    def arn(self) -> Output[str]:
        """Get the ARN of the load balancer."""
        ...
    
    def get_target_group_arn(self) -> Output[str]:
        """Get the target group ARN."""
        ...


class ISecurityGroup(Protocol):
    """Interface for security group implementations."""
    
    @property
    def id(self) -> Output[str]:
        """Get the security group ID."""
        ...
    
    @property
    def name(self) -> Output[str]:
        """Get the security group name."""
        ...


class INetworkProvider(ABC):
    """Abstract base class for network providers."""
    
    @abstractmethod
    def create_vpc(self, cidr_block: str) -> Any:
        """Create a VPC with the given CIDR block."""
        pass
    
    @abstractmethod
    def create_subnets(self, vpc_id: str, count: int) -> List[Any]:
        """Create subnets in the VPC."""
        pass
    
    @abstractmethod
    def create_security_group(self, name: str, vpc_id: str, rules: List[Any]) -> Any:
        """Create a security group with rules."""
        pass


class IContainerOrchestrator(ABC):
    """Abstract base class for container orchestration."""
    
    @abstractmethod
    def create_cluster(self, name: str) -> Any:
        """Create a container cluster."""
        pass
    
    @abstractmethod
    def create_service(self, name: str, cluster_id: str, config: Any) -> Any:
        """Create a container service."""
        pass
    
    @abstractmethod
    def create_task_definition(self, name: str, config: Any) -> Any:
        """Create a task/pod definition."""
        pass


@dataclass
class HealthCheckSpec:
    """Health check specification - cloud agnostic."""
    
    path: str = "/health"
    interval_seconds: int = 30
    timeout_seconds: int = 5
    healthy_threshold: int = 2
    unhealthy_threshold: int = 3
    
    def validate(self) -> None:
        """Validate health check configuration."""
        if self.timeout_seconds >= self.interval_seconds:
            raise ValueError(
                f"Timeout ({self.timeout_seconds}s) must be less than "
                f"interval ({self.interval_seconds}s)"
            )
        
        if self.healthy_threshold < 1:
            raise ValueError("Healthy threshold must be at least 1")
        
        if self.unhealthy_threshold < 1:
            raise ValueError("Unhealthy threshold must be at least 1")


@dataclass
class ScalingSpec:
    """Auto-scaling specification - cloud agnostic."""
    
    min_instances: int = 1
    max_instances: int = 4
    target_cpu_percent: float = 70.0
    target_memory_percent: float = 70.0
    scale_down_cooldown_seconds: int = 300
    scale_up_cooldown_seconds: int = 60
    
    def validate(self) -> None:
        """Validate scaling configuration."""
        if self.min_instances < 1:
            raise ValueError("Minimum instances must be at least 1")
        
        if self.min_instances > self.max_instances:
            raise ValueError(
                f"Minimum instances ({self.min_instances}) cannot exceed "
                f"maximum instances ({self.max_instances})"
            )
        
        if not 0 < self.target_cpu_percent <= 100:
            raise ValueError("Target CPU must be between 0 and 100")
        
        if not 0 < self.target_memory_percent <= 100:
            raise ValueError("Target memory must be between 0 and 100")


@dataclass
class ContainerSpec:
    """Container specification - cloud agnostic."""
    
    image: str
    cpu_units: int = 256
    memory_mb: int = 512
    port: int = 80
    environment_variables: Dict[str, str] = None
    secrets: Dict[str, str] = None
    
    def __post_init__(self):
        """Initialize with defaults."""
        if self.environment_variables is None:
            self.environment_variables = {}
        if self.secrets is None:
            self.secrets = {}
    
    def validate(self) -> None:
        """Validate container configuration."""
        if not self.image:
            raise ValueError("Container image is required")
        
        if self.cpu_units < 128:
            raise ValueError("CPU units must be at least 128")
        
        if self.memory_mb < 128:
            raise ValueError("Memory must be at least 128 MB")


class IResourceTagger(Protocol):
    """Interface for resource tagging strategies."""
    
    def get_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """Get tags for a resource."""
        ...