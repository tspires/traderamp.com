"""
AWS Security Group components following clean code principles.
"""

from typing import List, Dict, Optional, Any
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Output, Input

from core.base_component import BaseInfrastructureComponent
from core.validators import ValidationContext, ListLengthValidator


class SecurityRule:
    """Represents a security group rule."""
    
    def __init__(
        self,
        protocol: str,
        from_port: int,
        to_port: int,
        cidr_blocks: Optional[List[str]] = None,
        source_security_group_id: Optional[Input[str]] = None,
        description: str = ""
    ):
        """Initialize security rule."""
        self.protocol = protocol
        self.from_port = from_port
        self.to_port = to_port
        self.cidr_blocks = cidr_blocks
        self.source_security_group_id = source_security_group_id
        self.description = description


class SecurityGroupComponent(BaseInfrastructureComponent):
    """
    Security group component with clean separation of concerns.
    """
    
    def __init__(
        self,
        name: str,
        vpc_id: Input[str],
        description: str,
        ingress_rules: List[SecurityRule] = None,
        egress_rules: List[SecurityRule] = None,
        **kwargs
    ):
        """Initialize security group component."""
        self.vpc_id = vpc_id
        self.description = description
        self.ingress_rules = ingress_rules or []
        self.egress_rules = egress_rules or []
        
        super().__init__(
            "traderamp:aws:security:SecurityGroup",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate security group configuration."""
        # Basic validation - can be extended
        pass
    
    def create_resources(self) -> None:
        """Create security group resources."""
        # Create security group
        sg = aws.ec2.SecurityGroup(
            f"{self.name}-sg",
            vpc_id=self.vpc_id,
            description=self.description,
            tags=self.get_tags("SecurityGroup", f"{self.name}-sg"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("security_group", sg)
        
        # Create ingress rules
        for i, rule in enumerate(self.ingress_rules):
            self._create_rule(f"ingress-{i}", rule, "ingress", sg.id)
        
        # Create egress rules
        if not self.egress_rules:
            # Default: allow all outbound
            self._create_rule(
                "egress-default",
                SecurityRule("all", 0, 65535, ["0.0.0.0/0"], description="Allow all outbound"),
                "egress",
                sg.id
            )
        else:
            for i, rule in enumerate(self.egress_rules):
                self._create_rule(f"egress-{i}", rule, "egress", sg.id)
    
    def _create_rule(
        self,
        name: str,
        rule: SecurityRule,
        rule_type: str,
        security_group_id: Input[str]
    ) -> None:
        """Create a security group rule."""
        aws.ec2.SecurityGroupRule(
            f"{self.name}-{name}",
            type=rule_type,
            security_group_id=security_group_id,
            protocol=rule.protocol,
            from_port=rule.from_port,
            to_port=rule.to_port,
            cidr_blocks=rule.cidr_blocks,
            source_security_group_id=rule.source_security_group_id,
            description=rule.description,
            opts=ResourceOptions(parent=self)
        )
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        sg = self.get_resource("security_group")
        return {
            "security_group_id": sg.id,
            "security_group_name": sg.name
        }


class SecurityGroupFactory:
    """Factory for creating common security group configurations."""
    
    def __init__(self, vpc_id: Input[str], tagger=None):
        """Initialize security group factory."""
        self.vpc_id = vpc_id
        self.tagger = tagger
    
    def create_alb_security_group(self, name: str) -> SecurityGroupComponent:
        """Create security group for Application Load Balancer."""
        ingress_rules = [
            SecurityRule("tcp", 80, 80, ["0.0.0.0/0"], description="Allow HTTP"),
            SecurityRule("tcp", 443, 443, ["0.0.0.0/0"], description="Allow HTTPS")
        ]
        
        # ALB needs to reach anywhere for health checks
        egress_rules = [
            SecurityRule("tcp", 80, 80, ["0.0.0.0/0"], description="Allow HTTP outbound")
        ]
        
        return SecurityGroupComponent(
            name=name,
            vpc_id=self.vpc_id,
            description="Security group for Application Load Balancer",
            ingress_rules=ingress_rules,
            egress_rules=egress_rules,
            tagger=self.tagger
        )
    
    def create_ecs_security_group(
        self,
        name: str,
        alb_security_group_id: Input[str]
    ) -> SecurityGroupComponent:
        """Create security group for ECS tasks."""
        ingress_rules = [
            SecurityRule(
                "tcp", 80, 80,
                source_security_group_id=alb_security_group_id,
                description="Allow traffic from ALB"
            )
        ]
        
        # ECS tasks need outbound access for image pulls and external APIs
        egress_rules = None  # Use default (allow all)
        
        return SecurityGroupComponent(
            name=name,
            vpc_id=self.vpc_id,
            description="Security group for ECS tasks",
            ingress_rules=ingress_rules,
            egress_rules=egress_rules,
            tagger=self.tagger
        )