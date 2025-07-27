"""
Base component class following DRY principle.

Provides common functionality for all infrastructure components.
"""

from typing import Dict, Optional, Any, List
from abc import ABC, abstractmethod
import pulumi
from pulumi import ComponentResource, ResourceOptions, Output

from .interfaces import IResourceTagger


class BaseInfrastructureComponent(ComponentResource, ABC):
    """
    Base class for all infrastructure components.
    
    Provides:
    - Common initialization
    - Tag management
    - Error handling
    - Resource validation
    """
    
    def __init__(
        self,
        component_type: str,
        name: str,
        tagger: Optional[IResourceTagger] = None,
        opts: ResourceOptions = None
    ):
        """
        Initialize base component.
        
        Args:
            component_type: Type identifier for the component
            name: Component name
            tagger: Resource tagging strategy
            opts: Pulumi resource options
        """
        super().__init__(component_type, name, None, opts)
        
        self.name = name
        self.tagger = tagger
        self._resources: Dict[str, Any] = {}
        
        # Validate component configuration
        self.validate()
        
        # Create resources
        try:
            self.create_resources()
        except Exception as e:
            self._handle_creation_error(e)
        
        # Register outputs
        self.register_component_outputs()
    
    @abstractmethod
    def validate(self) -> None:
        """Validate component configuration."""
        pass
    
    @abstractmethod
    def create_resources(self) -> None:
        """Create the component's resources."""
        pass
    
    @abstractmethod
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs to register."""
        pass
    
    def register_component_outputs(self) -> None:
        """Register component outputs with Pulumi."""
        outputs = self.get_outputs()
        if outputs:
            self.register_outputs(outputs)
    
    def get_tags(self, resource_type: str, resource_name: str) -> Dict[str, str]:
        """
        Get tags for a resource.
        
        Args:
            resource_type: Type of the resource
            resource_name: Name of the resource
            
        Returns:
            Dictionary of tags
        """
        if self.tagger:
            return self.tagger.get_tags(resource_type, resource_name)
        
        # Default tags
        return {
            "Name": resource_name,
            "Component": self.name,
            "ManagedBy": "Pulumi"
        }
    
    def add_resource(self, key: str, resource: Any) -> None:
        """
        Add a resource to the component's resource collection.
        
        Args:
            key: Resource identifier
            resource: The resource instance
        """
        self._resources[key] = resource
        self._log_resource_creation(key, resource)
    
    def get_resource(self, key: str) -> Optional[Any]:
        """
        Get a resource by key.
        
        Args:
            key: Resource identifier
            
        Returns:
            The resource instance or None
        """
        return self._resources.get(key)
    
    def _log_resource_creation(self, key: str, resource: Any) -> None:
        """Log successful resource creation."""
        resource_type = type(resource).__name__
        pulumi.log.info(
            f"Created {resource_type} '{key}' in component '{self.name}'"
        )
    
    def _handle_creation_error(self, error: Exception) -> None:
        """
        Handle resource creation errors.
        
        Args:
            error: The exception that occurred
        """
        pulumi.log.error(
            f"Failed to create resources for component '{self.name}': {str(error)}"
        )
        raise
    
    def apply_to_all_resources(self, func: callable) -> None:
        """
        Apply a function to all resources in the component.
        
        Args:
            func: Function to apply to each resource
        """
        for key, resource in self._resources.items():
            func(key, resource)