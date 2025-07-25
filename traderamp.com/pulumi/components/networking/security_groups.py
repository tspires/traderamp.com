"""Security group components for TradeRamp infrastructure."""

from typing import List, Optional, Dict, Union
from dataclasses import dataclass, field
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions, Output, Input

from config.constants import Port, Protocol, NetworkCIDR


@dataclass
class SecurityRule:
    """Security group rule configuration."""
    
    protocol: Protocol
    from_port: int
    to_port: int
    description: str
    cidr_blocks: Optional[List[str]] = None
    ipv6_cidr_blocks: Optional[List[str]] = None
    source_security_group_id: Optional[Input[str]] = None
    self: Optional[bool] = None
    
    def __post_init__(self) -> None:
        """Validate rule configuration."""
        if not any([self.cidr_blocks, self.ipv6_cidr_blocks, 
                   self.source_security_group_id, self.self]):
            raise ValueError(
                "At least one of cidr_blocks, ipv6_cidr_blocks, "
                "source_security_group_id, or self must be specified"
            )
        
        if self.from_port > self.to_port:
            raise ValueError(f"from_port ({self.from_port}) cannot be greater than to_port ({self.to_port})")


class SecurityGroupComponent(ComponentResource):
    """Enhanced security group component with proper rule management."""
    
    def __init__(
        self,
        name: str,
        vpc_id: Input[str],
        description: str,
        ingress_rules: List[SecurityRule] = None,
        egress_rules: List[SecurityRule] = None,
        tags: Dict[str, str] = None,
        opts: ResourceOptions = None
    ) -> None:
        """
        Initialize security group component.
        
        Args:
            name: Security group name
            vpc_id: VPC ID where the security group will be created
            description: Security group description
            ingress_rules: List of ingress rules
            egress_rules: List of egress rules (if None, defaults to allow all)
            tags: Resource tags
            opts: Pulumi resource options
        """
        super().__init__("traderamp:networking:SecurityGroup", name, None, opts)
        
        self.name = name
        self.vpc_id = vpc_id
        self.description = description
        self.ingress_rules = ingress_rules or []
        self.egress_rules = egress_rules
        self.tags = tags or {}
        
        # Create security group
        self.security_group = self._create_security_group()
        
        # Create rules
        self._create_ingress_rules()
        self._create_egress_rules()
        
        # Register outputs
        self.register_outputs({
            "security_group_id": self.security_group.id,
            "security_group_name": self.security_group.name
        })
    
    def _create_security_group(self) -> aws.ec2.SecurityGroup:
        """Create the security group."""
        return aws.ec2.SecurityGroup(
            self.name,
            vpc_id=self.vpc_id,
            description=self.description,
            # Don't use inline rules - we'll create them separately
            tags={
                **self.tags,
                "Name": self.name
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_ingress_rules(self) -> None:
        """Create ingress rules."""
        for i, rule in enumerate(self.ingress_rules):
            rule_name = f"{self.name}-ingress-{i}"
            self._create_rule(rule_name, rule, "ingress")
    
    def _create_egress_rules(self) -> None:
        """Create egress rules."""
        if self.egress_rules is None:
            # Default: Allow all outbound traffic
            self.egress_rules = [
                SecurityRule(
                    protocol=Protocol.ALL,
                    from_port=0,
                    to_port=65535,
                    cidr_blocks=[NetworkCIDR.INTERNET.value],
                    description="Allow all outbound traffic"
                )
            ]
        
        for i, rule in enumerate(self.egress_rules):
            rule_name = f"{self.name}-egress-{i}"
            self._create_rule(rule_name, rule, "egress")
    
    def _create_rule(self, name: str, rule: SecurityRule, rule_type: str) -> aws.ec2.SecurityGroupRule:
        """Create individual security group rule."""
        return aws.ec2.SecurityGroupRule(
            name,
            type=rule_type,
            security_group_id=self.security_group.id,
            protocol=rule.protocol.value,
            from_port=rule.from_port,
            to_port=rule.to_port,
            cidr_blocks=rule.cidr_blocks,
            ipv6_cidr_blocks=rule.ipv6_cidr_blocks,
            source_security_group_id=rule.source_security_group_id,
            self=rule.self,
            description=rule.description,
            opts=ResourceOptions(parent=self)
        )


def create_alb_security_group(
    name: str,
    vpc_id: Input[str],
    allow_http: bool = True,
    allow_https: bool = True,
    additional_ingress_rules: List[SecurityRule] = None,
    tags: Dict[str, str] = None
) -> SecurityGroupComponent:
    """
    Create a security group for Application Load Balancer.
    
    Args:
        name: Base name for the security group
        vpc_id: VPC ID
        allow_http: Allow HTTP traffic (port 80)
        allow_https: Allow HTTPS traffic (port 443)
        additional_ingress_rules: Additional ingress rules
        tags: Resource tags
    
    Returns:
        SecurityGroupComponent instance
    """
    ingress_rules = []
    
    if allow_http:
        ingress_rules.append(
            SecurityRule(
                protocol=Protocol.TCP,
                from_port=Port.HTTP,
                to_port=Port.HTTP,
                cidr_blocks=[NetworkCIDR.INTERNET.value],
                description="Allow HTTP from anywhere"
            )
        )
    
    if allow_https:
        ingress_rules.append(
            SecurityRule(
                protocol=Protocol.TCP,
                from_port=Port.HTTPS,
                to_port=Port.HTTPS,
                cidr_blocks=[NetworkCIDR.INTERNET.value],
                description="Allow HTTPS from anywhere"
            )
        )
    
    if additional_ingress_rules:
        ingress_rules.extend(additional_ingress_rules)
    
    # ALB needs to reach targets, so allow outbound HTTP to VPC
    egress_rules = [
        SecurityRule(
            protocol=Protocol.TCP,
            from_port=Port.HTTP,
            to_port=Port.HTTP,
            cidr_blocks=[NetworkCIDR.VPC.value],
            description="Allow HTTP to VPC for health checks"
        )
    ]
    
    return SecurityGroupComponent(
        name=f"{name}-alb-sg",
        vpc_id=vpc_id,
        description="Security group for Application Load Balancer",
        ingress_rules=ingress_rules,
        egress_rules=egress_rules,
        tags=tags
    )


def create_ecs_security_group(
    name: str,
    vpc_id: Input[str],
    alb_security_group_id: Input[str],
    container_port: int = Port.HTTP,
    allow_all_egress: bool = False,
    additional_egress_cidrs: List[str] = None,
    tags: Dict[str, str] = None
) -> SecurityGroupComponent:
    """
    Create a security group for ECS tasks.
    
    Args:
        name: Base name for the security group
        vpc_id: VPC ID
        alb_security_group_id: Security group ID of the ALB
        container_port: Port the container listens on
        allow_all_egress: Whether to allow all outbound traffic
        additional_egress_cidrs: Additional CIDR blocks for egress
        tags: Resource tags
    
    Returns:
        SecurityGroupComponent instance
    """
    # Only allow traffic from ALB
    ingress_rules = [
        SecurityRule(
            protocol=Protocol.TCP,
            from_port=container_port,
            to_port=container_port,
            source_security_group_id=alb_security_group_id,
            description="Allow traffic from ALB"
        )
    ]
    
    # Configure egress rules
    if allow_all_egress:
        egress_rules = None  # Will use default (allow all)
    else:
        # Restrictive egress - only allow what's needed
        egress_rules = [
            # HTTPS for external APIs
            SecurityRule(
                protocol=Protocol.TCP,
                from_port=Port.HTTPS,
                to_port=Port.HTTPS,
                cidr_blocks=[NetworkCIDR.INTERNET.value],
                description="Allow HTTPS for external API calls"
            ),
            # DNS
            SecurityRule(
                protocol=Protocol.UDP,
                from_port=53,
                to_port=53,
                cidr_blocks=[NetworkCIDR.VPC.value],
                description="Allow DNS lookups"
            ),
            SecurityRule(
                protocol=Protocol.TCP,
                from_port=53,
                to_port=53,
                cidr_blocks=[NetworkCIDR.VPC.value],
                description="Allow DNS lookups (TCP)"
            )
        ]
        
        # Add ECR endpoints for image pulls
        ecr_cidrs = [
            "52.94.0.0/20",    # us-east-1 ECR
            "52.119.0.0/20",   # us-east-1 ECR
        ]
        for cidr in ecr_cidrs:
            egress_rules.append(
                SecurityRule(
                    protocol=Protocol.TCP,
                    from_port=Port.HTTPS,
                    to_port=Port.HTTPS,
                    cidr_blocks=[cidr],
                    description="Allow ECR image pulls"
                )
            )
        
        # Add any additional egress CIDRs
        if additional_egress_cidrs:
            for cidr in additional_egress_cidrs:
                egress_rules.append(
                    SecurityRule(
                        protocol=Protocol.TCP,
                        from_port=Port.HTTPS,
                        to_port=Port.HTTPS,
                        cidr_blocks=[cidr],
                        description="Additional egress rule"
                    )
                )
    
    return SecurityGroupComponent(
        name=f"{name}-ecs-sg",
        vpc_id=vpc_id,
        description="Security group for ECS tasks",
        ingress_rules=ingress_rules,
        egress_rules=egress_rules,
        tags=tags
    )