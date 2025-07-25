"""Application Load Balancer component for TradeRamp infrastructure."""

from typing import List, Dict, Optional, Any
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions, Output, Input

from config.constants import (
    Port, Protocol, TargetType, HealthCheckProtocol, 
    Defaults, AWSLimits
)
from config.settings import HealthCheckConfig, DomainConfig


class LoadBalancerComponent(ComponentResource):
    """
    Application Load Balancer component with HTTPS support.
    
    This component creates:
    - Application Load Balancer
    - Target Group with health checks
    - HTTP listener (redirect to HTTPS)
    - HTTPS listener (if certificate provided)
    - DNS records (if domain configured)
    """
    
    def __init__(
        self,
        name: str,
        vpc_id: Input[str],
        subnet_ids: List[Input[str]],
        security_group_ids: List[Input[str]],
        health_check_config: HealthCheckConfig,
        domain_config: Optional[DomainConfig] = None,
        enable_deletion_protection: bool = False,
        enable_http2: bool = True,
        idle_timeout: int = 60,
        tags: Dict[str, str] = None,
        opts: ResourceOptions = None
    ) -> None:
        """
        Initialize Load Balancer component.
        
        Args:
            name: Component name
            vpc_id: VPC ID for target group
            subnet_ids: List of subnet IDs (minimum 2)
            security_group_ids: List of security group IDs
            health_check_config: Health check configuration
            domain_config: Domain configuration for SSL/DNS
            enable_deletion_protection: Enable deletion protection
            enable_http2: Enable HTTP/2
            idle_timeout: Idle timeout in seconds
            tags: Resource tags
            opts: Pulumi resource options
        """
        super().__init__("traderamp:networking:LoadBalancer", name, None, opts)
        
        self.name = name
        self.vpc_id = vpc_id
        self.subnet_ids = subnet_ids
        self.security_group_ids = security_group_ids
        self.health_check_config = health_check_config
        self.domain_config = domain_config
        self.tags = tags or {}
        
        # Validate inputs
        if len(subnet_ids) < 2:
            raise ValueError("ALB requires at least 2 subnets in different AZs")
        
        # Create resources
        self.alb = self._create_alb(
            enable_deletion_protection, 
            enable_http2, 
            idle_timeout
        )
        self.target_group = self._create_target_group()
        self.http_listener = self._create_http_listener()
        
        # Handle HTTPS and DNS if domain is configured
        if domain_config and domain_config.has_domain:
            self._setup_https_and_dns()
        
        # Register outputs
        self.register_outputs({
            "alb_arn": self.alb.arn,
            "alb_dns_name": self.alb.dns_name,
            "alb_zone_id": self.alb.zone_id,
            "target_group_arn": self.target_group.arn,
            "target_group_name": self.target_group.name
        })
    
    def _create_alb(
        self, 
        enable_deletion_protection: bool,
        enable_http2: bool,
        idle_timeout: int
    ) -> aws.lb.LoadBalancer:
        """Create Application Load Balancer."""
        return aws.lb.LoadBalancer(
            f"{self.name}-alb",
            load_balancer_type="application",
            subnets=self.subnet_ids,
            security_groups=self.security_group_ids,
            enable_deletion_protection=enable_deletion_protection,
            enable_http2=enable_http2,
            idle_timeout=idle_timeout,
            access_logs={
                "enabled": False  # Can be enabled with S3 bucket
            },
            tags={
                **self.tags,
                "Name": f"{self.name}-alb"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_target_group(self) -> aws.lb.TargetGroup:
        """Create target group with health checks."""
        return aws.lb.TargetGroup(
            f"{self.name}-tg",
            port=Port.HTTP,
            protocol=HealthCheckProtocol.HTTP.value,
            vpc_id=self.vpc_id,
            target_type=TargetType.IP.value,  # For Fargate
            deregistration_delay=Defaults.DEREGISTRATION_DELAY,
            health_check={
                "enabled": True,
                "path": self.health_check_config.path,
                "protocol": HealthCheckProtocol.HTTP.value,
                "port": "traffic-port",
                "interval": self.health_check_config.interval,
                "timeout": self.health_check_config.timeout,
                "healthy_threshold": self.health_check_config.healthy_threshold,
                "unhealthy_threshold": self.health_check_config.unhealthy_threshold,
                "matcher": "200-299"
            },
            stickiness={
                "enabled": False,  # Can be enabled if needed
                "type": "lb_cookie"
            },
            tags={
                **self.tags,
                "Name": f"{self.name}-tg"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_http_listener(self) -> aws.lb.Listener:
        """Create HTTP listener with HTTPS redirect."""
        return aws.lb.Listener(
            f"{self.name}-http-listener",
            load_balancer_arn=self.alb.arn,
            port=Port.HTTP,
            protocol=Protocol.TCP.value.upper(),
            default_actions=[{
                "type": "redirect",
                "redirect": {
                    "port": str(Port.HTTPS),
                    "protocol": "HTTPS",
                    "status_code": "HTTP_301"
                }
            }],
            opts=ResourceOptions(parent=self)
        )
    
    def _setup_https_and_dns(self) -> None:
        """Set up HTTPS listener and DNS records."""
        if not self.domain_config:
            return
        
        # Get hosted zone
        try:
            hosted_zone = aws.route53.get_zone(
                name=self.domain_config.apex_domain,
                private_zone=False
            )
        except Exception as e:
            pulumi.log.warn(
                f"Could not find Route53 hosted zone for {self.domain_config.apex_domain}: {e}. "
                "Skipping HTTPS and DNS setup."
            )
            return
        
        # Create ACM certificate
        certificate = self._create_certificate(hosted_zone)
        
        # Create HTTPS listener
        self.https_listener = aws.lb.Listener(
            f"{self.name}-https-listener",
            load_balancer_arn=self.alb.arn,
            port=Port.HTTPS,
            protocol=Protocol.TCP.value.upper(),
            ssl_policy=self.domain_config.ssl_policy,
            certificate_arn=certificate.arn,
            default_actions=[{
                "type": "forward",
                "target_group_arn": self.target_group.arn
            }],
            opts=ResourceOptions(parent=self, depends_on=[certificate])
        )
        
        # Create DNS records
        if self.domain_config.create_dns_records:
            self._create_dns_records(hosted_zone)
    
    def _create_certificate(self, hosted_zone: Any) -> aws.acm.Certificate:
        """Create and validate ACM certificate."""
        # Request certificate
        certificate = aws.acm.Certificate(
            f"{self.name}-cert",
            domain_name=self.domain_config.apex_domain,
            subject_alternative_names=[
                self.domain_config.www_domain
            ] if self.domain_config.apex_domain != self.domain_config.www_domain else [],
            validation_method="DNS",
            tags={
                **self.tags,
                "Name": f"{self.name}-cert"
            },
            opts=ResourceOptions(parent=self)
        )
        
        # Create validation records
        validation_records = []
        for i in range(2):  # One for apex, one for www
            record = aws.route53.Record(
                f"{self.name}-cert-validation-{i}",
                zone_id=hosted_zone.id,
                name=certificate.domain_validation_options[i].resource_record_name,
                type=certificate.domain_validation_options[i].resource_record_type,
                ttl=60,
                records=[certificate.domain_validation_options[i].resource_record_value],
                allow_overwrite=True,
                opts=ResourceOptions(parent=self)
            )
            validation_records.append(record)
        
        # Wait for validation
        aws.acm.CertificateValidation(
            f"{self.name}-cert-validation",
            certificate_arn=certificate.arn,
            validation_record_fqdns=[r.fqdn for r in validation_records],
            opts=ResourceOptions(parent=self, depends_on=validation_records)
        )
        
        return certificate
    
    def _create_dns_records(self, hosted_zone: Any) -> None:
        """Create DNS A records for the domain."""
        # Apex domain
        aws.route53.Record(
            f"{self.name}-dns-apex",
            zone_id=hosted_zone.id,
            name=self.domain_config.apex_domain,
            type="A",
            aliases=[{
                "name": self.alb.dns_name,
                "zone_id": self.alb.zone_id,
                "evaluate_target_health": True
            }],
            opts=ResourceOptions(parent=self)
        )
        
        # WWW subdomain
        if self.domain_config.apex_domain != self.domain_config.www_domain:
            aws.route53.Record(
                f"{self.name}-dns-www",
                zone_id=hosted_zone.id,
                name=self.domain_config.www_domain,
                type="A",
                aliases=[{
                    "name": self.alb.dns_name,
                    "zone_id": self.alb.zone_id,
                    "evaluate_target_health": True
                }],
                opts=ResourceOptions(parent=self)
            )
    
    def add_listener_rule(
        self,
        name: str,
        priority: int,
        conditions: List[Dict[str, Any]],
        actions: List[Dict[str, Any]],
        listener_arn: Optional[Input[str]] = None
    ) -> aws.lb.ListenerRule:
        """
        Add a rule to the HTTPS listener.
        
        Args:
            name: Rule name
            priority: Rule priority (1-50000)
            conditions: List of conditions
            actions: List of actions
            listener_arn: Override listener ARN
        
        Returns:
            ListenerRule resource
        """
        if priority < 1 or priority > 50000:
            raise ValueError("Priority must be between 1 and 50000")
        
        listener = listener_arn or (
            self.https_listener.arn if hasattr(self, 'https_listener') 
            else self.http_listener.arn
        )
        
        return aws.lb.ListenerRule(
            f"{self.name}-{name}-rule",
            listener_arn=listener,
            priority=priority,
            conditions=conditions,
            actions=actions,
            opts=ResourceOptions(parent=self)
        )