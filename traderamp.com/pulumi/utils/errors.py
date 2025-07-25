"""Error handling utilities for TradeRamp infrastructure."""

from typing import Optional, Any, Type
import pulumi
from dataclasses import dataclass


@dataclass
class InfrastructureError(Exception):
    """Base exception for infrastructure errors."""
    
    message: str
    resource_name: Optional[str] = None
    error_code: Optional[str] = None
    
    def __str__(self) -> str:
        """String representation of the error."""
        parts = [self.message]
        
        if self.resource_name:
            parts.append(f"Resource: {self.resource_name}")
        
        if self.error_code:
            parts.append(f"Code: {self.error_code}")
        
        return " | ".join(parts)


class ConfigurationError(InfrastructureError):
    """Error in configuration validation."""
    pass


class ResourceCreationError(InfrastructureError):
    """Error during resource creation."""
    pass


class DependencyError(InfrastructureError):
    """Error with resource dependencies."""
    pass


class ValidationError(InfrastructureError):
    """Error in input validation."""
    pass


def handle_pulumi_error(
    operation: str,
    resource_name: str,
    error: Exception,
    reraise: bool = True
) -> None:
    """
    Handle Pulumi operation errors with proper logging.
    
    Args:
        operation: Description of the operation that failed
        resource_name: Name of the resource being operated on
        error: The original exception
        reraise: Whether to re-raise the exception
    
    Raises:
        ResourceCreationError: If reraise is True
    """
    error_message = f"Failed to {operation} for resource '{resource_name}': {str(error)}"
    
    # Log the error
    pulumi.log.error(error_message, resource=resource_name)
    
    if reraise:
        raise ResourceCreationError(
            message=error_message,
            resource_name=resource_name,
            error_code=getattr(error, 'code', None)
        ) from error


def validate_required_config(
    config_name: str,
    config_value: Any,
    error_message: Optional[str] = None
) -> None:
    """
    Validate that a required configuration value is present.
    
    Args:
        config_name: Name of the configuration
        config_value: Value to validate
        error_message: Custom error message
    
    Raises:
        ConfigurationError: If the value is missing or invalid
    """
    if config_value is None or config_value == "":
        message = error_message or f"Required configuration '{config_name}' is missing or empty"
        pulumi.log.error(message)
        raise ConfigurationError(message=message)


def validate_aws_limits(
    resource_type: str,
    current_count: int,
    limit: int,
    resource_name: Optional[str] = None
) -> None:
    """
    Validate that we don't exceed AWS service limits.
    
    Args:
        resource_type: Type of AWS resource
        current_count: Current count of resources
        limit: AWS service limit
        resource_name: Name of the resource being created
    
    Raises:
        ValidationError: If the limit would be exceeded
    """
    if current_count >= limit:
        message = (
            f"Creating {resource_type} '{resource_name or 'unnamed'}' would exceed "
            f"AWS limit of {limit} resources"
        )
        pulumi.log.error(message)
        raise ValidationError(
            message=message,
            resource_name=resource_name,
            error_code="AWS_LIMIT_EXCEEDED"
        )


def safe_resource_creation(
    resource_class: Type,
    resource_name: str,
    *args,
    **kwargs
) -> Any:
    """
    Safely create a resource with proper error handling.
    
    Args:
        resource_class: The resource class to instantiate
        resource_name: Name of the resource
        *args: Positional arguments for the resource
        **kwargs: Keyword arguments for the resource
    
    Returns:
        The created resource instance
    
    Raises:
        ResourceCreationError: If resource creation fails
    """
    try:
        return resource_class(resource_name, *args, **kwargs)
    except Exception as e:
        handle_pulumi_error(
            operation=f"create {resource_class.__name__}",
            resource_name=resource_name,
            error=e,
            reraise=True
        )


def log_resource_creation(
    resource_type: str,
    resource_name: str,
    additional_info: Optional[dict] = None
) -> None:
    """
    Log successful resource creation.
    
    Args:
        resource_type: Type of the resource
        resource_name: Name of the resource
        additional_info: Additional information to log
    """
    message = f"Successfully created {resource_type}: {resource_name}"
    
    if additional_info:
        info_str = ", ".join(f"{k}={v}" for k, v in additional_info.items())
        message += f" ({info_str})"
    
    pulumi.log.info(message, resource=resource_name)


def validate_dependencies(
    resource_name: str,
    dependencies: dict
) -> None:
    """
    Validate that all required dependencies are present.
    
    Args:
        resource_name: Name of the resource being created
        dependencies: Dictionary of dependency name -> dependency value
    
    Raises:
        DependencyError: If any required dependency is missing
    """
    missing_deps = []
    
    for dep_name, dep_value in dependencies.items():
        if dep_value is None:
            missing_deps.append(dep_name)
    
    if missing_deps:
        message = (
            f"Resource '{resource_name}' is missing required dependencies: "
            f"{', '.join(missing_deps)}"
        )
        pulumi.log.error(message)
        raise DependencyError(
            message=message,
            resource_name=resource_name,
            error_code="MISSING_DEPENDENCIES"
        )