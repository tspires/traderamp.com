"""ECR Repository component for TradeRamp infrastructure."""

from typing import Dict, Optional
import json
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions


class ECRRepositoryComponent(ComponentResource):
    """
    ECR Repository component with lifecycle policies.
    
    This component creates:
    - ECR Repository with image scanning
    - Lifecycle policy for image cleanup
    - Optional repository policy for cross-account access
    """
    
    def __init__(
        self,
        name: str,
        enable_image_scanning: bool = True,
        image_tag_mutability: str = "MUTABLE",
        max_image_count: int = 10,
        untagged_image_days: int = 7,
        cross_account_arns: Optional[list] = None,
        tags: Dict[str, str] = None,
        opts: ResourceOptions = None
    ) -> None:
        """
        Initialize ECR Repository component.
        
        Args:
            name: Repository name
            enable_image_scanning: Enable image scanning on push
            image_tag_mutability: MUTABLE or IMMUTABLE
            max_image_count: Maximum number of tagged images to keep
            untagged_image_days: Days to keep untagged images
            cross_account_arns: AWS account ARNs for cross-account access
            tags: Resource tags
            opts: Pulumi resource options
        """
        super().__init__("traderamp:storage:ECRRepository", name, None, opts)
        
        self.name = name
        self.enable_image_scanning = enable_image_scanning
        self.image_tag_mutability = image_tag_mutability
        self.max_image_count = max_image_count
        self.untagged_image_days = untagged_image_days
        self.cross_account_arns = cross_account_arns or []
        self.tags = tags or {}
        
        # Create resources
        self.repository = self._create_repository()
        self.lifecycle_policy = self._create_lifecycle_policy()
        
        if self.cross_account_arns:
            self.repository_policy = self._create_repository_policy()
        
        # Register outputs
        self.register_outputs({
            "repository_arn": self.repository.arn,
            "repository_url": self.repository.repository_url,
            "repository_name": self.repository.name
        })
    
    def _create_repository(self) -> aws.ecr.Repository:
        """Create ECR repository."""
        return aws.ecr.Repository(
            f"{self.name}-ecr",
            name=self.name,
            image_tag_mutability=self.image_tag_mutability,
            image_scanning_configuration={
                "scan_on_push": self.enable_image_scanning
            },
            encryption_configuration={
                "encryption_type": "AES256"  # Use KMS for enhanced security if needed
            },
            tags={
                **self.tags,
                "Name": f"{self.name}-ecr"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_lifecycle_policy(self) -> aws.ecr.LifecyclePolicy:
        """Create lifecycle policy for image cleanup."""
        lifecycle_rules = [
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
        
        # Add rule for old tagged images with specific patterns
        if self.max_image_count > 5:
            lifecycle_rules.append({
                "rulePriority": 3,
                "description": "Remove old development/feature branch images",
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
            repository=self.repository.name,
            policy=json.dumps({"rules": lifecycle_rules}),
            opts=ResourceOptions(parent=self)
        )
    
    def _create_repository_policy(self) -> aws.ecr.RepositoryPolicy:
        """Create repository policy for cross-account access."""
        policy_statements = []
        
        for account_arn in self.cross_account_arns:
            policy_statements.extend([
                {
                    "Sid": f"CrossAccountPull{account_arn.split(':')[4]}",
                    "Effect": "Allow",
                    "Principal": {"AWS": account_arn},
                    "Action": [
                        "ecr:BatchCheckLayerAvailability",
                        "ecr:GetDownloadUrlForLayer",
                        "ecr:BatchGetImage"
                    ]
                },
                {
                    "Sid": f"CrossAccountAuth{account_arn.split(':')[4]}",
                    "Effect": "Allow",
                    "Principal": {"AWS": account_arn},
                    "Action": "ecr:GetAuthorizationToken"
                }
            ])
        
        policy = {
            "Version": "2012-10-17",
            "Statement": policy_statements
        }
        
        return aws.ecr.RepositoryPolicy(
            f"{self.name}-policy",
            repository=self.repository.name,
            policy=json.dumps(policy),
            opts=ResourceOptions(parent=self)
        )
    
    def get_image_uri(self, tag: str = "latest") -> str:
        """
        Get the full image URI for a specific tag.
        
        Args:
            tag: Image tag
            
        Returns:
            Full ECR image URI
        """
        return f"{self.repository.repository_url}:{tag}"