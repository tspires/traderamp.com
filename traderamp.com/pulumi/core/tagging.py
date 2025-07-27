"""
Resource tagging strategies following Strategy pattern.

Each strategy has a single responsibility for tag generation.
"""

from typing import Dict, Optional, List
from datetime import datetime
from abc import ABC, abstractmethod

from .interfaces import IResourceTagger


class BaseTaggingStrategy(IResourceTagger, ABC):
    """Base class for tagging strategies."""
    
    def __init__(self, base_tags: Optional[Dict[str, str]] = None):
        """
        Initialize tagging strategy.
        
        Args:
            base_tags: Base tags to apply to all resources
        """
        self.base_tags = base_tags or {}
    
    @abstractmethod
    def get_strategy_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """
        Get strategy-specific tags.
        
        Args:
            resource_type: Type of the resource
            resource_name: Name of the resource
            
        Returns:
            Dictionary of tags
        """
        pass
    
    def get_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """
        Get complete tags for a resource.
        
        Args:
            resource_type: Type of the resource
            resource_name: Name of the resource
            
        Returns:
            Dictionary of tags
        """
        tags = self.base_tags.copy()
        tags.update(self.get_strategy_tags(resource_type, resource_name))
        tags["Name"] = resource_name  # Always include Name tag
        return tags


class StandardTaggingStrategy(BaseTaggingStrategy):
    """Standard tagging strategy with common tags."""
    
    def __init__(
        self,
        project: str,
        environment: str,
        owner: Optional[str] = None,
        cost_center: Optional[str] = None,
        **kwargs
    ):
        """
        Initialize standard tagging strategy.
        
        Args:
            project: Project name
            environment: Environment name
            owner: Resource owner
            cost_center: Cost center for billing
        """
        base_tags = {
            "Project": project,
            "Environment": environment,
            "ManagedBy": "Pulumi",
            "CreatedAt": datetime.utcnow().isoformat()
        }
        
        if owner:
            base_tags["Owner"] = owner
        
        if cost_center:
            base_tags["CostCenter"] = cost_center
        
        super().__init__(base_tags)
    
    def get_strategy_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """Get standard strategy tags."""
        return {
            "ResourceType": resource_type,
            "Purpose": self._get_purpose(resource_type)
        }
    
    def _get_purpose(self, resource_type: str) -> str:
        """Get purpose tag based on resource type."""
        purpose_map = {
            "VPC": "Network infrastructure",
            "Subnet": "Network segmentation",
            "SecurityGroup": "Network security",
            "ALB": "Load balancing",
            "TargetGroup": "Service routing",
            "ECS": "Container orchestration",
            "ECR": "Container registry",
            "IAMRole": "Access control",
            "LogGroup": "Logging and monitoring"
        }
        return purpose_map.get(resource_type, "Infrastructure component")


class ComplianceTaggingStrategy(StandardTaggingStrategy):
    """Tagging strategy with compliance requirements."""
    
    def __init__(
        self,
        project: str,
        environment: str,
        data_classification: str,
        compliance_framework: str,
        **kwargs
    ):
        """
        Initialize compliance tagging strategy.
        
        Args:
            project: Project name
            environment: Environment name
            data_classification: Data classification level
            compliance_framework: Compliance framework (e.g., PCI-DSS, HIPAA)
        """
        super().__init__(project, environment, **kwargs)
        self.data_classification = data_classification
        self.compliance_framework = compliance_framework
    
    def get_strategy_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """Get compliance strategy tags."""
        tags = super().get_strategy_tags(resource_type, resource_name)
        
        tags.update({
            "DataClassification": self.data_classification,
            "ComplianceFramework": self.compliance_framework,
            "Encrypted": self._requires_encryption(resource_type)
        })
        
        return tags
    
    def _requires_encryption(self, resource_type: str) -> str:
        """Determine if resource type requires encryption."""
        encrypted_types = ["RDS", "S3", "EBS", "ECR", "SecretsManager"]
        return "true" if any(t in resource_type for t in encrypted_types) else "false"


class CompositeTaggingStrategy(IResourceTagger):
    """Combines multiple tagging strategies."""
    
    def __init__(self, strategies: List[IResourceTagger]):
        """
        Initialize composite tagging strategy.
        
        Args:
            strategies: List of tagging strategies to combine
        """
        self.strategies = strategies
    
    def get_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """Combine tags from all strategies."""
        combined_tags = {}
        
        for strategy in self.strategies:
            tags = strategy.get_tags(resource_type, resource_name)
            combined_tags.update(tags)
        
        return combined_tags


class ConditionalTaggingStrategy(IResourceTagger):
    """Applies different strategies based on conditions."""
    
    def __init__(
        self,
        default_strategy: IResourceTagger,
        conditional_strategies: Dict[str, IResourceTagger]
    ):
        """
        Initialize conditional tagging strategy.
        
        Args:
            default_strategy: Default strategy to use
            conditional_strategies: Map of resource type patterns to strategies
        """
        self.default_strategy = default_strategy
        self.conditional_strategies = conditional_strategies
    
    def get_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """Get tags based on resource type."""
        # Check if any condition matches
        for pattern, strategy in self.conditional_strategies.items():
            if pattern in resource_type:
                return strategy.get_tags(resource_type, resource_name)
        
        # Use default strategy
        return self.default_strategy.get_tags(resource_type, resource_name)