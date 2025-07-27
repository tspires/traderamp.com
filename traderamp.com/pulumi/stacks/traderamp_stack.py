"""
Refactored TradeRamp stack following clean code principles.

- Single Responsibility: Each component has one reason to change
- Open/Closed: Easy to extend without modifying existing code
- Interface Segregation: Components depend on interfaces, not implementations
- Dependency Inversion: High-level modules don't depend on low-level details
"""

from typing import Dict, Any, Optional
import pulumi
from pulumi import Config, Output

from core.interfaces import (
    HealthCheckSpec,
    ScalingSpec,
    ContainerSpec,
    IResourceTagger
)
from core.tagging import StandardTaggingStrategy
from core.validators import ValidationContext, RangeValidator
from providers.aws.networking import VPCComponent, LoadBalancerComponent
from providers.aws.security import SecurityGroupFactory
from providers.aws.compute import FargateServiceComponent
from providers.aws.storage import ContainerRegistryComponent
from providers.aws.certificates import CertificateComponent
from providers.aws.dns import DNSComponent
from providers.aws.cdn import CloudFrontComponent


class TradeRampConfiguration:
    """
    Configuration class following Single Responsibility Principle.
    
    Only responsible for loading and validating configuration.
    """
    
    def __init__(self):
        """Load configuration from Pulumi config."""
        config = Config()
        
        # Basic settings
        self.project_name = config.get("project_name") or "traderamp"
        self.environment = config.get("environment") or "production"
        self.aws_region = config.get("aws:region") or "us-east-1"
        
        # Domain settings
        self.domain_name = config.get("domain_name")
        self.certificate_arn = config.get("certificate_arn")  # For existing certificates
        self.create_dns_records = config.get_bool("create_dns_records") if config.get_bool("create_dns_records") is not None else True
        
        # Container settings
        self.container_spec = ContainerSpec(
            image="nginx:alpine",  # Will be replaced with ECR URL
            cpu_units=config.get_int("container_cpu") or 256,
            memory_mb=config.get_int("container_memory") or 512,
            port=80,
            environment_variables={
                "ENVIRONMENT": self.environment,
                "PROJECT_NAME": self.project_name
            }
        )
        
        # Scaling settings
        self.scaling_spec = ScalingSpec(
            min_instances=config.get_int("min_capacity") or 1,
            max_instances=config.get_int("max_capacity") or 4,
            target_cpu_percent=config.get_float("cpu_target") or 70.0,
            target_memory_percent=config.get_float("memory_target") or 70.0
        )
        
        # Health check settings
        self.health_check_spec = HealthCheckSpec(
            path=config.get("health_check_path") or "/health",
            interval_seconds=config.get_int("health_check_interval") or 30,
            timeout_seconds=config.get_int("health_check_timeout") or 5
        )
        
        # Feature flags
        self.enable_flow_logs = self.environment == "production"
        self.enable_deletion_protection = self.environment == "production"
        self.enable_container_insights = config.get_bool("enable_container_insights") or True
        self.log_retention_days = config.get_int("log_retention_days") or 30
        self.enable_cloudfront = config.get_bool("enable_cloudfront") if config.get_bool("enable_cloudfront") is not None else True
    
    def validate(self) -> None:
        """Validate all configuration."""
        context = ValidationContext()
        
        # Validate log retention
        context.add_validation(
            "log_retention_days",
            RangeValidator(1, 3653, "Log retention days"),
            self.log_retention_days
        )
        
        # Validate specifications
        self.container_spec.validate()
        self.scaling_spec.validate()
        self.health_check_spec.validate()
        
        context.validate_all()
    
    @property
    def resource_prefix(self) -> str:
        """Get resource naming prefix."""
        return f"{self.project_name}-{self.environment}"


class TradeRampStack:
    """
    Main infrastructure stack with clean separation of concerns.
    
    Acts as an orchestrator, delegating actual resource creation to components.
    """
    
    def __init__(self):
        """Initialize TradeRamp infrastructure stack."""
        # Load and validate configuration
        self.config = TradeRampConfiguration()
        self.config.validate()
        
        # Create tagging strategy
        self.tagger = StandardTaggingStrategy(
            project=self.config.project_name,
            environment=self.config.environment,
            owner="TradeRamp Team",
            cost_center="MARKETING"
        )
        
        # Create infrastructure components
        self._create_infrastructure()
        
        # Export outputs
        self._export_outputs()
    
    def _create_infrastructure(self) -> None:
        """Orchestrate infrastructure creation."""
        # 1. Create networking layer
        networking = self._create_networking()
        
        # 2. Create security layer
        security = self._create_security(networking)
        
        # 3. Create storage layer
        storage = self._create_storage()
        
        # 4. Create load balancing layer first (needed for compute)
        load_balancing = self._create_load_balancing(networking, security)
        
        # 5. Create compute layer with load balancer connection
        compute = self._create_compute(networking, security, storage, load_balancing)
        
        # 6. No need to register separately - it's done during creation
        
        # 7. Set up HTTPS if domain is configured or certificate provided
        if self.config.domain_name or self.config.certificate_arn:
            self._setup_https_and_dns(load_balancing)
        
        # 8. Create CloudFront distribution if enabled
        cloudfront = None
        if self.config.enable_cloudfront:
            cloudfront = self._create_cloudfront(load_balancing)
        
        # Store references
        self.networking = networking
        self.security = security
        self.storage = storage
        self.compute = compute
        self.load_balancing = load_balancing
        self.cloudfront = cloudfront
    
    def _create_networking(self) -> Dict[str, Any]:
        """Create networking components."""
        vpc = VPCComponent(
            name=self.config.resource_prefix,
            cidr_block="10.0.0.0/16",
            availability_zone_count=2,
            enable_flow_logs=self.config.enable_flow_logs,
            tagger=self.tagger
        )
        
        return {
            "vpc": vpc,
            "vpc_id": vpc.get_outputs()["vpc_id"],
            "subnet_ids": vpc.get_outputs()["subnet_ids"]
        }
    
    def _create_security(self, networking: Dict[str, Any]) -> Dict[str, Any]:
        """Create security components."""
        factory = SecurityGroupFactory(
            vpc_id=networking["vpc_id"],
            tagger=self.tagger
        )
        
        # Create ALB security group
        alb_sg = factory.create_alb_security_group(
            name=f"{self.config.resource_prefix}-alb"
        )
        
        # Create ECS security group
        ecs_sg = factory.create_ecs_security_group(
            name=f"{self.config.resource_prefix}-ecs",
            alb_security_group_id=alb_sg.get_outputs()["security_group_id"]
        )
        
        return {
            "alb_security_group": alb_sg,
            "ecs_security_group": ecs_sg,
            "alb_sg_id": alb_sg.get_outputs()["security_group_id"],
            "ecs_sg_id": ecs_sg.get_outputs()["security_group_id"]
        }
    
    def _create_storage(self) -> Dict[str, Any]:
        """Create storage components."""
        ecr = ContainerRegistryComponent(
            name=self.config.resource_prefix,
            enable_image_scanning=True,
            max_image_count=15 if self.config.environment == "production" else 5,
            tagger=self.tagger
        )
        
        return {
            "ecr": ecr,
            "repository_url": ecr.get_outputs()["repository_url"]
        }
    
    def _create_compute(
        self,
        networking: Dict[str, Any],
        security: Dict[str, Any],
        storage: Dict[str, Any],
        load_balancing: LoadBalancerComponent
    ) -> FargateServiceComponent:
        """Create compute components."""
        # Update container spec with actual ECR image
        self.config.container_spec.image = storage["repository_url"].apply(
            lambda url: f"{url}:latest"
        )
        
        # Create Fargate service with target group
        return FargateServiceComponent(
            name=self.config.resource_prefix,
            vpc_id=networking["vpc_id"],
            subnet_ids=networking["subnet_ids"],
            security_group_ids=[security["ecs_sg_id"]],
            container_spec=self.config.container_spec,
            scaling_spec=self.config.scaling_spec,
            enable_container_insights=self.config.enable_container_insights,
            log_retention_days=self.config.log_retention_days,
            target_group_arn=load_balancing.target_group_arn,
            tagger=self.tagger
        )
    
    def _create_load_balancing(
        self,
        networking: Dict[str, Any],
        security: Dict[str, Any]
    ) -> LoadBalancerComponent:
        """Create load balancing components."""
        return LoadBalancerComponent(
            name=self.config.resource_prefix,
            vpc_id=networking["vpc_id"],
            subnet_ids=networking["subnet_ids"],
            security_group_ids=[security["alb_sg_id"]],
            health_check=self.config.health_check_spec,
            enable_deletion_protection=self.config.enable_deletion_protection,
            tagger=self.tagger
        )
    
    def _setup_https_and_dns(self, load_balancing: LoadBalancerComponent) -> None:
        """Set up HTTPS and DNS if domain is configured."""
        # Use existing certificate ARN if provided, otherwise create new
        if self.config.certificate_arn:
            certificate_arn = self.config.certificate_arn
            self.certificate_arn = certificate_arn  # Store for CloudFront
            pulumi.log.info(f"Using existing certificate: {certificate_arn}")
        else:
            # Create certificate
            cert = CertificateComponent(
                name=self.config.resource_prefix,
                domain_name=self.config.domain_name,
                tagger=self.tagger
            )
            certificate_arn = cert.get_outputs()["certificate_arn"]
            self.certificate_arn = certificate_arn  # Store for CloudFront
        
        # Add HTTPS listener
        load_balancing.create_https_listener(
            certificate_arn=certificate_arn
        )
        
        # Create DNS records - but only if NOT using CloudFront
        # (CloudFront DNS will be configured separately)
        if self.config.create_dns_records and not self.config.enable_cloudfront:
            dns = DNSComponent(
                name=self.config.resource_prefix,
                domain_name=self.config.domain_name,
                tagger=self.tagger
            )
            
            dns.create_alias_record(
                record_name=self.config.domain_name,
                alias_name=load_balancing.get_outputs()["alb_dns_name"],
                alias_zone_id=load_balancing.get_outputs()["alb_zone_id"]
            )
    
    def _create_cloudfront(self, load_balancing: LoadBalancerComponent) -> CloudFrontComponent:
        """Create CloudFront distribution."""
        # Prepare domain aliases if using custom domain
        domain_aliases = []
        if self.config.domain_name:
            domain_aliases = [self.config.domain_name]
            # Also add www subdomain
            if not self.config.domain_name.startswith("www."):
                domain_aliases.append(f"www.{self.config.domain_name}")
        
        # Create CloudFront distribution
        cloudfront = CloudFrontComponent(
            name=self.config.resource_prefix,
            origin_domain_name=load_balancing.get_outputs()["alb_dns_name"],
            certificate_arn=getattr(self, 'certificate_arn', None),
            domain_aliases=domain_aliases if self.config.domain_name else None,
            enable_ipv6=True,
            price_class="PriceClass_100",  # US, Canada, Europe
            tagger=self.tagger
        )
        
        # Create DNS records pointing to CloudFront
        if self.config.create_dns_records and self.config.domain_name:
            dns = DNSComponent(
                name=self.config.resource_prefix,
                domain_name=self.config.domain_name,
                tagger=self.tagger
            )
            
            # Create alias record for root domain
            dns.create_alias_record(
                record_name=self.config.domain_name,
                alias_name=cloudfront.get_outputs()["distribution_domain_name"],
                alias_zone_id=cloudfront.get_outputs()["distribution_hosted_zone_id"],
                is_cloudfront=True
            )
            
            # Create alias record for www subdomain if not already www
            if not self.config.domain_name.startswith("www."):
                dns.create_alias_record(
                    record_name=f"www.{self.config.domain_name}",
                    alias_name=cloudfront.get_outputs()["distribution_domain_name"],
                    alias_zone_id=cloudfront.get_outputs()["distribution_hosted_zone_id"],
                    is_cloudfront=True
                )
        
        return cloudfront
    
    def _export_outputs(self) -> None:
        """Export stack outputs."""
        # Networking outputs
        pulumi.export("vpc_id", self.networking["vpc_id"])
        pulumi.export("subnet_ids", self.networking["subnet_ids"])
        
        # Security outputs
        pulumi.export("alb_security_group_id", self.security["alb_sg_id"])
        pulumi.export("ecs_security_group_id", self.security["ecs_sg_id"])
        
        # Storage outputs
        pulumi.export("ecr_repository_url", self.storage["repository_url"])
        
        # Load balancing outputs
        lb_outputs = self.load_balancing.get_outputs()
        pulumi.export("alb_dns_name", lb_outputs["alb_dns_name"])
        pulumi.export("target_group_arn", lb_outputs["target_group_arn"])
        
        # Compute outputs
        compute_outputs = self.compute.get_outputs()
        pulumi.export("ecs_cluster_name", compute_outputs["cluster_name"])
        pulumi.export("ecs_service_name", compute_outputs["service_name"])
        
        # CloudFront outputs if enabled
        if self.cloudfront:
            cf_outputs = self.cloudfront.get_outputs()
            pulumi.export("cloudfront_distribution_id", cf_outputs["distribution_id"])
            pulumi.export("cloudfront_domain_name", cf_outputs["distribution_domain_name"])
        
        # Application URL
        if self.config.enable_cloudfront and self.cloudfront:
            if self.config.domain_name:
                pulumi.export("website_url", f"https://{self.config.domain_name}")
            else:
                cf_outputs = self.cloudfront.get_outputs()
                pulumi.export("website_url",
                    cf_outputs["distribution_domain_name"].apply(lambda dns: f"https://{dns}")
                )
        else:
            if self.config.domain_name:
                pulumi.export("website_url", f"https://{self.config.domain_name}")
            else:
                pulumi.export("website_url", 
                    lb_outputs["alb_dns_name"].apply(lambda dns: f"http://{dns}")
                )