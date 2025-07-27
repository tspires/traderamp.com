"""
AWS storage components following clean code principles.
"""

from typing import Dict, Optional, Any, List
import json
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Output

from core.base_component import BaseInfrastructureComponent
from core.validators import ValidationContext, RangeValidator


class ContainerRegistryComponent(BaseInfrastructureComponent):
    """
    ECR (Elastic Container Registry) component.
    
    Manages container image repository with lifecycle policies.
    """
    
    def __init__(
        self,
        name: str,
        enable_image_scanning: bool = True,
        image_tag_mutability: str = "MUTABLE",
        max_image_count: int = 10,
        untagged_image_days: int = 7,
        **kwargs
    ):
        """Initialize container registry component."""
        self.enable_image_scanning = enable_image_scanning
        self.image_tag_mutability = image_tag_mutability
        self.max_image_count = max_image_count
        self.untagged_image_days = untagged_image_days
        
        super().__init__(
            "traderamp:aws:storage:ContainerRegistry",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate container registry configuration."""
        context = ValidationContext()
        
        context.add_validation(
            "max_image_count",
            RangeValidator(1, 1000, "Max image count"),
            self.max_image_count
        )
        
        context.add_validation(
            "untagged_image_days",
            RangeValidator(1, 365, "Untagged image retention"),
            self.untagged_image_days
        )
        
        context.validate_all()
        
        if self.image_tag_mutability not in ["MUTABLE", "IMMUTABLE"]:
            raise ValueError("image_tag_mutability must be MUTABLE or IMMUTABLE")
    
    def create_resources(self) -> None:
        """Create ECR resources."""
        # Create repository
        repository = aws.ecr.Repository(
            f"{self.name}-ecr",
            name=self.name,
            image_tag_mutability=self.image_tag_mutability,
            image_scanning_configuration={
                "scan_on_push": self.enable_image_scanning
            },
            encryption_configurations=[{
                "encryption_type": "AES256"
            }],
            tags=self.get_tags("ECR", f"{self.name}-ecr"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("repository", repository)
        
        # Create lifecycle policy
        lifecycle_policy = self._create_lifecycle_policy(repository)
        self.add_resource("lifecycle_policy", lifecycle_policy)
    
    def _create_lifecycle_policy(self, repository: aws.ecr.Repository) -> aws.ecr.LifecyclePolicy:
        """Create lifecycle policy for image cleanup."""
        rules = [
            {
                "rulePriority": 1,
                "description": f"Keep last {self.max_image_count} tagged images",
                "selection": {
                    "tagStatus": "tagged",
                    "tagPrefixList": ["v", "latest", "main", "master"],
                    "countType": "imageCountMoreThan",
                    "countNumber": self.max_image_count
                },
                "action": {"type": "expire"}
            },
            {
                "rulePriority": 2,
                "description": f"Remove untagged images after {self.untagged_image_days} days",
                "selection": {
                    "tagStatus": "untagged",
                    "countType": "sinceImagePushed",
                    "countUnit": "days",
                    "countNumber": self.untagged_image_days
                },
                "action": {"type": "expire"}
            }
        ]
        
        # Add rule for development images
        if self.max_image_count > 5:
            rules.append({
                "rulePriority": 3,
                "description": "Remove old development images",
                "selection": {
                    "tagStatus": "tagged",
                    "tagPrefixList": ["dev-", "feature-", "test-"],
                    "countType": "sinceImagePushed",
                    "countUnit": "days",
                    "countNumber": 3
                },
                "action": {"type": "expire"}
            })
        
        return aws.ecr.LifecyclePolicy(
            f"{self.name}-lifecycle",
            repository=repository.name,
            policy=json.dumps({"rules": rules}),
            opts=ResourceOptions(parent=self)
        )
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        repository = self.get_resource("repository")
        return {
            "repository_arn": repository.arn,
            "repository_url": repository.repository_url,
            "repository_name": repository.name
        }