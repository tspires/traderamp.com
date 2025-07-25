"""Tag management utilities for TradeRamp infrastructure."""

from typing import Dict, Optional
from datetime import datetime, timezone

from config.constants import TagKeys


def create_default_tags(
    project_name: str,
    environment: str,
    owner: Optional[str] = None,
    cost_center: Optional[str] = None
) -> Dict[str, str]:
    """
    Create default tags for all AWS resources.
    
    Args:
        project_name: Project name
        environment: Environment (dev, staging, prod)
        owner: Resource owner
        cost_center: Cost center for billing
    
    Returns:
        Dictionary of default tags
    """
    tags = {
        TagKeys.PROJECT: project_name,
        TagKeys.ENVIRONMENT: environment,
        TagKeys.MANAGED_BY: "Pulumi",
        TagKeys.CREATED_AT: datetime.now(timezone.utc).isoformat()
    }
    
    if owner:
        tags[TagKeys.OWNER] = owner
    
    if cost_center:
        tags[TagKeys.COST_CENTER] = cost_center
    
    return tags


def merge_tags(
    default_tags: Dict[str, str],
    custom_tags: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """
    Merge custom tags with defaults, giving priority to custom tags.
    
    Args:
        default_tags: Default tags to apply
        custom_tags: Custom tags to merge
    
    Returns:
        Merged tag dictionary
    """
    if not custom_tags:
        return default_tags.copy()
    
    return {**default_tags, **custom_tags}


def validate_tags(tags: Dict[str, str]) -> Dict[str, str]:
    """
    Validate and clean tags according to AWS requirements.
    
    Args:
        tags: Tag dictionary to validate
    
    Returns:
        Validated and cleaned tag dictionary
    
    Raises:
        ValueError: If tags violate AWS constraints
    """
    from config.constants import AWSLimits
    
    if len(tags) > AWSLimits.MAX_TAGS_PER_RESOURCE:
        raise ValueError(
            f"Too many tags ({len(tags)}). "
            f"Maximum allowed: {AWSLimits.MAX_TAGS_PER_RESOURCE}"
        )
    
    validated_tags = {}
    
    for key, value in tags.items():
        # Validate key length
        if len(key) > AWSLimits.MAX_TAG_KEY_LENGTH:
            raise ValueError(
                f"Tag key '{key}' exceeds maximum length "
                f"({AWSLimits.MAX_TAG_KEY_LENGTH} characters)"
            )
        
        # Validate value length
        if len(str(value)) > AWSLimits.MAX_TAG_VALUE_LENGTH:
            raise ValueError(
                f"Tag value for '{key}' exceeds maximum length "
                f"({AWSLimits.MAX_TAG_VALUE_LENGTH} characters)"
            )
        
        # Clean key (remove invalid characters)
        clean_key = key.strip()
        if not clean_key:
            continue
        
        # Clean value
        clean_value = str(value).strip()
        
        validated_tags[clean_key] = clean_value
    
    return validated_tags


def add_resource_specific_tags(
    base_tags: Dict[str, str],
    resource_type: str,
    resource_name: str,
    purpose: Optional[str] = None
) -> Dict[str, str]:
    """
    Add resource-specific tags to base tags.
    
    Args:
        base_tags: Base tag dictionary
        resource_type: Type of AWS resource (e.g., 'VPC', 'ECS')
        resource_name: Name of the specific resource
        purpose: Purpose or function of the resource
    
    Returns:
        Tags with resource-specific additions
    """
    resource_tags = base_tags.copy()
    resource_tags["Name"] = resource_name
    resource_tags["ResourceType"] = resource_type
    
    if purpose:
        resource_tags[TagKeys.PURPOSE] = purpose
    
    return validate_tags(resource_tags)