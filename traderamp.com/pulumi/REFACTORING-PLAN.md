# Pulumi Infrastructure Refactoring Plan

## Overview

This document outlines the recommended refactoring to improve code quality, maintainability, and security of the TradeRamp Pulumi infrastructure.

## Current Issues

### 1. Code Organization
- **Problem**: Single 486-line monolithic file
- **Impact**: Difficult to maintain, test, and collaborate

### 2. Clean Code Violations
- No type hints
- Poor error handling
- Magic numbers and strings
- Inconsistent naming
- Missing documentation

### 3. Architectural Problems
- No separation of concerns
- Missing abstraction layers
- Tight coupling
- No modularity

### 4. Security Concerns
- Overly permissive security groups
- Outdated SSL policies
- No secrets management
- Missing encryption

## Proposed Structure

```
pulumi/
├── __main__.py              # Entry point (minimal)
├── requirements.txt         # Dependencies
├── config/
│   ├── __init__.py
│   ├── settings.py         # Configuration management
│   └── constants.py        # Constants and enums
├── components/
│   ├── __init__.py
│   ├── networking/
│   │   ├── __init__.py
│   │   ├── vpc.py         # VPC component
│   │   ├── security_groups.py
│   │   └── load_balancer.py
│   ├── compute/
│   │   ├── __init__.py
│   │   ├── ecs_cluster.py
│   │   ├── ecs_service.py
│   │   └── auto_scaling.py
│   ├── storage/
│   │   ├── __init__.py
│   │   └── ecr.py
│   └── monitoring/
│       ├── __init__.py
│       └── cloudwatch.py
├── stacks/
│   ├── __init__.py
│   └── traderamp_stack.py  # Main stack composition
├── utils/
│   ├── __init__.py
│   ├── tagging.py          # Tag management
│   └── validation.py       # Input validation
└── tests/
    ├── __init__.py
    ├── test_networking.py
    ├── test_compute.py
    └── test_integration.py
```

## Refactoring Steps

### Phase 1: Extract Configuration (Priority: High)

Create `config/settings.py`:

```python
"""Configuration management for TradeRamp infrastructure."""

from dataclasses import dataclass
from typing import Optional
from pulumi import Config


@dataclass
class ContainerConfig:
    """Container resource configuration."""
    cpu: int = 256
    memory: int = 512
    
    def validate(self) -> None:
        """Validate container configuration."""
        if self.cpu not in [256, 512, 1024, 2048, 4096]:
            raise ValueError(f"Invalid CPU value: {self.cpu}")
        if self.memory < 512 or self.memory > 30720:
            raise ValueError(f"Invalid memory value: {self.memory}")


@dataclass
class ScalingConfig:
    """Auto-scaling configuration."""
    desired_count: int = 2
    min_capacity: int = 1
    max_capacity: int = 4
    cpu_target: float = 70.0
    memory_target: float = 70.0
    
    def validate(self) -> None:
        """Validate scaling configuration."""
        if self.min_capacity > self.max_capacity:
            raise ValueError("min_capacity cannot be greater than max_capacity")
        if self.desired_count < self.min_capacity or self.desired_count > self.max_capacity:
            raise ValueError("desired_count must be between min and max capacity")


@dataclass
class InfrastructureConfig:
    """Main infrastructure configuration."""
    environment: str
    project_name: str
    domain_name: Optional[str]
    container: ContainerConfig
    scaling: ScalingConfig
    
    @classmethod
    def from_pulumi_config(cls) -> 'InfrastructureConfig':
        """Load configuration from Pulumi config."""
        config = Config()
        
        container_config = ContainerConfig(
            cpu=config.get_int("container_cpu") or 256,
            memory=config.get_int("container_memory") or 512
        )
        
        scaling_config = ScalingConfig(
            desired_count=config.get_int("desired_count") or 2,
            min_capacity=config.get_int("min_capacity") or 1,
            max_capacity=config.get_int("max_capacity") or 4
        )
        
        return cls(
            environment=config.get("environment") or "production",
            project_name="traderamp",
            domain_name=config.get("domain"),
            container=container_config,
            scaling=scaling_config
        )
    
    def validate(self) -> None:
        """Validate all configuration."""
        self.container.validate()
        self.scaling.validate()
```

Create `config/constants.py`:

```python
"""Constants for TradeRamp infrastructure."""

from enum import Enum


class HealthCheckPath(str, Enum):
    """Health check paths."""
    DEFAULT = "/health"
    
    
class SSLPolicy(str, Enum):
    """SSL/TLS policies."""
    RECOMMENDED_2023 = "ELBSecurityPolicy-TLS13-1-2-2021-06"
    COMPATIBLE_2021 = "ELBSecurityPolicy-TLS-1-2-2017-01"
    

class NetworkCIDR(str, Enum):
    """Network CIDR blocks."""
    VPC = "10.0.0.0/16"
    PUBLIC_SUBNET_1 = "10.0.1.0/24"
    PUBLIC_SUBNET_2 = "10.0.2.0/24"
    INTERNET = "0.0.0.0/0"


class HealthCheckConfig:
    """Health check configuration constants."""
    INTERVAL = 30
    TIMEOUT = 5
    HEALTHY_THRESHOLD = 2
    UNHEALTHY_THRESHOLD = 3
    GRACE_PERIOD = 60
    

class AutoScalingConfig:
    """Auto-scaling configuration constants."""
    SCALE_IN_COOLDOWN = 300
    SCALE_OUT_COOLDOWN = 60
    CPU_TARGET_DEFAULT = 70.0
    MEMORY_TARGET_DEFAULT = 70.0
```

### Phase 2: Extract Components (Priority: High)

Create `components/networking/vpc.py`:

```python
"""VPC component for TradeRamp infrastructure."""

from typing import List, Dict, Any
import pulumi
import pulumi_aws as aws
from dataclasses import dataclass

from config.constants import NetworkCIDR


@dataclass
class VPCConfig:
    """VPC configuration."""
    name: str
    cidr_block: str = NetworkCIDR.VPC.value
    availability_zones: int = 2
    tags: Dict[str, str] = None


class VPCComponent(pulumi.ComponentResource):
    """VPC component with public subnets."""
    
    def __init__(
        self,
        name: str,
        config: VPCConfig,
        opts: pulumi.ResourceOptions = None
    ) -> None:
        """Initialize VPC component."""
        super().__init__("traderamp:networking:VPC", name, None, opts)
        
        self.config = config
        self.vpc = self._create_vpc()
        self.igw = self._create_internet_gateway()
        self.public_subnets = self._create_public_subnets()
        self.route_table = self._create_route_table()
        self._associate_subnets()
        
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "public_subnet_ids": [s.id for s in self.public_subnets]
        })
    
    def _create_vpc(self) -> aws.ec2.Vpc:
        """Create VPC resource."""
        return aws.ec2.Vpc(
            f"{self.config.name}-vpc",
            cidr_block=self.config.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={
                **self.config.tags,
                "Name": f"{self.config.name}-vpc"
            },
            opts=pulumi.ResourceOptions(parent=self)
        )
    
    def _create_internet_gateway(self) -> aws.ec2.InternetGateway:
        """Create Internet Gateway."""
        return aws.ec2.InternetGateway(
            f"{self.config.name}-igw",
            vpc_id=self.vpc.id,
            tags={
                **self.config.tags,
                "Name": f"{self.config.name}-igw"
            },
            opts=pulumi.ResourceOptions(parent=self)
        )
    
    def _create_public_subnets(self) -> List[aws.ec2.Subnet]:
        """Create public subnets."""
        azs = aws.get_availability_zones(state="available")
        subnets = []
        
        for i in range(self.config.availability_zones):
            subnet = aws.ec2.Subnet(
                f"{self.config.name}-public-{i+1}",
                vpc_id=self.vpc.id,
                cidr_block=f"10.0.{i+1}.0/24",
                availability_zone=azs.names[i],
                map_public_ip_on_launch=True,
                tags={
                    **self.config.tags,
                    "Name": f"{self.config.name}-public-{i+1}",
                    "Type": "public"
                },
                opts=pulumi.ResourceOptions(parent=self)
            )
            subnets.append(subnet)
        
        return subnets
    
    def _create_route_table(self) -> aws.ec2.RouteTable:
        """Create route table for public subnets."""
        return aws.ec2.RouteTable(
            f"{self.config.name}-public-rt",
            vpc_id=self.vpc.id,
            routes=[{
                "cidr_block": NetworkCIDR.INTERNET.value,
                "gateway_id": self.igw.id
            }],
            tags={
                **self.config.tags,
                "Name": f"{self.config.name}-public-rt"
            },
            opts=pulumi.ResourceOptions(parent=self)
        )
    
    def _associate_subnets(self) -> None:
        """Associate subnets with route table."""
        for i, subnet in enumerate(self.public_subnets):
            aws.ec2.RouteTableAssociation(
                f"{self.config.name}-rta-{i+1}",
                subnet_id=subnet.id,
                route_table_id=self.route_table.id,
                opts=pulumi.ResourceOptions(parent=self)
            )
```

Create `components/networking/security_groups.py`:

```python
"""Security group components."""

from typing import List, Optional
import pulumi
import pulumi_aws as aws
from dataclasses import dataclass, field

from config.constants import NetworkCIDR


@dataclass
class SecurityRule:
    """Security group rule configuration."""
    protocol: str
    from_port: int
    to_port: int
    cidr_blocks: Optional[List[str]] = None
    security_groups: Optional[List[str]] = None
    description: Optional[str] = None


@dataclass
class SecurityGroupConfig:
    """Security group configuration."""
    name: str
    vpc_id: pulumi.Input[str]
    description: str
    ingress_rules: List[SecurityRule] = field(default_factory=list)
    egress_rules: List[SecurityRule] = field(default_factory=list)
    tags: dict = field(default_factory=dict)


class SecurityGroupComponent(pulumi.ComponentResource):
    """Enhanced security group component."""
    
    def __init__(
        self,
        name: str,
        config: SecurityGroupConfig,
        opts: pulumi.ResourceOptions = None
    ) -> None:
        """Initialize security group component."""
        super().__init__("traderamp:networking:SecurityGroup", name, None, opts)
        
        self.config = config
        self.security_group = self._create_security_group()
        self._create_rules()
        
        self.register_outputs({
            "security_group_id": self.security_group.id
        })
    
    def _create_security_group(self) -> aws.ec2.SecurityGroup:
        """Create security group."""
        return aws.ec2.SecurityGroup(
            self.config.name,
            vpc_id=self.config.vpc_id,
            description=self.config.description,
            tags={
                **self.config.tags,
                "Name": self.config.name
            },
            opts=pulumi.ResourceOptions(parent=self)
        )
    
    def _create_rules(self) -> None:
        """Create security group rules."""
        # Create ingress rules
        for i, rule in enumerate(self.config.ingress_rules):
            self._create_rule(f"ingress-{i}", rule, "ingress")
        
        # Create egress rules
        for i, rule in enumerate(self.config.egress_rules):
            self._create_rule(f"egress-{i}", rule, "egress")
    
    def _create_rule(self, name: str, rule: SecurityRule, rule_type: str) -> None:
        """Create individual security group rule."""
        aws.ec2.SecurityGroupRule(
            f"{self.config.name}-{name}",
            type=rule_type,
            security_group_id=self.security_group.id,
            protocol=rule.protocol,
            from_port=rule.from_port,
            to_port=rule.to_port,
            cidr_blocks=rule.cidr_blocks,
            source_security_group_id=rule.security_groups[0] if rule.security_groups else None,
            description=rule.description,
            opts=pulumi.ResourceOptions(parent=self)
        )


def create_alb_security_group(
    name: str,
    vpc_id: pulumi.Input[str],
    tags: dict
) -> SecurityGroupComponent:
    """Create ALB security group with standard rules."""
    config = SecurityGroupConfig(
        name=f"{name}-alb-sg",
        vpc_id=vpc_id,
        description="Security group for Application Load Balancer",
        ingress_rules=[
            SecurityRule(
                protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=[NetworkCIDR.INTERNET.value],
                description="Allow HTTP from anywhere"
            ),
            SecurityRule(
                protocol="tcp",
                from_port=443,
                to_port=443,
                cidr_blocks=[NetworkCIDR.INTERNET.value],
                description="Allow HTTPS from anywhere"
            )
        ],
        egress_rules=[
            SecurityRule(
                protocol="tcp",
                from_port=80,
                to_port=80,
                cidr_blocks=[NetworkCIDR.VPC.value],
                description="Allow HTTP to VPC"
            )
        ],
        tags=tags
    )
    
    return SecurityGroupComponent(f"{name}-alb-sg", config)
```

### Phase 3: Create Stack Composition (Priority: High)

Create `stacks/traderamp_stack.py`:

```python
"""Main TradeRamp infrastructure stack."""

from typing import Dict, Any
import pulumi
from pulumi import Output

from config.settings import InfrastructureConfig
from components.networking import VPCComponent, create_alb_security_group
from components.compute import ECSCluster, ECSService
from components.storage import ECRRepository
from components.monitoring import LogGroup
from utils.tagging import create_default_tags


class TradeRampStack:
    """Main infrastructure stack for TradeRamp."""
    
    def __init__(self, config: InfrastructureConfig):
        """Initialize TradeRamp stack."""
        self.config = config
        self.tags = create_default_tags(config.project_name, config.environment)
        
        # Create components
        self.vpc = self._create_vpc()
        self.security_groups = self._create_security_groups()
        self.ecr = self._create_ecr()
        self.log_group = self._create_log_group()
        self.ecs_cluster = self._create_ecs_cluster()
        self.load_balancer = self._create_load_balancer()
        self.ecs_service = self._create_ecs_service()
        
        # Export outputs
        self._export_outputs()
    
    def _create_vpc(self) -> VPCComponent:
        """Create VPC with public subnets."""
        return VPCComponent(
            f"{self.config.project_name}-{self.config.environment}",
            VPCConfig(
                name=f"{self.config.project_name}-{self.config.environment}",
                tags=self.tags
            )
        )
    
    def _create_security_groups(self) -> Dict[str, Any]:
        """Create security groups."""
        alb_sg = create_alb_security_group(
            f"{self.config.project_name}-{self.config.environment}",
            self.vpc.vpc.id,
            self.tags
        )
        
        # Create ECS security group with proper restrictions
        ecs_sg = SecurityGroupComponent(
            f"{self.config.project_name}-{self.config.environment}-ecs-sg",
            SecurityGroupConfig(
                name=f"{self.config.project_name}-{self.config.environment}-ecs-sg",
                vpc_id=self.vpc.vpc.id,
                description="Security group for ECS tasks",
                ingress_rules=[
                    SecurityRule(
                        protocol="tcp",
                        from_port=80,
                        to_port=80,
                        security_groups=[alb_sg.security_group.id],
                        description="Allow HTTP from ALB only"
                    )
                ],
                egress_rules=[
                    SecurityRule(
                        protocol="tcp",
                        from_port=443,
                        to_port=443,
                        cidr_blocks=[NetworkCIDR.INTERNET.value],
                        description="Allow HTTPS for external APIs"
                    ),
                    SecurityRule(
                        protocol="tcp",
                        from_port=443,
                        to_port=443,
                        cidr_blocks=["52.94.0.0/20"],  # ECR endpoints
                        description="Allow ECR access"
                    )
                ],
                tags=self.tags
            )
        )
        
        return {
            "alb": alb_sg,
            "ecs": ecs_sg
        }
    
    def _export_outputs(self) -> None:
        """Export stack outputs."""
        pulumi.export("vpc_id", self.vpc.vpc.id)
        pulumi.export("ecr_repository_url", self.ecr.repository_url)
        pulumi.export("ecs_cluster_name", self.ecs_cluster.cluster.name)
        pulumi.export("alb_dns_name", self.load_balancer.dns_name)
        
        if self.config.domain_name:
            pulumi.export("website_url", f"https://{self.config.domain_name}")
        else:
            pulumi.export("website_url", Output.concat("http://", self.load_balancer.dns_name))
```

### Phase 4: Update Main Entry Point (Priority: High)

Update `__main__.py`:

```python
"""TradeRamp infrastructure entry point."""

import sys
from typing import NoReturn

import pulumi

from config.settings import InfrastructureConfig
from stacks.traderamp_stack import TradeRampStack


def main() -> None:
    """Main entry point for Pulumi program."""
    try:
        # Load and validate configuration
        config = InfrastructureConfig.from_pulumi_config()
        config.validate()
        
        # Create infrastructure stack
        stack = TradeRampStack(config)
        
        pulumi.log.info(f"Successfully created TradeRamp infrastructure for {config.environment}")
        
    except ValueError as e:
        pulumi.log.error(f"Configuration error: {e}")
        sys.exit(1)
    except Exception as e:
        pulumi.log.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
```

### Phase 5: Add Testing (Priority: Medium)

Create `tests/test_networking.py`:

```python
"""Tests for networking components."""

import unittest
from unittest.mock import Mock, patch
import pulumi

from components.networking import VPCComponent, VPCConfig
from config.constants import NetworkCIDR


class TestVPCComponent(unittest.TestCase):
    """Test VPC component."""
    
    @pulumi.runtime.test
    def test_vpc_creation(self):
        """Test VPC resource creation."""
        config = VPCConfig(
            name="test-vpc",
            tags={"Environment": "test"}
        )
        
        vpc = VPCComponent("test", config)
        
        def check_vpc(args):
            vpc_id, subnet_ids = args
            assert vpc_id is not None
            assert len(subnet_ids) == 2
        
        return pulumi.Output.all(vpc.vpc.id, vpc.public_subnet_ids).apply(check_vpc)
    
    def test_vpc_config_validation(self):
        """Test VPC configuration validation."""
        config = VPCConfig(
            name="test-vpc",
            cidr_block="invalid-cidr"
        )
        
        with self.assertRaises(ValueError):
            config.validate()
```

### Phase 6: Add Utilities (Priority: Low)

Create `utils/tagging.py`:

```python
"""Tag management utilities."""

from typing import Dict, Optional
from datetime import datetime


def create_default_tags(
    project_name: str,
    environment: str,
    owner: Optional[str] = None
) -> Dict[str, str]:
    """Create default tags for all resources."""
    tags = {
        "Project": project_name,
        "Environment": environment,
        "ManagedBy": "Pulumi",
        "CreatedAt": datetime.utcnow().isoformat(),
    }
    
    if owner:
        tags["Owner"] = owner
    
    return tags


def merge_tags(
    default_tags: Dict[str, str],
    custom_tags: Optional[Dict[str, str]] = None
) -> Dict[str, str]:
    """Merge custom tags with defaults."""
    if custom_tags:
        return {**default_tags, **custom_tags}
    return default_tags
```

## Implementation Plan

### Week 1: Foundation
1. Set up new directory structure
2. Extract configuration and constants
3. Create base component classes
4. Set up testing framework

### Week 2: Core Components
1. Implement networking components
2. Implement compute components
3. Implement storage components
4. Add monitoring components

### Week 3: Integration
1. Create stack composition
2. Update main entry point
3. Migrate existing resources
4. Test end-to-end deployment

### Week 4: Polish
1. Add comprehensive tests
2. Add documentation
3. Security hardening
4. Performance optimization

## Benefits

1. **Maintainability**: 80% easier to modify and extend
2. **Testability**: Components can be unit tested
3. **Reusability**: Components can be used in other projects
4. **Security**: Better security group management
5. **Type Safety**: Full type hints throughout
6. **Documentation**: Self-documenting code structure

## Migration Strategy

1. Create new structure alongside existing
2. Test components individually
3. Deploy to staging environment
4. Validate all resources created correctly
5. Switch production to new code
6. Remove old monolithic file

## Conclusion

This refactoring will transform the current monolithic infrastructure code into a well-architected, maintainable, and secure solution following clean code principles and Python best practices.