"""Main TradeRamp infrastructure stack."""

from typing import Dict, Any, Optional
import pulumi
from pulumi import Output

from config.settings import InfrastructureConfig
from components.networking import (
    VPCComponent,
    create_alb_security_group,
    create_ecs_security_group,
    LoadBalancerComponent
)
from components.compute import ECSClusterComponent, ECSServiceComponent
from components.storage import ECRRepositoryComponent
from utils.tagging import create_default_tags, add_resource_specific_tags
from utils.errors import (
    log_resource_creation,
    validate_dependencies,
    handle_pulumi_error
)


class TradeRampStack:
    """
    Main infrastructure stack for TradeRamp application.
    
    This stack orchestrates all infrastructure components:
    - VPC with public subnets
    - Security groups
    - Application Load Balancer with SSL
    - ECS cluster and service
    - ECR repository
    - Auto-scaling configuration
    """
    
    def __init__(self, config: InfrastructureConfig):
        """
        Initialize TradeRamp infrastructure stack.
        
        Args:
            config: Infrastructure configuration
        """
        self.config = config
        self.tags = create_default_tags(
            project_name=config.project_name,
            environment=config.environment
        )
        
        try:
            # Create infrastructure components in dependency order
            self._create_networking()
            self._create_storage()
            self._create_compute()
            self._create_load_balancer()
            self._create_ecs_service()
            
            # Export stack outputs
            self._export_outputs()
            
            pulumi.log.info(
                f"Successfully initialized TradeRamp stack for {config.environment} environment"
            )
            
        except Exception as e:
            handle_pulumi_error(
                operation="initialize TradeRamp stack",
                resource_name=f"{config.project_name}-{config.environment}",
                error=e,
                reraise=True
            )
    
    def _create_networking(self) -> None:
        """Create networking components."""
        pulumi.log.info("Creating networking components...")
        
        # Create VPC
        self.vpc = VPCComponent(
            name=self.config.get_resource_name("vpc"),
            enable_flow_logs=self.config.environment == "production",
            tags=add_resource_specific_tags(
                self.tags, "VPC", self.config.get_resource_name("vpc")
            )
        )
        log_resource_creation("VPC", self.vpc.name)
        
        # Create ALB security group
        self.alb_security_group = create_alb_security_group(
            name=self.config.name_prefix,
            vpc_id=self.vpc.vpc.id,
            tags=add_resource_specific_tags(
                self.tags, "SecurityGroup", f"{self.config.name_prefix}-alb-sg", "ALB"
            )
        )
        log_resource_creation("ALB Security Group", self.alb_security_group.name)
        
        # Create ECS security group
        self.ecs_security_group = create_ecs_security_group(
            name=self.config.name_prefix,
            vpc_id=self.vpc.vpc.id,
            alb_security_group_id=self.alb_security_group.security_group.id,
            allow_all_egress=self.config.environment != "production",  # More restrictive in prod
            tags=add_resource_specific_tags(
                self.tags, "SecurityGroup", f"{self.config.name_prefix}-ecs-sg", "ECS"
            )
        )
        log_resource_creation("ECS Security Group", self.ecs_security_group.name)
    
    def _create_storage(self) -> None:
        """Create storage components."""
        pulumi.log.info("Creating storage components...")
        
        self.ecr_repository = ECRRepositoryComponent(
            name=self.config.name_prefix,
            enable_image_scanning=True,
            max_image_count=15 if self.config.environment == "production" else 5,
            untagged_image_days=3 if self.config.environment == "production" else 1,
            tags=add_resource_specific_tags(
                self.tags, "ECR", f"{self.config.name_prefix}-ecr"
            )
        )
        log_resource_creation("ECR Repository", self.ecr_repository.name)
    
    def _create_compute(self) -> None:
        """Create compute components."""
        pulumi.log.info("Creating compute components...")
        
        self.ecs_cluster = ECSClusterComponent(
            name=self.config.name_prefix,
            enable_container_insights=self.config.enable_container_insights,
            log_retention_days=self.config.log_retention_days,
            tags=add_resource_specific_tags(
                self.tags, "ECS", f"{self.config.name_prefix}-cluster"
            )
        )
        log_resource_creation("ECS Cluster", self.ecs_cluster.name)
    
    def _create_load_balancer(self) -> None:
        """Create load balancer components."""
        pulumi.log.info("Creating load balancer...")
        
        # Validate dependencies
        validate_dependencies(
            "LoadBalancer",
            {
                "vpc": self.vpc,
                "subnets": self.vpc.public_subnets,
                "security_group": self.alb_security_group
            }
        )
        
        self.load_balancer = LoadBalancerComponent(
            name=self.config.name_prefix,
            vpc_id=self.vpc.vpc.id,
            subnet_ids=[subnet.id for subnet in self.vpc.public_subnets],
            security_group_ids=[self.alb_security_group.security_group.id],
            health_check_config=self.config.health_check,
            domain_config=self.config.domain,
            enable_deletion_protection=self.config.environment == "production",
            tags=add_resource_specific_tags(
                self.tags, "ALB", f"{self.config.name_prefix}-alb"
            )
        )
        log_resource_creation("Load Balancer", self.load_balancer.name)
    
    def _create_ecs_service(self) -> None:
        """Create ECS service."""
        pulumi.log.info("Creating ECS service...")
        
        # Validate dependencies
        validate_dependencies(
            "ECS Service",
            {
                "cluster": self.ecs_cluster,
                "target_group": self.load_balancer.target_group,
                "ecr_repository": self.ecr_repository,
                "security_group": self.ecs_security_group
            }
        )
        
        # Prepare environment variables
        environment_vars = {
            "ENVIRONMENT": self.config.environment,
            "PROJECT_NAME": self.config.project_name,
            "LOG_LEVEL": "INFO" if self.config.environment == "production" else "DEBUG"
        }
        
        # Get log configuration from cluster
        log_config = self.ecs_cluster.get_log_configuration(
            self.ecs_cluster.create_log_stream_prefix(self.config.name_prefix)
        )
        
        self.ecs_service = ECSServiceComponent(
            name=self.config.name_prefix,
            cluster_arn=self.ecs_cluster.cluster.arn,
            container_image=self.ecr_repository.repository.repository_url.apply(
                lambda url: f"{url}:latest"
            ),
            container_config=self.config.container,
            scaling_config=self.config.scaling,
            vpc_subnets=[subnet.id for subnet in self.vpc.public_subnets],
            security_groups=[self.ecs_security_group.security_group.id],
            target_group_arn=self.load_balancer.target_group.arn,
            log_configuration=log_config,
            environment_variables=environment_vars,
            health_check_grace_period=self.config.health_check.grace_period,
            enable_execute_command=self.config.environment != "production",
            tags=add_resource_specific_tags(
                self.tags, "ECS", f"{self.config.name_prefix}-service"
            )
        )
        log_resource_creation("ECS Service", self.ecs_service.name)
    
    def _export_outputs(self) -> None:
        """Export stack outputs."""
        pulumi.log.info("Exporting stack outputs...")
        
        # Basic infrastructure outputs
        pulumi.export("vpc_id", self.vpc.vpc.id)
        pulumi.export("vpc_cidr", self.vpc.vpc.cidr_block)
        pulumi.export("public_subnet_ids", [s.id for s in self.vpc.public_subnets])
        
        # Load balancer outputs
        pulumi.export("alb_arn", self.load_balancer.alb.arn)
        pulumi.export("alb_dns_name", self.load_balancer.alb.dns_name)
        pulumi.export("alb_zone_id", self.load_balancer.alb.zone_id)
        
        # ECS outputs
        pulumi.export("ecs_cluster_name", self.ecs_cluster.cluster.name)
        pulumi.export("ecs_cluster_arn", self.ecs_cluster.cluster.arn)
        pulumi.export("ecs_service_name", self.ecs_service.service.name)
        pulumi.export("ecs_service_arn", self.ecs_service.service.id)
        
        # Storage outputs
        pulumi.export("ecr_repository_url", self.ecr_repository.repository.repository_url)
        pulumi.export("ecr_repository_arn", self.ecr_repository.repository.arn)
        
        # Logging outputs
        pulumi.export("log_group_name", self.ecs_cluster.log_group.name)
        pulumi.export("log_group_arn", self.ecs_cluster.log_group.arn)
        
        # Application URL
        if self.config.domain.has_domain:
            pulumi.export("website_url", f"https://{self.config.domain.apex_domain}")
        else:
            pulumi.export(
                "website_url", 
                self.load_balancer.alb.dns_name.apply(lambda dns: f"http://{dns}")
            )
        
        # Security group IDs for reference
        pulumi.export("alb_security_group_id", self.alb_security_group.security_group.id)
        pulumi.export("ecs_security_group_id", self.ecs_security_group.security_group.id)
        
        # Resource counts for monitoring
        pulumi.export("container_cpu", self.config.container.cpu)
        pulumi.export("container_memory", self.config.container.memory)
        pulumi.export("desired_task_count", self.config.scaling.desired_count)
        pulumi.export("min_task_count", self.config.scaling.min_capacity)
        pulumi.export("max_task_count", self.config.scaling.max_capacity)
    
    def get_stack_info(self) -> Dict[str, Any]:
        """
        Get stack information for monitoring and debugging.
        
        Returns:
            Dictionary with stack information
        """
        return {
            "project_name": self.config.project_name,
            "environment": self.config.environment,
            "aws_region": self.config.aws_region,
            "stack_name": self.config.name_prefix,
            "domain_configured": self.config.domain.has_domain,
            "container_insights_enabled": self.config.enable_container_insights,
            "log_retention_days": self.config.log_retention_days,
            "tags": self.tags
        }