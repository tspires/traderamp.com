"""
AWS implementation of networking components.

Follows Interface Segregation and Dependency Inversion principles.
"""

from typing import List, Dict, Optional, Any
import pulumi
import pulumi_aws as aws
from pulumi import ResourceOptions, Output

from core.base_component import BaseInfrastructureComponent
from core.interfaces import INetworkProvider, HealthCheckSpec
from core.validators import RangeValidator, ListLengthValidator, ValidationContext


class AWSNetworkProvider(INetworkProvider):
    """AWS implementation of network provider."""
    
    def create_vpc(self, cidr_block: str) -> aws.ec2.Vpc:
        """Create an AWS VPC."""
        return aws.ec2.Vpc(
            "vpc",
            cidr_block=cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True
        )
    
    def create_subnets(self, vpc_id: str, count: int) -> List[aws.ec2.Subnet]:
        """Create subnets in the VPC."""
        # Implementation details...
        pass
    
    def create_security_group(self, name: str, vpc_id: str, rules: List[Any]) -> aws.ec2.SecurityGroup:
        """Create a security group."""
        # Implementation details...
        pass


class VPCComponent(BaseInfrastructureComponent):
    """
    VPC component with clean separation of concerns.
    
    Only responsible for VPC and directly related resources.
    """
    
    def __init__(
        self,
        name: str,
        cidr_block: str = "10.0.0.0/16",
        availability_zone_count: int = 2,
        enable_flow_logs: bool = False,
        **kwargs
    ):
        """Initialize VPC component."""
        self.cidr_block = cidr_block
        self.availability_zone_count = availability_zone_count
        self.enable_flow_logs = enable_flow_logs
        
        super().__init__(
            "traderamp:aws:networking:VPC",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate VPC configuration."""
        context = ValidationContext()
        
        context.add_validation(
            "availability_zone_count",
            RangeValidator(1, 6, "AZ count"),
            self.availability_zone_count
        )
        
        context.validate_all()
    
    def create_resources(self) -> None:
        """Create VPC resources."""
        # Create VPC
        vpc = aws.ec2.Vpc(
            f"{self.name}-vpc",
            cidr_block=self.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags=self.get_tags("VPC", f"{self.name}-vpc"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("vpc", vpc)
        
        # Create Internet Gateway
        igw = aws.ec2.InternetGateway(
            f"{self.name}-igw",
            vpc_id=vpc.id,
            tags=self.get_tags("InternetGateway", f"{self.name}-igw"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("igw", igw)
        
        # Create subnets
        self._create_subnets(vpc)
        
        # Create route table
        self._create_route_table(vpc, igw)
        
        # Optionally create flow logs
        if self.enable_flow_logs:
            self._create_flow_logs(vpc)
    
    def _create_subnets(self, vpc: aws.ec2.Vpc) -> None:
        """Create public subnets."""
        azs = aws.get_availability_zones(state="available")
        
        subnets = []
        for i in range(min(self.availability_zone_count, len(azs.names))):
            subnet = aws.ec2.Subnet(
                f"{self.name}-subnet-{i+1}",
                vpc_id=vpc.id,
                cidr_block=f"10.0.{i+1}.0/24",
                availability_zone=azs.names[i],
                map_public_ip_on_launch=True,
                tags=self.get_tags("Subnet", f"{self.name}-subnet-{i+1}"),
                opts=ResourceOptions(parent=self)
            )
            subnets.append(subnet)
            self.add_resource(f"subnet-{i+1}", subnet)
        
        self.add_resource("subnets", subnets)
    
    def _create_route_table(self, vpc: aws.ec2.Vpc, igw: aws.ec2.InternetGateway) -> None:
        """Create and associate route table."""
        route_table = aws.ec2.RouteTable(
            f"{self.name}-rt",
            vpc_id=vpc.id,
            routes=[{
                "cidr_block": "0.0.0.0/0",
                "gateway_id": igw.id
            }],
            tags=self.get_tags("RouteTable", f"{self.name}-rt"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("route_table", route_table)
        
        # Associate with subnets
        subnets = self.get_resource("subnets")
        for i, subnet in enumerate(subnets):
            aws.ec2.RouteTableAssociation(
                f"{self.name}-rta-{i+1}",
                subnet_id=subnet.id,
                route_table_id=route_table.id,
                opts=ResourceOptions(parent=self)
            )
    
    def _create_flow_logs(self, vpc: aws.ec2.Vpc) -> None:
        """Create VPC flow logs."""
        # Create log group
        log_group = aws.cloudwatch.LogGroup(
            f"{self.name}-flow-logs",
            name=f"/aws/vpc/{self.name}",
            retention_in_days=7,
            tags=self.get_tags("LogGroup", f"{self.name}-flow-logs"),
            opts=ResourceOptions(parent=self)
        )
        
        # Create IAM role for flow logs
        flow_log_role = self._create_flow_log_role()
        
        # Create flow log
        flow_log = aws.ec2.FlowLog(
            f"{self.name}-flow-log",
            iam_role_arn=flow_log_role.arn,
            log_destination_type="cloud-watch-logs",
            log_group_name=log_group.name,
            traffic_type="ALL",
            vpc_id=vpc.id,
            tags=self.get_tags("FlowLog", f"{self.name}-flow-log"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("flow_log", flow_log)
    
    def _create_flow_log_role(self) -> aws.iam.Role:
        """Create IAM role for flow logs."""
        role = aws.iam.Role(
            f"{self.name}-flow-log-role",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }""",
            tags=self.get_tags("IAMRole", f"{self.name}-flow-log-role"),
            opts=ResourceOptions(parent=self)
        )
        
        # Attach policy
        aws.iam.RolePolicy(
            f"{self.name}-flow-log-policy",
            role=role.id,
            policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": "*"
                }]
            }""",
            opts=ResourceOptions(parent=self)
        )
        
        return role
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        vpc = self.get_resource("vpc")
        subnets = self.get_resource("subnets")
        
        return {
            "vpc_id": vpc.id,
            "vpc_cidr": vpc.cidr_block,
            "subnet_ids": [s.id for s in subnets],
            "subnet_count": len(subnets)
        }


class LoadBalancerComponent(BaseInfrastructureComponent):
    """
    Load balancer component - single responsibility.
    
    Only manages the load balancer and target group.
    Certificate management is delegated to a separate component.
    """
    
    def __init__(
        self,
        name: str,
        vpc_id: Output[str],
        subnet_ids: List[Output[str]],
        security_group_ids: List[Output[str]],
        health_check: HealthCheckSpec,
        enable_deletion_protection: bool = False,
        **kwargs
    ):
        """Initialize load balancer component."""
        self.vpc_id = vpc_id
        self.subnet_ids = subnet_ids
        self.security_group_ids = security_group_ids
        self.health_check = health_check
        self.enable_deletion_protection = enable_deletion_protection
        
        super().__init__(
            "traderamp:aws:networking:LoadBalancer",
            name,
            **kwargs
        )
    
    def validate(self) -> None:
        """Validate load balancer configuration."""
        context = ValidationContext()
        
        context.add_validation(
            "subnet_count",
            ListLengthValidator(2, None, "Subnets"),
            self.subnet_ids
        )
        
        # Validate health check
        self.health_check.validate()
        
        context.validate_all()
    
    def create_resources(self) -> None:
        """Create load balancer resources."""
        # Create ALB
        alb = aws.lb.LoadBalancer(
            f"{self.name}-alb",
            load_balancer_type="application",
            subnets=self.subnet_ids,
            security_groups=self.security_group_ids,
            enable_deletion_protection=self.enable_deletion_protection,
            enable_http2=True,
            idle_timeout=60,
            tags=self.get_tags("ALB", f"{self.name}-alb"),
            opts=ResourceOptions(parent=self)
        )
        self.add_resource("alb", alb)
        
        # Create target group
        target_group = self._create_target_group()
        self.add_resource("target_group", target_group)
        
        # Create HTTP listener (redirect to HTTPS)
        http_listener = self._create_http_listener(alb)
        self.add_resource("http_listener", http_listener)
    
    def _create_target_group(self) -> aws.lb.TargetGroup:
        """Create target group with health checks."""
        return aws.lb.TargetGroup(
            f"{self.name}-tg",
            port=80,
            protocol="HTTP",
            vpc_id=self.vpc_id,
            target_type="ip",  # For Fargate
            deregistration_delay=30,
            health_check={
                "enabled": True,
                "path": self.health_check.path,
                "protocol": "HTTP",
                "port": "traffic-port",
                "interval": self.health_check.interval_seconds,
                "timeout": self.health_check.timeout_seconds,
                "healthy_threshold": self.health_check.healthy_threshold,
                "unhealthy_threshold": self.health_check.unhealthy_threshold,
                "matcher": "200-299"
            },
            tags=self.get_tags("TargetGroup", f"{self.name}-tg"),
            opts=ResourceOptions(parent=self)
        )
    
    def _create_http_listener(self, alb: aws.lb.LoadBalancer) -> aws.lb.Listener:
        """Create HTTP listener."""
        target_group = self.get_resource("target_group")
        return aws.lb.Listener(
            f"{self.name}-http",
            load_balancer_arn=alb.arn,
            port=80,
            protocol="HTTP",
            default_actions=[{
                "type": "forward",
                "target_group_arn": target_group.arn
            }],
            opts=ResourceOptions(parent=self)
        )
    
    def create_https_listener(
        self,
        certificate_arn: Output[str],
        ssl_policy: str = "ELBSecurityPolicy-TLS13-1-2-2021-06"
    ) -> aws.lb.Listener:
        """
        Create HTTPS listener.
        
        Separated from main creation to allow certificate to be provided externally.
        """
        alb = self.get_resource("alb")
        target_group = self.get_resource("target_group")
        
        https_listener = aws.lb.Listener(
            f"{self.name}-https",
            load_balancer_arn=alb.arn,
            port=443,
            protocol="HTTPS",
            ssl_policy=ssl_policy,
            certificate_arn=certificate_arn,
            default_actions=[{
                "type": "forward",
                "target_group_arn": target_group.arn
            }],
            opts=ResourceOptions(parent=self)
        )
        
        self.add_resource("https_listener", https_listener)
        return https_listener
    
    def get_outputs(self) -> Dict[str, Any]:
        """Get component outputs."""
        alb = self.get_resource("alb")
        target_group = self.get_resource("target_group")
        
        return {
            "alb_arn": alb.arn,
            "alb_dns_name": alb.dns_name,
            "alb_zone_id": alb.zone_id,
            "target_group_arn": target_group.arn
        }
    
    @property
    def target_group_arn(self) -> Output[str]:
        """Get target group ARN for external use."""
        target_group = self.get_resource("target_group")
        return target_group.arn if target_group else None