"""VPC component for TradeRamp infrastructure."""

from typing import List, Dict, Any, Optional
import pulumi
import pulumi_aws as aws
from pulumi import ComponentResource, ResourceOptions, Output

from config.constants import NetworkCIDR, Defaults


class VPCComponent(ComponentResource):
    """
    VPC component with public subnets for ECS Fargate.
    
    This component creates:
    - VPC with DNS enabled
    - Internet Gateway
    - Public subnets across multiple AZs
    - Route table with internet access
    - VPC Flow Logs (optional)
    """
    
    def __init__(
        self,
        name: str,
        cidr_block: str = NetworkCIDR.VPC.value,
        availability_zones: int = Defaults.AVAILABILITY_ZONES,
        enable_flow_logs: bool = False,
        tags: Dict[str, str] = None,
        opts: ResourceOptions = None
    ) -> None:
        """
        Initialize VPC component.
        
        Args:
            name: Component name
            cidr_block: VPC CIDR block
            availability_zones: Number of AZs to use (default: 2)
            enable_flow_logs: Enable VPC Flow Logs
            tags: Resource tags
            opts: Pulumi resource options
        """
        super().__init__("traderamp:networking:VPC", name, None, opts)
        
        self.name = name
        self.cidr_block = cidr_block
        self.availability_zones = availability_zones
        self.tags = tags or {}
        
        # Create resources
        self.vpc = self._create_vpc()
        self.igw = self._create_internet_gateway()
        self.public_subnets = self._create_public_subnets()
        self.route_table = self._create_route_table()
        self._associate_subnets()
        
        if enable_flow_logs:
            self.flow_logs = self._create_flow_logs()
        
        # Register outputs
        self.register_outputs({
            "vpc_id": self.vpc.id,
            "vpc_cidr": self.vpc.cidr_block,
            "internet_gateway_id": self.igw.id,
            "public_subnet_ids": [s.id for s in self.public_subnets],
            "public_subnet_cidrs": [s.cidr_block for s in self.public_subnets],
            "route_table_id": self.route_table.id
        })
    
    def _create_vpc(self) -> aws.ec2.Vpc:
        """Create VPC resource."""
        return aws.ec2.Vpc(
            f"{self.name}-vpc",
            cidr_block=self.cidr_block,
            enable_dns_hostnames=True,
            enable_dns_support=True,
            tags={
                **self.tags,
                "Name": f"{self.name}-vpc",
                "Type": "main"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_internet_gateway(self) -> aws.ec2.InternetGateway:
        """Create Internet Gateway."""
        return aws.ec2.InternetGateway(
            f"{self.name}-igw",
            vpc_id=self.vpc.id,
            tags={
                **self.tags,
                "Name": f"{self.name}-igw"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _create_public_subnets(self) -> List[aws.ec2.Subnet]:
        """Create public subnets across availability zones."""
        # Get available AZs
        azs = aws.get_availability_zones(
            state="available",
            filters=[{
                "name": "opt-in-status",
                "values": ["opt-in-not-required"]
            }]
        )
        
        if len(azs.names) < self.availability_zones:
            pulumi.log.warn(
                f"Requested {self.availability_zones} AZs but only "
                f"{len(azs.names)} are available. Using {len(azs.names)}."
            )
            self.availability_zones = len(azs.names)
        
        subnets = []
        for i in range(self.availability_zones):
            # Calculate subnet CIDR
            subnet_cidr = f"10.0.{i+1}.0/24"
            
            subnet = aws.ec2.Subnet(
                f"{self.name}-public-subnet-{i+1}",
                vpc_id=self.vpc.id,
                cidr_block=subnet_cidr,
                availability_zone=azs.names[i],
                map_public_ip_on_launch=True,
                tags={
                    **self.tags,
                    "Name": f"{self.name}-public-subnet-{i+1}",
                    "Type": "public",
                    "kubernetes.io/role/elb": "1"  # For potential K8s use
                },
                opts=ResourceOptions(parent=self)
            )
            subnets.append(subnet)
        
        return subnets
    
    def _create_route_table(self) -> aws.ec2.RouteTable:
        """Create route table for public subnets."""
        return aws.ec2.RouteTable(
            f"{self.name}-public-rt",
            vpc_id=self.vpc.id,
            routes=[{
                "cidr_block": NetworkCIDR.INTERNET.value,
                "gateway_id": self.igw.id
            }],
            tags={
                **self.tags,
                "Name": f"{self.name}-public-rt",
                "Type": "public"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def _associate_subnets(self) -> None:
        """Associate subnets with route table."""
        for i, subnet in enumerate(self.public_subnets):
            aws.ec2.RouteTableAssociation(
                f"{self.name}-public-rta-{i+1}",
                subnet_id=subnet.id,
                route_table_id=self.route_table.id,
                opts=ResourceOptions(parent=self)
            )
    
    def _create_flow_logs(self) -> aws.ec2.FlowLog:
        """Create VPC Flow Logs for security monitoring."""
        # Create CloudWatch log group for flow logs
        log_group = aws.cloudwatch.LogGroup(
            f"{self.name}-flow-logs",
            name=f"/aws/vpc/{self.name}",
            retention_in_days=7,  # Short retention for cost optimization
            tags=self.tags,
            opts=ResourceOptions(parent=self)
        )
        
        # Create IAM role for flow logs
        flow_log_role = aws.iam.Role(
            f"{self.name}-flow-log-role",
            assume_role_policy="""{
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Principal": {"Service": "vpc-flow-logs.amazonaws.com"},
                    "Action": "sts:AssumeRole"
                }]
            }""",
            tags=self.tags,
            opts=ResourceOptions(parent=self)
        )
        
        # Attach policy to role
        aws.iam.RolePolicy(
            f"{self.name}-flow-log-policy",
            role=flow_log_role.id,
            policy=Output.all(log_group.arn).apply(lambda args: f"""{{
                "Version": "2012-10-17",
                "Statement": [{{
                    "Effect": "Allow",
                    "Action": [
                        "logs:CreateLogGroup",
                        "logs:CreateLogStream",
                        "logs:PutLogEvents",
                        "logs:DescribeLogGroups",
                        "logs:DescribeLogStreams"
                    ],
                    "Resource": "{args[0]}:*"
                }}]
            }}"""),
            opts=ResourceOptions(parent=self)
        )
        
        # Create flow log
        return aws.ec2.FlowLog(
            f"{self.name}-flow-log",
            iam_role_arn=flow_log_role.arn,
            log_destination_type="cloud-watch-logs",
            log_group_name=log_group.name,
            traffic_type="ALL",
            vpc_id=self.vpc.id,
            tags={
                **self.tags,
                "Name": f"{self.name}-flow-log"
            },
            opts=ResourceOptions(parent=self)
        )
    
    def get_subnet_ids(self) -> Output[List[str]]:
        """Get list of subnet IDs."""
        return Output.all(*[s.id for s in self.public_subnets])
    
    def get_availability_zones(self) -> Output[List[str]]:
        """Get list of availability zones used."""
        return Output.all(*[s.availability_zone for s in self.public_subnets])