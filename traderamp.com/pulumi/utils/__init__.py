"""Utility modules for TradeRamp infrastructure."""

from .tagging import create_default_tags, merge_tags, validate_tags, add_resource_specific_tags
from .errors import (
    InfrastructureError,
    ConfigurationError,
    ResourceCreationError,
    DependencyError,
    ValidationError,
    handle_pulumi_error,
    validate_required_config,
    validate_aws_limits,
    safe_resource_creation,
    log_resource_creation,
    validate_dependencies
)

__all__ = [
    # Tagging utilities
    "create_default_tags",
    "merge_tags", 
    "validate_tags",
    "add_resource_specific_tags",
    
    # Error handling
    "InfrastructureError",
    "ConfigurationError",
    "ResourceCreationError", 
    "DependencyError",
    "ValidationError",
    "handle_pulumi_error",
    "validate_required_config",
    "validate_aws_limits",
    "safe_resource_creation",
    "log_resource_creation",
    "validate_dependencies"
]